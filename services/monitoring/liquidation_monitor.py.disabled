"""
Liquidation Monitor Service
Real-time WebSocket monitoring of Binance liquidations
Detects cascades and large liquidations
"""

import asyncio
import json
import websockets
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.models.compact_liquidation import CompactLiquidation, LiquidationBuffer
from shared.config.alert_thresholds import LIQUIDATION_THRESHOLDS


class LiquidationMonitor:
    """
    Real-time liquidation monitoring service
    Connects to Binance WebSocket for force liquidation stream
    """
    
    def __init__(self):
        self.websocket_url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        self.buffer = LiquidationBuffer(max_size=1000)
        self.running = False
        self.websocket = None
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 16
        self.alert_output_path = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/liquidation_alerts.json"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure alert output directory exists
        os.makedirs(os.path.dirname(self.alert_output_path), exist_ok=True)
    
    async def connect(self) -> None:
        """Connect to Binance WebSocket"""
        try:
            self.logger.info(f"Connecting to {self.websocket_url}")
            self.websocket = await websockets.connect(self.websocket_url)
            self.logger.info("Connected to Binance liquidation stream")
            self.reconnect_delay = 1  # Reset reconnect delay on success
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("Disconnected from WebSocket")
    
    async def reconnect(self) -> None:
        """Reconnect with exponential backoff"""
        self.logger.warning(f"Reconnecting in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        
        # Exponential backoff
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        try:
            await self.connect()
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            await self.reconnect()  # Try again
    
    def process_liquidation(self, data: dict) -> Optional[CompactLiquidation]:
        """Process incoming liquidation data"""
        try:
            liquidation = CompactLiquidation.from_binance_data(data)
            
            # Add to buffer
            self.buffer.add(liquidation)
            
            # Check if this liquidation meets alert criteria
            if self.should_alert_single(liquidation):
                asyncio.create_task(self.send_single_liquidation_alert(liquidation))
            
            # Check for cascade
            if self.should_check_cascade():
                cascade_liq, total_value = self.buffer.get_cascade_data(30)
                if self.should_alert_cascade(cascade_liq, total_value):
                    asyncio.create_task(self.send_cascade_alert(cascade_liq, total_value))
            
            return liquidation
            
        except Exception as e:
            self.logger.error(f"Error processing liquidation: {e}")
            return None
    
    def should_alert_single(self, liquidation: CompactLiquidation) -> bool:
        """Check if single liquidation meets alert criteria"""
        value = liquidation.actual_value_usd
        
        # Check against thresholds for major assets
        if liquidation.symbol_hash == hash("BTCUSDT") & 0xFFFFFFFF:
            return value >= LIQUIDATION_THRESHOLDS["BTC"]["single_large"]
        elif liquidation.symbol_hash == hash("ETHUSDT") & 0xFFFFFFFF:
            return value >= LIQUIDATION_THRESHOLDS["ETH"]["single_large"]
        elif liquidation.symbol_hash == hash("SOLUSDT") & 0xFFFFFFFF:
            return value >= LIQUIDATION_THRESHOLDS["SOL"]["single_large"]
        
        return False
    
    def should_check_cascade(self) -> bool:
        """Check if we should analyze for cascades (rate limited)"""
        # Check every 5 seconds to avoid excessive processing
        return len(self.buffer) % 10 == 0
    
    def should_alert_cascade(self, liquidations: List[CompactLiquidation], total_value: float) -> bool:
        """Check if liquidation cascade meets alert criteria"""
        if len(liquidations) < 5:  # Minimum cascade size
            return False
        
        # Analyze by symbol
        symbol_groups = {}
        for liq in liquidations:
            symbol_groups.setdefault(liq.symbol_hash, []).append(liq)
        
        # Check each major symbol
        for symbol_hash, group in symbol_groups.items():
            if symbol_hash == hash("BTCUSDT") & 0xFFFFFFFF:
                thresholds = LIQUIDATION_THRESHOLDS["BTC"]
            elif symbol_hash == hash("ETHUSDT") & 0xFFFFFFFF:
                thresholds = LIQUIDATION_THRESHOLDS["ETH"]
            elif symbol_hash == hash("SOLUSDT") & 0xFFFFFFFF:
                thresholds = LIQUIDATION_THRESHOLDS["SOL"]
            else:
                continue
            
            group_value = sum(liq.actual_value_usd for liq in group)
            
            if (len(group) >= thresholds["cascade_count"] and 
                group_value >= thresholds["cascade_value"]):
                return True
        
        return False
    
    async def send_single_liquidation_alert(self, liquidation: CompactLiquidation) -> None:
        """Send alert for large single liquidation"""
        alert_data = {
            "type": "single_liquidation",
            "timestamp": datetime.now().isoformat(),
            "symbol": self.get_symbol_from_hash(liquidation.symbol_hash),
            "side": liquidation.side_str,
            "price": liquidation.actual_price,
            "quantity": liquidation.actual_quantity,
            "value_usd": liquidation.actual_value_usd,
            "message": f"🚨 LARGE {liquidation.side_str} LIQUIDATION\n"
                      f"💰 ${liquidation.actual_value_usd:,.0f} liquidated\n"
                      f"📊 {liquidation.actual_quantity:.4f} @ ${liquidation.actual_price:,.2f}\n"
                      f"⚠️ Significant position liquidated"
        }
        
        await self.write_alert(alert_data)
    
    async def send_cascade_alert(self, liquidations: List[CompactLiquidation], total_value: float) -> None:
        """Send alert for liquidation cascade"""
        if not liquidations:
            return
        
        # Analyze cascade
        long_count = sum(1 for liq in liquidations if liq.side_str == "LONG")
        short_count = len(liquidations) - long_count
        
        # Get primary symbol
        symbol_counts = {}
        for liq in liquidations:
            symbol = self.get_symbol_from_hash(liq.symbol_hash)
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        primary_symbol = max(symbol_counts.keys(), key=lambda k: symbol_counts[k])
        
        alert_data = {
            "type": "liquidation_cascade",
            "timestamp": datetime.now().isoformat(),
            "primary_symbol": primary_symbol,
            "liquidation_count": len(liquidations),
            "total_value_usd": total_value,
            "long_count": long_count,
            "short_count": short_count,
            "message": f"🚨 {primary_symbol} LIQUIDATION CASCADE\n"
                      f"⚡ {len(liquidations)} liquidations in 30 seconds\n"
                      f"💰 Total: ${total_value:,.0f} liquidated\n"
                      f"📉 {long_count} longs, {short_count} shorts\n"
                      f"⚠️ Potential price impact expected"
        }
        
        await self.write_alert(alert_data)
    
    def get_symbol_from_hash(self, symbol_hash: int) -> str:
        """Get symbol name from hash (reverse lookup for major symbols)"""
        major_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT"]
        for symbol in major_symbols:
            if hash(symbol) & 0xFFFFFFFF == symbol_hash:
                return symbol.replace("USDT", "")
        return "UNKNOWN"
    
    async def write_alert(self, alert_data: dict) -> None:
        """Write alert to JSON file"""
        try:
            # Read existing alerts
            alerts = []
            if os.path.exists(self.alert_output_path):
                with open(self.alert_output_path, 'r') as f:
                    alerts = json.load(f)
            
            # Add new alert
            alerts.append(alert_data)
            
            # Keep only last 100 alerts
            alerts = alerts[-100:]
            
            # Write back
            with open(self.alert_output_path, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            self.logger.info(f"Alert sent: {alert_data['type']} - {alert_data.get('message', '').split(chr(10))[0]}")
            
        except Exception as e:
            self.logger.error(f"Failed to write alert: {e}")
    
    async def listen(self) -> None:
        """Main listening loop"""
        while self.running:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                self.process_liquidation(data)
                
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                if self.running:
                    await self.reconnect()
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error in listen loop: {e}")
                if self.running:
                    await self.reconnect()
    
    async def cleanup_old_data(self) -> None:
        """Periodic cleanup of old data"""
        while self.running:
            try:
                # Clean buffer every 5 minutes
                await asyncio.sleep(300)
                self.buffer.clear_old(300)  # Keep 5 minutes of data
                
                memory_usage = self.buffer.memory_usage()
                self.logger.info(f"Memory usage: {memory_usage} bytes, Buffer size: {len(self.buffer)}")
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    async def start(self) -> None:
        """Start the liquidation monitor"""
        self.logger.info("Starting liquidation monitor...")
        self.running = True
        
        try:
            await self.connect()
            
            # Start concurrent tasks
            listen_task = asyncio.create_task(self.listen())
            cleanup_task = asyncio.create_task(self.cleanup_old_data())
            
            # Wait for tasks
            await asyncio.gather(listen_task, cleanup_task)
            
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the liquidation monitor"""
        self.logger.info("Stopping liquidation monitor...")
        self.running = False
        await self.disconnect()
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            "running": self.running,
            "connected": self.websocket is not None,
            "buffer_size": len(self.buffer),
            "memory_usage_bytes": self.buffer.memory_usage(),
            "total_liquidations": len(self.buffer)
        }


async def main():
    """Main entry point"""
    monitor = LiquidationMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())