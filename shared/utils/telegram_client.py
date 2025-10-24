"""
Telegram Client for Alert Notifications
Independent Telegram client for proactive alerts
"""

import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os
from pathlib import Path


class TelegramClient:
    """
    Independent Telegram client for sending alerts
    Rate-limited and with retry logic
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable required")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable required")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None
        
        # Rate limiting
        self.message_times: List[datetime] = []
        self.max_messages_per_minute = 20  # Telegram limit
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _clean_old_message_times(self) -> None:
        """Clean message times older than 1 minute"""
        cutoff = datetime.now() - timedelta(minutes=1)
        self.message_times = [t for t in self.message_times if t > cutoff]
    
    def _can_send_message(self) -> bool:
        """Check if we can send a message (rate limiting)"""
        self._clean_old_message_times()
        return len(self.message_times) < self.max_messages_per_minute
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait until we can send a message"""
        while not self._can_send_message():
            await asyncio.sleep(1)
    
    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message via Telegram
        Returns True if successful, False otherwise
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        retry_count = 0
        max_retries = 3
        backoff_delays = [1, 2, 4]
        
        while retry_count < max_retries:
            try:
                async with self.session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.message_times.append(datetime.now())
                        self.logger.info("Message sent successfully")
                        return True
                    elif response.status == 429:
                        # Rate limited by Telegram
                        retry_after = int(response.headers.get("Retry-After", 60))
                        self.logger.warning(f"Rate limited by Telegram, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram API error {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                self.logger.error("Telegram API timeout")
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
            
            # Wait before retry
            if retry_count < max_retries - 1:
                await asyncio.sleep(backoff_delays[retry_count])
            retry_count += 1
        
        self.logger.error(f"Failed to send message after {max_retries} attempts")
        return False
    
    async def send_alert(self, alert_data: Dict) -> bool:
        """
        Send formatted alert message
        """
        try:
            message = self.format_alert_message(alert_data)
            return await self.send_message(message)
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    def format_alert_message(self, alert_data: Dict) -> str:
        """
        Format alert data into Telegram message
        """
        alert_type = alert_data.get("type", "unknown")
        message = alert_data.get("message", "")
        
        # Add timestamp
        timestamp = datetime.fromisoformat(alert_data.get("timestamp", datetime.now().isoformat()))
        time_str = timestamp.strftime("%H:%M:%S UTC")
        
        formatted_message = f"🕐 {time_str}\n{message}"
        
        # Add alert type specific formatting
        if alert_type == "liquidation_cascade":
            formatted_message += f"\n\n📊 *Details:*\n"
            formatted_message += f"• Symbol: {alert_data.get('primary_symbol', 'N/A')}\n"
            formatted_message += f"• Count: {alert_data.get('liquidation_count', 0)} liquidations\n"
            formatted_message += f"• Value: ${alert_data.get('total_value_usd', 0):,.0f}\n"
        
        elif alert_type == "single_liquidation":
            formatted_message += f"\n\n📊 *Details:*\n"
            formatted_message += f"• Symbol: {alert_data.get('symbol', 'N/A')}\n"
            formatted_message += f"• Side: {alert_data.get('side', 'N/A')}\n"
            formatted_message += f"• Value: ${alert_data.get('value_usd', 0):,.0f}\n"
        
        elif alert_type == "oi_explosion":
            formatted_message += f"\n\n📊 *Details:*\n"
            formatted_message += f"• Symbol: {alert_data.get('symbol', 'N/A')}\n"
            formatted_message += f"• Change: {alert_data.get('change_pct', 0):+.1f}%\n"
            formatted_message += f"• New OI: ${alert_data.get('new_oi', 0):,.0f}\n"
        
        return formatted_message
    
    async def test_connection(self) -> bool:
        """Test Telegram connection"""
        try:
            return await self.send_message("🤖 Crypto Assistant Alert System - Connection Test")
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False