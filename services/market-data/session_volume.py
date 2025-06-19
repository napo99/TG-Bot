"""
Session Volume Analysis Engine for Crypto Trading Assistant
Implements LuxAlgo 4-Session Framework with DST handling and volume tracking
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import statistics
from loguru import logger
import pytz

@dataclass
class SessionVolumeData:
    """Data structure for session volume tracking"""
    session_name: str
    start_time: str  # HH:MM UTC format
    end_time: str    # HH:MM UTC format
    duration_hours: int
    current_volume: float
    session_progress: float  # 0.0 to 1.0
    current_hour: int        # Which hour within session (1-9 for NY)
    total_hours: int         # Total hours in session
    timestamp: datetime

@dataclass 
class SessionBaseline:
    """7-day historical baseline for session volume"""
    session_name: str
    avg_total_volume: float      # Average total volume for this session over 7 days
    avg_hourly_rate: float       # Average volume per hour in this session
    typical_daily_pct: float     # Typical % this session contributes to daily volume
    volume_history: List[float]  # Last 7 days of session volumes
    updated_at: datetime

@dataclass
class DailyVolumeContext:
    """Daily volume context and progress tracking"""
    current_daily_volume: float
    daily_avg_7day: float
    daily_progress_pct: float    # How much of typical daily volume we've seen
    sessions_completed: int      # How many sessions completed today
    estimated_daily_total: float # Projected daily total based on current progress
    timestamp: datetime

@dataclass
class SessionAnalysis:
    """Complete session volume analysis result"""
    current_session: SessionVolumeData
    session_baseline: SessionBaseline
    daily_context: DailyVolumeContext
    session_rel_volume: float    # Current session volume vs baseline
    session_hourly_rate: float   # Current hourly rate in session
    session_hourly_rel: float    # Current hourly rate vs baseline
    session_share_current: float # % of current daily volume
    session_share_typical: float # Typical % share
    is_dst_active: bool
    dst_adjustment: str

class SessionVolumeEngine:
    """LuxAlgo 4-Session Volume Analysis Engine"""
    
    # LuxAlgo Session Framework (GMT-0 base)
    SESSIONS = {
        'new_york': {'start': '12:00', 'end': '21:00', 'hours': 9},
        'london': {'start': '06:00', 'end': '12:00', 'hours': 6}, 
        'close': {'start': '21:00', 'end': '01:00', 'hours': 4},
        'asia': {'start': '01:00', 'end': '06:00', 'hours': 5}
    }
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.session_baselines = {}  # Store historical baselines
        self.daily_volume_cache = {}  # Cache for daily volume calculations
        
    def _is_dst_active(self, dt: datetime = None) -> Tuple[bool, str]:
        """
        Check if European DST is currently active
        European DST: Last Sunday in March to Last Sunday in October
        """
        if dt is None:
            dt = datetime.utcnow()
            
        year = dt.year
        
        # Calculate last Sunday in March
        march_last_sunday = datetime(year, 3, 31)
        while march_last_sunday.weekday() != 6:  # 6 = Sunday
            march_last_sunday -= timedelta(days=1)
            
        # Calculate last Sunday in October  
        oct_last_sunday = datetime(year, 10, 31)
        while oct_last_sunday.weekday() != 6:
            oct_last_sunday -= timedelta(days=1)
            
        is_dst = march_last_sunday <= dt.replace(hour=0, minute=0, second=0, microsecond=0) < oct_last_sunday
        
        adjustment = "+1 hour (DST active)" if is_dst else "Standard time (no DST)"
        return is_dst, adjustment
    
    def _get_session_boundaries(self, is_dst: bool = False) -> Dict[str, Dict[str, str]]:
        """Get session boundaries adjusted for DST"""
        sessions = self.SESSIONS.copy()
        
        if is_dst:
            # Shift all sessions +1 hour for European DST
            dst_sessions = {}
            for name, config in sessions.items():
                start_hour = int(config['start'].split(':')[0])
                end_hour = int(config['end'].split(':')[0])
                
                # Handle 24-hour wraparound
                start_hour = (start_hour + 1) % 24
                end_hour = (end_hour + 1) % 24
                
                dst_sessions[name] = {
                    'start': f"{start_hour:02d}:00",
                    'end': f"{end_hour:02d}:00", 
                    'hours': config['hours']
                }
            return dst_sessions
        
        return sessions
    
    def _get_current_session(self, dt: datetime = None) -> Tuple[str, SessionVolumeData]:
        """Identify current trading session and calculate progress"""
        if dt is None:
            dt = datetime.utcnow()
            
        is_dst, dst_adj = self._is_dst_active(dt)
        sessions = self._get_session_boundaries(is_dst)
        
        current_hour = dt.hour
        current_minute = dt.minute
        current_time_decimal = current_hour + (current_minute / 60.0)
        
        for session_name, config in sessions.items():
            start_hour = int(config['start'].split(':')[0])
            end_hour = int(config['end'].split(':')[0])
            
            # Handle sessions that cross midnight (like 'close': 21:00-01:00)
            if start_hour > end_hour:  # Crosses midnight
                if current_hour >= start_hour or current_hour < end_hour:
                    # Calculate session progress
                    if current_hour >= start_hour:
                        hours_elapsed = current_time_decimal - start_hour
                    else:  # After midnight
                        hours_elapsed = (24 - start_hour) + current_time_decimal
                    
                    session_progress = min(hours_elapsed / config['hours'], 1.0)
                    current_session_hour = int(hours_elapsed) + 1
                    
                    return session_name, SessionVolumeData(
                        session_name=session_name,
                        start_time=config['start'],
                        end_time=config['end'], 
                        duration_hours=config['hours'],
                        current_volume=0.0,  # To be filled by caller
                        session_progress=session_progress,
                        current_hour=current_session_hour,
                        total_hours=config['hours'],
                        timestamp=dt
                    )
            else:  # Normal session (doesn't cross midnight)
                if start_hour <= current_hour < end_hour:
                    hours_elapsed = current_time_decimal - start_hour
                    session_progress = min(hours_elapsed / config['hours'], 1.0)
                    current_session_hour = int(hours_elapsed) + 1
                    
                    return session_name, SessionVolumeData(
                        session_name=session_name,
                        start_time=config['start'],
                        end_time=config['end'],
                        duration_hours=config['hours'], 
                        current_volume=0.0,  # To be filled by caller
                        session_progress=session_progress,
                        current_hour=current_session_hour,
                        total_hours=config['hours'],
                        timestamp=dt
                    )
        
        # Fallback - shouldn't happen if sessions cover 24 hours
        return 'unknown', SessionVolumeData(
            session_name='unknown', start_time='00:00', end_time='24:00',
            duration_hours=24, current_volume=0.0, session_progress=0.0,
            current_hour=1, total_hours=24, timestamp=dt
        )
    
    async def _calculate_session_volume(self, symbol: str, session_name: str, 
                                      timeframe: str = '15m', exchange: str = 'binance') -> float:
        """Calculate current session volume by summing candles within session timeframe"""
        try:
            current_time = datetime.utcnow()
            is_dst, _ = self._is_dst_active(current_time)
            sessions = self._get_session_boundaries(is_dst)
            
            if session_name not in sessions:
                return 0.0
                
            session_config = sessions[session_name]
            
            # Calculate session start time
            start_hour = int(session_config['start'].split(':')[0])
            
            # For sessions that cross midnight, handle carefully
            if session_name == 'close' or session_name == 'asia':
                if current_time.hour < 12:  # We're in the "next day" part of the session
                    session_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    if session_name == 'close':
                        session_start -= timedelta(days=1)  # Go back to previous day 21:00
                else:
                    session_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            else:
                session_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            
            # Calculate how many 15m candles we need
            time_elapsed = current_time - session_start
            candles_needed = max(int(time_elapsed.total_seconds() / 900), 1)  # 900s = 15m
            
            # Fetch OHLCV data
            if exchange not in self.exchange_manager.exchanges:
                logger.warning(f"Exchange {exchange} not available")
                return 0.0
                
            ex = self.exchange_manager.exchanges[exchange]
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=candles_needed + 5)
            
            if not ohlcv:
                return 0.0
            
            # Sum volumes for candles within current session
            session_volume = 0.0
            session_start_timestamp = int(session_start.timestamp() * 1000)
            
            for candle in ohlcv:
                candle_time = candle[0]  # timestamp
                volume = candle[5]       # volume
                
                if candle_time >= session_start_timestamp:
                    session_volume += volume
                    
            return round(session_volume, 2)
            
        except Exception as e:
            logger.error(f"Error calculating session volume: {e}")
            return 0.0
    
    async def _get_session_baseline(self, symbol: str, session_name: str, 
                                  timeframe: str = '15m', exchange: str = 'binance') -> SessionBaseline:
        """Calculate 7-day baseline for session volume"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{session_name}_{timeframe}_{exchange}"
            if cache_key in self.session_baselines:
                baseline = self.session_baselines[cache_key]
                # Check if baseline is recent (within 4 hours)
                if (datetime.utcnow() - baseline.updated_at).total_seconds() < 14400:
                    return baseline
            
            # Calculate new baseline
            current_time = datetime.utcnow()
            session_volumes = []
            
            # Collect volume data for last 7 days for this session
            for days_back in range(1, 8):  # 1-7 days ago
                target_date = current_time - timedelta(days=days_back)
                
                # Calculate session volume for that day
                is_dst, _ = self._is_dst_active(target_date)
                sessions = self._get_session_boundaries(is_dst)
                
                if session_name not in sessions:
                    continue
                    
                session_config = sessions[session_name]
                start_hour = int(session_config['start'].split(':')[0])
                
                # Set session start for that historical day
                session_start = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                session_end = session_start + timedelta(hours=session_config['hours'])
                
                # Fetch historical data
                session_start_timestamp = int(session_start.timestamp() * 1000)
                session_end_timestamp = int(session_end.timestamp() * 1000)
                
                # Get enough candles to cover the session
                candles_needed = session_config['hours'] * 4 + 10  # 4 candles per hour + buffer
                
                try:
                    ex = self.exchange_manager.exchanges[exchange]
                    since_timestamp = session_start_timestamp - (candles_needed * 900000)  # Go back further
                    ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=candles_needed, since=since_timestamp)
                    
                    if ohlcv:
                        day_session_volume = 0.0
                        for candle in ohlcv:
                            candle_time = candle[0]
                            volume = candle[5]
                            
                            if session_start_timestamp <= candle_time < session_end_timestamp:
                                day_session_volume += volume
                        
                        if day_session_volume > 0:
                            session_volumes.append(day_session_volume)
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch historical data for {target_date}: {e}")
                    continue
            
            # Calculate baseline statistics
            if len(session_volumes) >= 3:  # Need at least 3 days of data
                # Remove outliers (top/bottom 10% if we have enough data)
                if len(session_volumes) >= 5:
                    sorted_volumes = sorted(session_volumes)
                    trim_count = max(1, len(sorted_volumes) // 10)
                    trimmed_volumes = sorted_volumes[trim_count:-trim_count]
                else:
                    trimmed_volumes = session_volumes
                
                avg_total_volume = statistics.median(trimmed_volumes)
                avg_hourly_rate = avg_total_volume / sessions[session_name]['hours']
                
                # Estimate typical daily percentage (placeholder - would need daily volume data)
                typical_daily_pct = 0.25 if session_name == 'new_york' else 0.20  # Rough estimates
                
                baseline = SessionBaseline(
                    session_name=session_name,
                    avg_total_volume=round(avg_total_volume, 2),
                    avg_hourly_rate=round(avg_hourly_rate, 2),
                    typical_daily_pct=typical_daily_pct,
                    volume_history=session_volumes[-7:],  # Keep last 7 entries
                    updated_at=datetime.utcnow()
                )
                
                # Cache the baseline
                self.session_baselines[cache_key] = baseline
                return baseline
            else:
                # Not enough data - return default baseline
                default_volume = 1000.0  # Default fallback
                return SessionBaseline(
                    session_name=session_name,
                    avg_total_volume=default_volume,
                    avg_hourly_rate=default_volume / sessions[session_name]['hours'],
                    typical_daily_pct=0.25,
                    volume_history=[default_volume],
                    updated_at=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error calculating session baseline: {e}")
            # Return safe default
            return SessionBaseline(
                session_name=session_name,
                avg_total_volume=1000.0,
                avg_hourly_rate=200.0,
                typical_daily_pct=0.25,
                volume_history=[1000.0],
                updated_at=datetime.utcnow()
            )
    
    async def _get_daily_volume_context(self, symbol: str, timeframe: str = '15m', 
                                      exchange: str = 'binance') -> DailyVolumeContext:
        """Calculate daily volume context and progress"""
        try:
            current_time = datetime.utcnow()
            
            # Get today's volume so far
            day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            candles_since_start = int((current_time - day_start).total_seconds() / 900)  # 15m candles
            
            ex = self.exchange_manager.exchanges[exchange]
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=candles_since_start + 10)
            
            current_daily_volume = 0.0
            day_start_timestamp = int(day_start.timestamp() * 1000)
            
            if ohlcv:
                for candle in ohlcv:
                    if candle[0] >= day_start_timestamp:
                        current_daily_volume += candle[5]
            
            # Calculate 7-day daily average
            daily_volumes = []
            for days_back in range(1, 8):
                target_date = current_time - timedelta(days=days_back)
                day_start_hist = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end_hist = day_start_hist + timedelta(days=1)
                
                try:
                    # Get full day data (96 candles for 24 hours of 15m data)
                    since_timestamp = int(day_start_hist.timestamp() * 1000)
                    hist_ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=100, since=since_timestamp)
                    
                    day_volume = 0.0
                    day_end_timestamp = int(day_end_hist.timestamp() * 1000)
                    
                    if hist_ohlcv:
                        for candle in hist_ohlcv:
                            if since_timestamp <= candle[0] < day_end_timestamp:
                                day_volume += candle[5]
                    
                    if day_volume > 0:
                        daily_volumes.append(day_volume)
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch daily historical data: {e}")
                    continue
            
            # Calculate averages
            if daily_volumes:
                daily_avg_7day = statistics.median(daily_volumes)
            else:
                daily_avg_7day = current_daily_volume * 2  # Fallback estimation
            
            # Calculate progress
            hours_elapsed = (current_time - day_start).total_seconds() / 3600
            expected_progress = hours_elapsed / 24.0
            actual_progress = current_daily_volume / daily_avg_7day if daily_avg_7day > 0 else 0
            
            daily_progress_pct = (actual_progress / expected_progress * 100) if expected_progress > 0 else 0
            
            # Count completed sessions
            sessions_completed = 0
            is_dst, _ = self._is_dst_active(current_time)
            sessions = self._get_session_boundaries(is_dst)
            
            for session_name, config in sessions.items():
                session_end_hour = int(config['end'].split(':')[0])
                if session_name in ['close', 'asia'] and session_end_hour < 12:
                    # Handle midnight crossover sessions
                    if current_time.hour >= 12 or current_time.hour >= session_end_hour:
                        sessions_completed += 1
                else:
                    if current_time.hour >= session_end_hour:
                        sessions_completed += 1
            
            # Estimate daily total
            if expected_progress > 0:
                estimated_daily_total = current_daily_volume / expected_progress
            else:
                estimated_daily_total = daily_avg_7day
            
            return DailyVolumeContext(
                current_daily_volume=round(current_daily_volume, 2),
                daily_avg_7day=round(daily_avg_7day, 2),
                daily_progress_pct=round(daily_progress_pct, 1),
                sessions_completed=sessions_completed,
                estimated_daily_total=round(estimated_daily_total, 2),
                timestamp=current_time
            )
            
        except Exception as e:
            logger.error(f"Error calculating daily volume context: {e}")
            return DailyVolumeContext(
                current_daily_volume=0.0,
                daily_avg_7day=5000.0,  # Default fallback
                daily_progress_pct=50.0,
                sessions_completed=2,
                estimated_daily_total=5000.0,
                timestamp=datetime.utcnow()
            )
    
    async def analyze_session_volume(self, symbol: str, timeframe: str = '15m', 
                                   exchange: str = 'binance') -> SessionAnalysis:
        """Complete session volume analysis"""
        try:
            # Get current session
            session_name, current_session = self._get_current_session()
            
            # Get current session volume
            current_session.current_volume = await self._calculate_session_volume(
                symbol, session_name, timeframe, exchange
            )
            
            # Get session baseline
            session_baseline = await self._get_session_baseline(
                symbol, session_name, timeframe, exchange
            )
            
            # Get daily context
            daily_context = await self._get_daily_volume_context(symbol, timeframe, exchange)
            
            # Calculate relative metrics
            session_rel_volume = (current_session.current_volume / session_baseline.avg_total_volume 
                                if session_baseline.avg_total_volume > 0 else 0)
            
            # Current hourly rate in session
            if current_session.session_progress > 0:
                hours_elapsed = current_session.session_progress * current_session.duration_hours
                session_hourly_rate = current_session.current_volume / hours_elapsed if hours_elapsed > 0 else 0
            else:
                session_hourly_rate = 0
            
            session_hourly_rel = (session_hourly_rate / session_baseline.avg_hourly_rate 
                                if session_baseline.avg_hourly_rate > 0 else 0)
            
            # Session share calculations
            session_share_current = (current_session.current_volume / daily_context.current_daily_volume * 100
                                   if daily_context.current_daily_volume > 0 else 0)
            
            session_share_typical = session_baseline.typical_daily_pct * 100
            
            # DST info
            is_dst, dst_adjustment = self._is_dst_active()
            
            return SessionAnalysis(
                current_session=current_session,
                session_baseline=session_baseline,
                daily_context=daily_context,
                session_rel_volume=round(session_rel_volume, 2),
                session_hourly_rate=round(session_hourly_rate, 2),
                session_hourly_rel=round(session_hourly_rel, 2),
                session_share_current=round(session_share_current, 1),
                session_share_typical=round(session_share_typical, 1),
                is_dst_active=is_dst,
                dst_adjustment=dst_adjustment
            )
            
        except Exception as e:
            logger.error(f"Error in session volume analysis: {e}")
            # Return safe defaults
            return SessionAnalysis(
                current_session=SessionVolumeData('unknown', '00:00', '24:00', 24, 0.0, 0.0, 1, 24, datetime.utcnow()),
                session_baseline=SessionBaseline('unknown', 1000.0, 100.0, 25.0, [1000.0], datetime.utcnow()),
                daily_context=DailyVolumeContext(0.0, 5000.0, 50.0, 2, 5000.0, datetime.utcnow()),
                session_rel_volume=1.0,
                session_hourly_rate=100.0,
                session_hourly_rel=1.0,
                session_share_current=20.0,
                session_share_typical=25.0,
                is_dst_active=False,
                dst_adjustment="Error in calculation"
            )