#!/usr/bin/env python3
"""
REAL-TIME AGENT MONITORING & ALERT SYSTEM
Continuously monitor agent claims against external reality
PRINCIPLE: Trust but verify - constantly
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

@dataclass
class MonitoringAlert:
    alert_id: str
    alert_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    agent_claim: str
    external_reality: str
    deviation_pct: float
    threshold_exceeded: str
    timestamp: datetime
    evidence: str
    action_required: str

class RealTimeAgentMonitor:
    """
    Continuously monitors agent claims against external reality
    Generates immediate alerts when deviations exceed thresholds
    """
    
    def __init__(self):
        self.monitoring_thresholds = {
            'price_deviation': 5.0,      # Max 5% price deviation
            'oi_calculation_error': 1.0,  # Max 1% calculation error
            'exchange_oi_deviation': 15.0, # Max 15% OI deviation
            'magnitude_sanity': 100.0     # Max 100% magnitude error
        }
        
        self.alert_channels = ['console', 'log', 'telegram']  # Add email, slack etc.
        self.monitoring_active = True
        self.alert_history = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start_continuous_monitoring(self, agent_endpoint: str, symbol: str, interval_seconds: int = 300):
        """Start continuous monitoring of agent claims"""
        self.logger.info(f"🚀 Starting continuous monitoring for {symbol} at {agent_endpoint}")
        self.logger.info(f"📊 Monitoring interval: {interval_seconds} seconds")
        self.logger.info(f"⚠️ Alert thresholds: {self.monitoring_thresholds}")
        
        while self.monitoring_active:
            try:
                # Get agent claims
                agent_data = await self._fetch_agent_claims(agent_endpoint, symbol)
                
                if agent_data:
                    # Validate against external reality
                    alerts = await self._validate_against_reality(agent_data, symbol)
                    
                    # Process alerts
                    for alert in alerts:
                        await self._process_alert(alert)
                        self.alert_history.append(alert)
                    
                    # Log monitoring status
                    if alerts:
                        self.logger.warning(f"⚠️ Generated {len(alerts)} alerts for {symbol}")
                    else:
                        self.logger.info(f"✅ No alerts for {symbol} - agent claims validated")
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _fetch_agent_claims(self, endpoint: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current agent claims"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json={'base_symbol': symbol}, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data['data']
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch agent claims: {str(e)}")
            return None
    
    async def _validate_against_reality(self, agent_data: Dict[str, Any], symbol: str) -> List[MonitoringAlert]:
        """Validate agent claims against external reality"""
        alerts = []
        
        try:
            # Validate each exchange claim
            if 'exchange_breakdown' in agent_data:
                for exchange_data in agent_data['exchange_breakdown']:
                    exchange = exchange_data.get('exchange', '')
                    
                    # Price validation
                    price_alert = await self._validate_price_claim(
                        symbol, exchange, exchange_data.get('price', 0)
                    )
                    if price_alert:
                        alerts.append(price_alert)
                    
                    # OI calculation validation
                    calc_alert = await self._validate_calculation_claim(
                        symbol, exchange, exchange_data
                    )
                    if calc_alert:
                        alerts.append(calc_alert)
                    
                    # Exchange OI validation
                    oi_alert = await self._validate_exchange_oi_claim(
                        symbol, exchange, exchange_data.get('oi_tokens', 0)
                    )
                    if oi_alert:
                        alerts.append(oi_alert)
            
            # Magnitude sanity validation
            magnitude_alert = await self._validate_magnitude_sanity(
                symbol, agent_data.get('aggregated_oi', {}).get('total_usd', 0)
            )
            if magnitude_alert:
                alerts.append(magnitude_alert)
        
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
        
        return alerts
    
    async def _validate_price_claim(self, symbol: str, exchange: str, agent_price: float) -> Optional[MonitoringAlert]:
        """Validate price claim against external sources"""
        try:
            external_price = await self._get_external_price(symbol)
            
            if external_price and agent_price > 0:
                deviation_pct = abs(agent_price - external_price) / external_price * 100
                
                if deviation_pct > self.monitoring_thresholds['price_deviation']:
                    return MonitoringAlert(
                        alert_id=f"price_{symbol}_{exchange}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type='price_deviation',
                        severity='HIGH' if deviation_pct > 10.0 else 'MEDIUM',
                        agent_claim=f"${agent_price:,.2f}",
                        external_reality=f"${external_price:,.2f}",
                        deviation_pct=deviation_pct,
                        threshold_exceeded=f">{self.monitoring_thresholds['price_deviation']}%",
                        timestamp=datetime.now(),
                        evidence=f"{exchange} {symbol}: Agent ${agent_price:,.2f} vs External ${external_price:,.2f}",
                        action_required="Investigate price source accuracy"
                    )
        except Exception as e:
            self.logger.error(f"Price validation error: {str(e)}")
        
        return None
    
    async def _validate_calculation_claim(self, symbol: str, exchange: str, exchange_data: Dict[str, Any]) -> Optional[MonitoringAlert]:
        """Validate calculation claim against mathematical ground truth"""
        try:
            oi_tokens = exchange_data.get('oi_tokens', 0)
            oi_usd = exchange_data.get('oi_usd', 0)
            price = exchange_data.get('price', 0)
            
            if oi_tokens > 0 and price > 0:
                expected_oi_usd = oi_tokens * price
                deviation_pct = abs(oi_usd - expected_oi_usd) / expected_oi_usd * 100
                
                if deviation_pct > self.monitoring_thresholds['oi_calculation_error']:
                    return MonitoringAlert(
                        alert_id=f"calc_{symbol}_{exchange}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type='calculation_error',
                        severity='CRITICAL',  # Calculation errors are always critical
                        agent_claim=f"${oi_usd/1e9:.1f}B",
                        external_reality=f"${expected_oi_usd/1e9:.1f}B",
                        deviation_pct=deviation_pct,
                        threshold_exceeded=f">{self.monitoring_thresholds['oi_calculation_error']}%",
                        timestamp=datetime.now(),
                        evidence=f"{exchange}: Agent ${oi_usd/1e9:.1f}B vs Expected ${expected_oi_usd/1e9:.1f}B ({oi_tokens:,.0f} × ${price:,.0f})",
                        action_required="Fix USD calculation logic immediately"
                    )
        except Exception as e:
            self.logger.error(f"Calculation validation error: {str(e)}")
        
        return None
    
    async def _validate_exchange_oi_claim(self, symbol: str, exchange: str, agent_oi: float) -> Optional[MonitoringAlert]:
        """Validate OI claim against direct exchange API"""
        try:
            external_oi = await self._get_external_oi(symbol, exchange)
            
            if external_oi and agent_oi > 0:
                deviation_pct = abs(agent_oi - external_oi) / external_oi * 100
                
                if deviation_pct > self.monitoring_thresholds['exchange_oi_deviation']:
                    return MonitoringAlert(
                        alert_id=f"oi_{symbol}_{exchange}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type='oi_deviation',
                        severity='MEDIUM',
                        agent_claim=f"{agent_oi:,.0f}",
                        external_reality=f"{external_oi:,.0f}",
                        deviation_pct=deviation_pct,
                        threshold_exceeded=f">{self.monitoring_thresholds['exchange_oi_deviation']}%",
                        timestamp=datetime.now(),
                        evidence=f"{exchange} {symbol}: Agent {agent_oi:,.0f} vs External {external_oi:,.0f}",
                        action_required="Verify OI data source and processing"
                    )
        except Exception as e:
            self.logger.error(f"Exchange OI validation error: {str(e)}")
        
        return None
    
    async def _validate_magnitude_sanity(self, symbol: str, total_oi_usd: float) -> Optional[MonitoringAlert]:
        """Validate magnitude sanity against known market reality"""
        try:
            # Known reasonable ranges for major cryptocurrencies
            known_ranges = {
                'BTC': {'min': 10_000_000_000, 'max': 50_000_000_000},  # $10B - $50B
                'ETH': {'min': 5_000_000_000, 'max': 25_000_000_000},   # $5B - $25B
            }
            
            if symbol.upper() in known_ranges:
                range_data = known_ranges[symbol.upper()]
                
                if total_oi_usd < range_data['min'] or total_oi_usd > range_data['max']:
                    # Calculate how far outside the range
                    if total_oi_usd < range_data['min']:
                        deviation_pct = (range_data['min'] - total_oi_usd) / range_data['min'] * 100
                    else:
                        deviation_pct = (total_oi_usd - range_data['max']) / range_data['max'] * 100
                    
                    return MonitoringAlert(
                        alert_id=f"magnitude_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type='magnitude_sanity',
                        severity='HIGH' if deviation_pct > 200.0 else 'MEDIUM',
                        agent_claim=f"${total_oi_usd/1e9:.1f}B",
                        external_reality=f"${range_data['min']/1e9:.1f}B - ${range_data['max']/1e9:.1f}B",
                        deviation_pct=deviation_pct,
                        threshold_exceeded="Outside known range",
                        timestamp=datetime.now(),
                        evidence=f"{symbol} total OI: ${total_oi_usd/1e9:.1f}B vs expected ${range_data['min']/1e9:.1f}B-${range_data['max']/1e9:.1f}B",
                        action_required="Investigate total OI calculation and aggregation"
                    )
        except Exception as e:
            self.logger.error(f"Magnitude validation error: {str(e)}")
        
        return None
    
    async def _process_alert(self, alert: MonitoringAlert):
        """Process and distribute alerts through configured channels"""
        alert_message = self._format_alert_message(alert)
        
        for channel in self.alert_channels:
            try:
                if channel == 'console':
                    await self._send_console_alert(alert_message, alert.severity)
                elif channel == 'log':
                    await self._send_log_alert(alert_message, alert.severity)
                elif channel == 'telegram':
                    await self._send_telegram_alert(alert_message, alert.severity)
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel}: {str(e)}")
    
    def _format_alert_message(self, alert: MonitoringAlert) -> str:
        """Format alert message for distribution"""
        severity_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️'
        }
        
        return f"""
{severity_emoji.get(alert.severity, '⚠️')} **AGENT MONITORING ALERT**

**Alert Type:** {alert.alert_type}
**Severity:** {alert.severity}
**Timestamp:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**Deviation:** {alert.deviation_pct:.2f}% ({alert.threshold_exceeded})
**Agent Claim:** {alert.agent_claim}
**External Reality:** {alert.external_reality}

**Evidence:** {alert.evidence}
**Action Required:** {alert.action_required}

**Alert ID:** {alert.alert_id}
"""
    
    async def _send_console_alert(self, message: str, severity: str):
        """Send alert to console"""
        if severity == 'CRITICAL':
            print(f"\033[91m{message}\033[0m")  # Red
        elif severity == 'HIGH':
            print(f"\033[93m{message}\033[0m")  # Yellow
        else:
            print(message)
    
    async def _send_log_alert(self, message: str, severity: str):
        """Send alert to log file"""
        if severity == 'CRITICAL':
            self.logger.critical(message)
        elif severity == 'HIGH':
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    async def _send_telegram_alert(self, message: str, severity: str):
        """Send alert to Telegram (placeholder - implement with bot token)"""
        # Implement Telegram bot alert sending
        self.logger.info(f"Telegram alert: {severity} - {message[:100]}...")
    
    async def _get_external_price(self, symbol: str) -> Optional[float]:
        """Get price from external source"""
        try:
            symbol_map = {'BTC': 'bitcoin', 'ETH': 'ethereum'}
            cg_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    return data[cg_id]['usd']
        except:
            return None
    
    async def _get_external_oi(self, symbol: str, exchange: str) -> Optional[float]:
        """Get OI from external source"""
        try:
            if exchange.lower() == 'binance':
                async with aiohttp.ClientSession() as session:
                    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol.upper()}USDT"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        data = await response.json()
                        return float(data['openInterest'])
            elif exchange.lower() == 'bybit':
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol.upper()}USDT"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        data = await response.json()
                        if data['retCode'] == 0 and data['result']['list']:
                            return float(data['result']['list'][0]['openInterest'])
        except:
            pass
        return None
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        self.logger.info("🛑 Monitoring stopped")
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        severity_counts = {}
        alert_type_counts = {}
        
        for alert in recent_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
            alert_type_counts[alert.alert_type] = alert_type_counts.get(alert.alert_type, 0) + 1
        
        return {
            'period_hours': hours,
            'total_alerts': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'alert_type_breakdown': alert_type_counts,
            'most_recent_alert': recent_alerts[-1].timestamp.isoformat() if recent_alerts else None
        }

# Usage Example
async def start_agent_monitoring():
    """Start monitoring agent claims in real-time"""
    monitor = RealTimeAgentMonitor()
    
    # Configure monitoring thresholds
    monitor.monitoring_thresholds.update({
        'price_deviation': 3.0,       # Stricter price monitoring
        'oi_calculation_error': 0.5,  # Very strict calculation monitoring
        'exchange_oi_deviation': 10.0, # Stricter OI monitoring
        'magnitude_sanity': 50.0      # Stricter magnitude monitoring
    })
    
    # Start monitoring
    agent_endpoint = 'http://localhost:8001/multi_oi'
    symbol = 'BTC'
    monitoring_interval = 60  # Check every minute
    
    print(f"🚀 Starting real-time monitoring for {symbol}")
    print(f"📊 Endpoint: {agent_endpoint}")
    print(f"⏱️ Interval: {monitoring_interval} seconds")
    print(f"⚠️ Thresholds: {monitor.monitoring_thresholds}")
    
    try:
        await monitor.start_continuous_monitoring(agent_endpoint, symbol, monitoring_interval)
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring...")
        monitor.stop_monitoring()
        
        # Show summary
        summary = monitor.get_alert_summary(1)  # Last hour
        print(f"\n📊 MONITORING SUMMARY (Last Hour):")
        print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    asyncio.run(start_agent_monitoring())