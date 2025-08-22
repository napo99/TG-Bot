"""
Alert Dispatcher Service
Aggregates and dispatches alerts from monitoring services
Priority queue management and rate limiting
"""

import asyncio
import json
import logging
import sqlite3
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import IntEnum
import hashlib

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.utils.telegram_client import TelegramClient
from shared.config.alert_thresholds import ALERT_RATE_LIMITS


class AlertPriority(IntEnum):
    """Alert priority levels"""
    HIGH = 1    # Immediate dispatch
    MEDIUM = 2  # Dispatch within 30 seconds
    LOW = 3     # Dispatch within 60 seconds


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    priority: AlertPriority
    alert_type: str
    data: Dict
    created_at: datetime
    attempts: int = 0
    next_retry: Optional[datetime] = None


class AlertDispatcher:
    """
    Alert dispatch service with priority queue and rate limiting
    Aggregates alerts from liquidation and OI monitoring
    """
    
    def __init__(self):
        # File paths
        self.liquidation_alerts_path = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/liquidation_alerts.json"
        self.oi_alerts_path = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/oi_alerts.json"
        self.db_path = "/Users/screener-m3/projects/crypto-assistant/data/alerts.db"
        
        # State
        self.running = False
        self.alert_queue: List[Alert] = []
        self.sent_alerts: Set[str] = set()  # Deduplication
        self.user_alert_counts: Dict[str, List[datetime]] = {}
        
        # Telegram client
        self.telegram_client = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.liquidation_alerts_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize SQLite database for alert history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    sent_at TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT FALSE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    chat_id TEXT PRIMARY KEY,
                    liquidation_alerts BOOLEAN DEFAULT TRUE,
                    oi_alerts BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def start(self) -> None:
        """Start the alert dispatcher"""
        self.logger.info("Starting alert dispatcher...")
        self.running = True
        
        # Initialize Telegram client
        self.telegram_client = TelegramClient()
        
        try:
            async with self.telegram_client:
                # Start concurrent tasks
                monitor_task = asyncio.create_task(self.monitor_alert_files())
                dispatch_task = asyncio.create_task(self.dispatch_alerts())
                cleanup_task = asyncio.create_task(self.cleanup_old_data())
                
                # Wait for tasks
                await asyncio.gather(monitor_task, dispatch_task, cleanup_task)
                
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the alert dispatcher"""
        self.logger.info("Stopping alert dispatcher...")
        self.running = False
    
    async def monitor_alert_files(self) -> None:
        """Monitor alert files for new alerts"""
        last_liquidation_check = 0
        last_oi_check = 0
        
        while self.running:
            try:
                # Check liquidation alerts
                if os.path.exists(self.liquidation_alerts_path):
                    stat = os.stat(self.liquidation_alerts_path)
                    if stat.st_mtime > last_liquidation_check:
                        await self.process_liquidation_alerts()
                        last_liquidation_check = stat.st_mtime
                
                # Check OI alerts
                if os.path.exists(self.oi_alerts_path):
                    stat = os.stat(self.oi_alerts_path)
                    if stat.st_mtime > last_oi_check:
                        await self.process_oi_alerts()
                        last_oi_check = stat.st_mtime
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring alert files: {e}")
                await asyncio.sleep(10)
    
    async def process_liquidation_alerts(self) -> None:
        """Process new liquidation alerts"""
        try:
            with open(self.liquidation_alerts_path, 'r') as f:
                alerts = json.load(f)
            
            for alert_data in alerts:
                alert_id = self.generate_alert_id(alert_data)
                
                if alert_id not in self.sent_alerts:
                    priority = self.determine_priority(alert_data)
                    alert = Alert(
                        id=alert_id,
                        priority=priority,
                        alert_type="liquidation",
                        data=alert_data,
                        created_at=datetime.now()
                    )
                    
                    self.add_alert_to_queue(alert)
                    self.sent_alerts.add(alert_id)
            
        except FileNotFoundError:
            pass  # File doesn't exist yet
        except Exception as e:
            self.logger.error(f"Error processing liquidation alerts: {e}")
    
    async def process_oi_alerts(self) -> None:
        """Process new OI alerts"""
        try:
            with open(self.oi_alerts_path, 'r') as f:
                alerts = json.load(f)
            
            for alert_data in alerts:
                alert_id = self.generate_alert_id(alert_data)
                
                if alert_id not in self.sent_alerts:
                    priority = self.determine_priority(alert_data)
                    alert = Alert(
                        id=alert_id,
                        priority=priority,
                        alert_type="oi",
                        data=alert_data,
                        created_at=datetime.now()
                    )
                    
                    self.add_alert_to_queue(alert)
                    self.sent_alerts.add(alert_id)
            
        except FileNotFoundError:
            pass  # File doesn't exist yet
        except Exception as e:
            self.logger.error(f"Error processing OI alerts: {e}")
    
    def generate_alert_id(self, alert_data: Dict) -> str:
        """Generate unique alert ID for deduplication"""
        # Create hash of essential alert data
        key_data = {
            "type": alert_data.get("type"),
            "timestamp": alert_data.get("timestamp", "")[:16],  # Minute precision
            "symbol": alert_data.get("symbol", alert_data.get("primary_symbol", "")),
            "value": alert_data.get("value_usd", alert_data.get("total_value_usd", 0))
        }
        
        hash_input = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def determine_priority(self, alert_data: Dict) -> AlertPriority:
        """Determine alert priority based on alert data"""
        alert_type = alert_data.get("type", "")
        
        if alert_type == "liquidation_cascade":
            total_value = alert_data.get("total_value_usd", 0)
            if total_value > 1_000_000:  # $1M+
                return AlertPriority.HIGH
            elif total_value > 500_000:  # $500K+
                return AlertPriority.MEDIUM
            else:
                return AlertPriority.LOW
        
        elif alert_type == "single_liquidation":
            value = alert_data.get("value_usd", 0)
            if value > 500_000:  # $500K+
                return AlertPriority.HIGH
            elif value > 100_000:  # $100K+
                return AlertPriority.MEDIUM
            else:
                return AlertPriority.LOW
        
        elif alert_type == "oi_explosion":
            change_pct = abs(alert_data.get("change_pct", 0))
            if change_pct > 25:  # 25%+
                return AlertPriority.HIGH
            elif change_pct > 18:  # 18%+
                return AlertPriority.MEDIUM
            else:
                return AlertPriority.LOW
        
        return AlertPriority.LOW
    
    def add_alert_to_queue(self, alert: Alert) -> None:
        """Add alert to priority queue"""
        self.alert_queue.append(alert)
        # Sort by priority (HIGH=1, MEDIUM=2, LOW=3)
        self.alert_queue.sort(key=lambda a: (a.priority.value, a.created_at))
        
        self.logger.info(f"Alert queued: {alert.alert_type} (Priority: {alert.priority.name})")
    
    async def dispatch_alerts(self) -> None:
        """Main alert dispatch loop"""
        while self.running:
            try:
                if not self.alert_queue:
                    await asyncio.sleep(1)
                    continue
                
                # Get next alert to dispatch
                alert = self.get_next_alert()
                if not alert:
                    await asyncio.sleep(1)
                    continue
                
                # Check rate limiting
                if not self.can_send_alert():
                    await asyncio.sleep(5)
                    continue
                
                # Dispatch alert
                success = await self.send_alert(alert)
                
                if success:
                    self.log_alert_success(alert)
                    self.alert_queue.remove(alert)
                else:
                    self.handle_alert_failure(alert)
                
            except Exception as e:
                self.logger.error(f"Error in dispatch loop: {e}")
                await asyncio.sleep(5)
    
    def get_next_alert(self) -> Optional[Alert]:
        """Get next alert to dispatch based on priority and timing"""
        current_time = datetime.now()
        
        for alert in self.alert_queue:
            # Check if it's time to send this alert
            if alert.next_retry and current_time < alert.next_retry:
                continue
            
            # Check priority timing
            time_since_creation = current_time - alert.created_at
            
            if alert.priority == AlertPriority.HIGH:
                return alert  # Send immediately
            elif alert.priority == AlertPriority.MEDIUM and time_since_creation.seconds >= 30:
                return alert  # Send after 30 seconds
            elif alert.priority == AlertPriority.LOW and time_since_creation.seconds >= 60:
                return alert  # Send after 60 seconds
        
        return None
    
    def can_send_alert(self) -> bool:
        """Check if we can send an alert (rate limiting)"""
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "default")
        current_time = datetime.now()
        
        # Clean old timestamps
        if chat_id in self.user_alert_counts:
            cutoff_time = current_time - timedelta(hours=1)
            self.user_alert_counts[chat_id] = [
                t for t in self.user_alert_counts[chat_id] if t > cutoff_time
            ]
        else:
            self.user_alert_counts[chat_id] = []
        
        # Check rate limit
        return len(self.user_alert_counts[chat_id]) < ALERT_RATE_LIMITS["max_alerts_per_hour"]
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        try:
            if not self.telegram_client:
                return False
            
            success = await self.telegram_client.send_alert(alert.data)
            
            if success:
                # Update rate limiting
                chat_id = os.getenv("TELEGRAM_CHAT_ID", "default")
                self.user_alert_counts[chat_id].append(datetime.now())
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending alert {alert.id}: {e}")
            return False
    
    def log_alert_success(self, alert: Alert) -> None:
        """Log successful alert dispatch"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO alert_history
                (id, alert_type, priority, data, created_at, sent_at, attempts, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.alert_type,
                alert.priority.value,
                json.dumps(alert.data),
                alert.created_at.isoformat(),
                datetime.now().isoformat(),
                alert.attempts + 1,
                True
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Alert dispatched successfully: {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Error logging alert success: {e}")
    
    def handle_alert_failure(self, alert: Alert) -> None:
        """Handle failed alert dispatch"""
        alert.attempts += 1
        max_attempts = ALERT_RATE_LIMITS["max_retry_attempts"]
        
        if alert.attempts >= max_attempts:
            # Give up on this alert
            self.logger.error(f"Alert {alert.id} failed after {max_attempts} attempts")
            self.alert_queue.remove(alert)
            return
        
        # Schedule retry with backoff
        backoff_delays = ALERT_RATE_LIMITS["retry_backoff_seconds"]
        delay_index = min(alert.attempts - 1, len(backoff_delays) - 1)
        delay_seconds = backoff_delays[delay_index]
        
        alert.next_retry = datetime.now() + timedelta(seconds=delay_seconds)
        
        self.logger.warning(f"Alert {alert.id} failed (attempt {alert.attempts}), retrying in {delay_seconds}s")
    
    async def cleanup_old_data(self) -> None:
        """Cleanup old alerts and data"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean in-memory data
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                # Clean sent alerts set (keep last 1000)
                if len(self.sent_alerts) > 1000:
                    self.sent_alerts = set(list(self.sent_alerts)[-1000:])
                
                # Clean database
                self.cleanup_database(cutoff_time)
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    def cleanup_database(self, cutoff_time: datetime) -> None:
        """Clean old database entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old alert history
            cursor.execute(
                "DELETE FROM alert_history WHERE created_at < ?",
                (cutoff_time.isoformat(),)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get dispatcher status"""
        return {
            "running": self.running,
            "queue_size": len(self.alert_queue),
            "sent_alerts_count": len(self.sent_alerts),
            "telegram_connected": self.telegram_client is not None
        }


async def main():
    """Main entry point"""
    dispatcher = AlertDispatcher()
    
    try:
        await dispatcher.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        await dispatcher.stop()


if __name__ == "__main__":
    asyncio.run(main())