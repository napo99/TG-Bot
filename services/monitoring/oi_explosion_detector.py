"""
OI Explosion Detector Service
Monitors Open Interest changes across exchanges
Detects institutional position building and explosions
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import time

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.models.compact_oi_data import OIDataManager, OISnapshot
from shared.config.alert_thresholds import OI_EXPLOSION_THRESHOLDS, EXCHANGE_CONFIG


class OIExplosionDetector:
    """
    OI explosion detection service
    Monitors OI changes across multiple exchanges
    Detects significant position building
    """
    
    def __init__(self):
        # Configuration
        self.market_data_url = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
        self.monitoring_interval = EXCHANGE_CONFIG["oi_monitoring_interval"]  # 5 minutes
        self.api_timeout = EXCHANGE_CONFIG["api_timeout_seconds"]
        
        # Data manager
        self.oi_manager = OIDataManager(target_memory_mb=40)
        
        # State
        self.running = False
        self.session = None
        self.last_alerts: Dict[str, datetime] = {}  # Deduplication
        self.alert_output_path = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/oi_alerts.json"
        
        # Monitored symbols (focus on major pairs)
        self.monitored_symbols = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "ATOM"]
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure alert output directory exists
        os.makedirs(os.path.dirname(self.alert_output_path), exist_ok=True)
    
    async def start(self) -> None:
        """Start the OI explosion detector"""
        self.logger.info("Starting OI explosion detector...")
        self.running = True
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.api_timeout))
        
        try:
            # Start concurrent tasks
            monitor_task = asyncio.create_task(self.monitor_oi_changes())
            cleanup_task = asyncio.create_task(self.periodic_cleanup())
            
            # Wait for tasks
            await asyncio.gather(monitor_task, cleanup_task)
            
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the OI explosion detector"""
        self.logger.info("Stopping OI explosion detector...")
        self.running = False
        
        if self.session:
            await self.session.close()
    
    async def monitor_oi_changes(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                start_time = time.time()
                
                # Collect OI data for all monitored symbols
                for symbol in self.monitored_symbols:
                    await self.collect_symbol_oi(symbol)
                
                # Detect explosions
                explosions = self.oi_manager.detect_explosions()
                
                # Process detected explosions
                for explosion in explosions:
                    await self.process_explosion(explosion)
                
                # Log performance
                elapsed = time.time() - start_time
                self.logger.info(f"OI monitoring cycle completed in {elapsed:.2f}s, {len(explosions)} explosions detected")
                
                # Wait for next cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def collect_symbol_oi(self, symbol: str) -> None:
        """Collect OI data for a specific symbol"""
        try:
            # Get OI data from existing market-data service
            oi_data = await self.fetch_oi_data(symbol)
            
            if oi_data:
                # Convert to OI snapshots
                current_timestamp = int(datetime.now().timestamp())
                
                for exchange, oi_info in oi_data.items():
                    if isinstance(oi_info, dict) and "oi_usd" in oi_info:
                        snapshot = OISnapshot(
                            timestamp=current_timestamp,
                            exchange=exchange,
                            symbol=symbol,
                            oi_usd=float(oi_info["oi_usd"]),
                            oi_change_24h=float(oi_info.get("oi_change_24h", 0))
                        )
                        
                        self.oi_manager.add_oi_snapshot(snapshot)
            
        except Exception as e:
            self.logger.error(f"Error collecting OI for {symbol}: {e}")
    
    async def fetch_oi_data(self, symbol: str) -> Optional[Dict]:
        """Fetch OI data from existing market-data service"""
        try:
            # Use existing /multi_oi endpoint (read-only)
            url = f"{self.market_data_url}/multi_oi"
            payload = {"symbol": f"{symbol}-USDT"}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "success" in data and data["success"]:
                        return data.get("data", {})
                else:
                    self.logger.warning(f"API request failed for {symbol}: {response.status}")
                    
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout fetching OI data for {symbol}")
        except Exception as e:
            self.logger.error(f"Error fetching OI data for {symbol}: {e}")
        
        return None
    
    async def process_explosion(self, explosion: Dict) -> None:
        """Process detected OI explosion"""
        symbol = explosion["symbol"]
        avg_change = explosion["avg_change_pct"]
        total_oi = explosion["total_oi"]
        
        # Check deduplication
        alert_key = f"{symbol}_{int(abs(avg_change))}"
        current_time = datetime.now()
        
        if alert_key in self.last_alerts:
            time_since_last = current_time - self.last_alerts[alert_key]
            if time_since_last.total_seconds() < 300:  # 5 minutes
                return  # Skip duplicate alert
        
        self.last_alerts[alert_key] = current_time
        
        # Create alert
        alert_data = {
            "type": "oi_explosion",
            "timestamp": current_time.isoformat(),
            "symbol": symbol,
            "change_pct": avg_change,
            "total_oi": total_oi,
            "new_oi": total_oi,  # For compatibility
            "confirming_exchanges": len(explosion["exploding_exchanges"]),
            "exchange_details": explosion["exploding_exchanges"],
            "message": self.format_explosion_message(explosion)
        }
        
        await self.send_alert(alert_data)
    
    def format_explosion_message(self, explosion: Dict) -> str:
        """Format explosion data into alert message"""
        symbol = explosion["symbol"]
        avg_change = explosion["avg_change_pct"]
        total_oi = explosion["total_oi"]
        confirming_exchanges = len(explosion["exploding_exchanges"])
        
        # Determine direction
        direction_emoji = "📈" if avg_change > 0 else "📉"
        direction_word = "EXPLOSION" if avg_change > 0 else "COLLAPSE"
        
        # Format message
        message = f"🚨 {symbol} OI {direction_word}\n"
        message += f"{direction_emoji} {avg_change:+.1f}% increase in 15 minutes\n"
        message += f"💰 Total OI: ${total_oi:,.0f}\n"
        message += f"🏦 {confirming_exchanges}/3 exchanges confirming\n"
        
        if abs(avg_change) > 20:
            message += f"⚡ Institutional positioning detected"
        else:
            message += f"📊 Significant position building activity"
        
        return message
    
    async def send_alert(self, alert_data: Dict) -> None:
        """Send alert to JSON file"""
        try:
            # Read existing alerts
            alerts = []
            if os.path.exists(self.alert_output_path):
                with open(self.alert_output_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        alerts = json.loads(content)
            
            # Add new alert
            alerts.append(alert_data)
            
            # Keep only last 100 alerts
            alerts = alerts[-100:]
            
            # Write back
            with open(self.alert_output_path, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            self.logger.info(f"OI explosion alert sent: {alert_data['symbol']} {alert_data['change_pct']:+.1f}%")
            
        except Exception as e:
            self.logger.error(f"Failed to write OI alert: {e}")
    
    async def periodic_cleanup(self) -> None:
        """Periodic cleanup and memory management"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean old data
                self.oi_manager.cleanup_memory()
                
                # Clean old alerts from deduplication
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=1)
                
                self.last_alerts = {
                    k: v for k, v in self.last_alerts.items() if v > cutoff_time
                }
                
                # Log memory usage
                memory_stats = self.oi_manager.get_memory_usage()
                self.logger.info(f"Memory usage: {memory_stats['total_mb']:.1f}MB across {memory_stats['symbols_count']} symbols")
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get detector status"""
        memory_stats = self.oi_manager.get_memory_usage()
        
        return {
            "running": self.running,
            "monitored_symbols": len(self.monitored_symbols),
            "memory_usage_mb": memory_stats["total_mb"],
            "symbols_tracked": memory_stats["symbols_count"],
            "last_alerts_count": len(self.last_alerts),
            "api_url": self.market_data_url
        }
    
    async def test_connection(self) -> bool:
        """Test connection to market data service"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            
            url = f"{self.market_data_url}/health"
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


async def main():
    """Main entry point"""
    detector = OIExplosionDetector()
    
    try:
        await detector.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        await detector.stop()


if __name__ == "__main__":
    asyncio.run(main())