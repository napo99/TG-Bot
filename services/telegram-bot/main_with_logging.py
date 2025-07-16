"""
Enhanced Telegram Bot Main with Comprehensive Logging Integration
This demonstrates how to integrate the structured logging system
"""

import asyncio
import os
import json
import time
from typing import Dict, Any
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from aiohttp import ClientSession, ClientTimeout
from dotenv import load_dotenv

# Import new logging system
from ..shared.logging_config import setup_service_logging
from .bot_logger import bot_logger, TelegramBotLogger
from ..shared.structured_logger import APIRequestData, APIResponseData, TelegramInteractionData

from formatting_utils import (
    format_large_number, format_price, format_percentage, format_volume_with_usd,
    format_dollar_amount, format_dual_timezone_timestamp, get_change_emoji, format_delta_value,
    format_funding_rate, format_long_short_ratio, format_oi_change, format_enhanced_funding_rate,
    format_delta_with_emoji, format_market_intelligence
)

load_dotenv()

# Setup structured logging
logger = setup_service_logging('telegram-bot', 'main')
bot_logger = TelegramBotLogger()

class EnhancedMarketDataClient:
    """Enhanced MarketDataClient with comprehensive logging"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('MARKET_DATA_URL', 'http://localhost:8001')
        self.session = None
        self.logger = setup_service_logging('telegram-bot', 'market_client')
    
    async def _get_session(self):
        if self.session is None:
            timeout = ClientTimeout(total=30)
            self.session = ClientSession(timeout=timeout)
        return self.session
    
    async def get_price(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        """Get price data with comprehensive logging"""
        start_time = time.time()
        
        # Log request
        bot_logger.log_market_data_request('/price', symbol, exchange)
        
        session = await self._get_session()
        try:
            payload = {'symbol': symbol, 'exchange': exchange}
            
            with bot_logger.time_operation('market_data_price_fetch', {'symbol': symbol, 'exchange': exchange}):
                async with session.post(f"{self.base_url}/price", json=payload) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    response_data = await response.json()
                    response_size = len(json.dumps(response_data))
                    
                    # Log response
                    bot_logger.log_market_data_response(
                        '/price', 
                        response_time_ms, 
                        response.status == 200,
                        response_size
                    )
                    
                    # Log business event
                    bot_logger.log_business_event('price_data_retrieved', {
                        'symbol': symbol,
                        'exchange': exchange,
                        'response_time_ms': response_time_ms,
                        'data_size': response_size,
                        'price': response_data.get('spot', {}).get('price', 0) if response_data.get('success') else None
                    })
                    
                    return response_data
                    
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log error
            bot_logger.log_market_data_response('/price', response_time_ms, False, error=str(e))
            
            self.logger.error(f"Error fetching price for {symbol}: {e}", 
                            extra={'extra_data': {'symbol': symbol, 'exchange': exchange}})
            return {'success': False, 'error': str(e)}
    
    async def get_combined_price(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        """Get combined price data with logging"""
        start_time = time.time()
        
        bot_logger.log_market_data_request('/combined_price', symbol, exchange)
        
        session = await self._get_session()
        try:
            with bot_logger.time_operation('combined_price_fetch', {'symbol': symbol, 'exchange': exchange}):
                async with session.post(f"{self.base_url}/combined_price", json={
                    'symbol': symbol,
                    'exchange': exchange
                }) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    response_data = await response.json()
                    
                    bot_logger.log_market_data_response('/combined_price', response_time_ms, True)
                    
                    return response_data
                    
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            bot_logger.log_market_data_response('/combined_price', response_time_ms, False, error=str(e))
            
            self.logger.error(f"Error fetching combined price: {e}")
            return {'success': False, 'error': str(e)}

class EnhancedTelegramBot:
    """Enhanced Telegram Bot with comprehensive logging"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.authorized_users = set(os.getenv('AUTHORIZED_USERS', '').split(','))
        self.market_client = EnhancedMarketDataClient()
        self.logger = setup_service_logging('telegram-bot', 'bot')
        
        # Log bot initialization
        bot_logger.log_business_event('bot_initialization', {
            'authorized_users_count': len(self.authorized_users),
            'market_data_url': self.market_client.base_url
        })
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized with logging"""
        authorized = str(user_id) in self.authorized_users
        
        bot_logger.log_user_authorization_attempt(
            str(user_id),
            authorized=authorized,
            reason='in_whitelist' if authorized else 'not_in_whitelist'
        )
        
        return authorized
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command with comprehensive logging"""
        command_id = bot_logger.log_command_start(update, context, 'start')
        
        try:
            user = update.effective_user
            
            if not self.is_authorized(user.id):
                response_text = "❌ You are not authorized to use this bot."
                await update.message.reply_text(response_text)
                
                bot_logger.log_command_complete(command_id, update, response_text, False, "unauthorized")
                return
            
            response_text = """
🚀 **Crypto Assistant Bot**

Available commands:
/price <symbol> [exchange] - Get comprehensive price analysis
/balance [exchange] - Get account balance
/positions [exchange] - Get open positions
/pnl [exchange] - Get PnL summary
/top [market_type] [limit] [exchange] - Get top performing symbols

Examples:
• `/price BTC-USDT` - Bitcoin price analysis
• `/price ETH-USDT bybit` - Ethereum on Bybit
• `/balance binance` - Binance account balance
• `/top spot 5` - Top 5 spot gainers

📊 **Enhanced Features:**
✅ Real-time price data from multiple exchanges
✅ Volume analysis with spike detection  
✅ CVD (Cumulative Volume Delta) analysis
✅ Long/Short position ratios
✅ Technical indicators (RSI, VWAP, ATR)
✅ Open Interest tracking across 6 exchanges
✅ Market sentiment analysis

🔄 **Latest Updates:**
• Enhanced logging system with comprehensive monitoring
• Performance metrics tracking
• Real-time error detection and alerting
• User interaction analytics
"""
            
            await update.message.reply_text(response_text, parse_mode='Markdown')
            
            bot_logger.log_command_complete(command_id, update, response_text, True)
            
        except Exception as e:
            bot_logger.log_message_processing_error(update, e, 'start')
            bot_logger.log_command_complete(command_id, update, '', False, str(e))
            
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Price command with enhanced logging"""
        command_id = bot_logger.log_command_start(update, context, 'price')
        start_time = time.time()
        
        try:
            user = update.effective_user
            
            if not self.is_authorized(user.id):
                response_text = "❌ You are not authorized to use this bot."
                await update.message.reply_text(response_text)
                bot_logger.log_command_complete(command_id, update, response_text, False, "unauthorized")
                return
            
            # Parse command arguments
            args = context.args
            if not args:
                response_text = "❌ Please provide a symbol. Example: `/price BTC-USDT`"
                await update.message.reply_text(response_text, parse_mode='Markdown')
                bot_logger.log_command_complete(command_id, update, response_text, False, "missing_symbol")
                return
            
            symbol = args[0].upper()
            exchange = args[1] if len(args) > 1 else None
            
            # Log command parameters
            bot_logger.log_business_event('price_command_executed', {
                'symbol': symbol,
                'exchange': exchange,
                'user_id': str(user.id),
                'username': user.username
            })
            
            # Send "typing" indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            # Fetch data from market service
            with bot_logger.time_operation('price_command_processing', {'symbol': symbol, 'exchange': exchange}):
                price_data = await self.market_client.get_combined_price(symbol, exchange)
            
            if not price_data.get('success', False):
                error_msg = price_data.get('error', 'Unknown error')
                response_text = f"❌ Error fetching price data: {error_msg}"
                await update.message.reply_text(response_text)
                
                bot_logger.log_command_complete(command_id, update, response_text, False, error_msg)
                return
            
            # Format response
            formatted_response = self._format_price_response(price_data)
            
            # Log formatting operation
            input_size = len(json.dumps(price_data))
            output_size = len(formatted_response)
            formatting_time = (time.time() - start_time) * 1000
            
            bot_logger.log_formatting_operation(
                'price_response_formatting',
                input_size,
                output_size,
                formatting_time
            )
            
            # Send response
            await update.message.reply_text(formatted_response, parse_mode='Markdown')
            
            # Log successful completion
            total_response_time = (time.time() - start_time) * 1000
            bot_logger.log_command_complete(command_id, update, formatted_response[:100] + "...", True)
            
            # Log performance metrics
            bot_logger.log_performance_metric({
                'metric_name': 'price_command_total_time',
                'value': total_response_time,
                'unit': 'milliseconds',
                'tags': {
                    'symbol': symbol,
                    'exchange': exchange or 'default',
                    'user_id': str(user.id)
                },
                'timestamp': time.time(),
                'memory_usage_mb': 0,  # Will be auto-populated
                'cpu_percent': 0      # Will be auto-populated
            })
            
        except Exception as e:
            bot_logger.log_message_processing_error(update, e, 'price')
            bot_logger.log_command_complete(command_id, update, '', False, str(e))
            
            await update.message.reply_text("❌ An error occurred while fetching price data. Please try again.")
    
    def _format_price_response(self, price_data: Dict[str, Any]) -> str:
        """Format price response (simplified version)"""
        try:
            # This would use the existing formatting_utils functions
            # For demonstration, returning a simplified format
            symbol = price_data.get('symbol', 'Unknown')
            spot_data = price_data.get('spot', {})
            perp_data = price_data.get('perpetual', {})
            
            response = f"📊 **{symbol}**\\n\\n"
            
            if spot_data:
                price = spot_data.get('price', 0)
                change_24h = spot_data.get('change_24h', 0)
                response += f"🏪 **SPOT**\\n"
                response += f"💰 Price: ${price:.4f} | {change_24h:+.2f}%\\n\\n"
            
            if perp_data:
                price = perp_data.get('price', 0)
                funding_rate = perp_data.get('funding_rate', 0)
                response += f"⚡ **PERPETUALS**\\n"
                response += f"💰 Price: ${price:.4f}\\n"
                response += f"💸 Funding: {funding_rate:.4f}%\\n"
            
            response += f"\\n🕐 {datetime.now().strftime('%H:%M:%S')} UTC"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error formatting price response: {e}")
            return "❌ Error formatting response data"
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler with logging"""
        error = context.error
        
        if isinstance(update, Update):
            bot_logger.log_message_processing_error(update, error)
        else:
            self.logger.error(f"Unhandled error: {error}", exc_info=error)
        
        # Send user-friendly error message
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An unexpected error occurred. The development team has been notified."
            )
    
    def setup_application(self) -> Application:
        """Setup telegram application with handlers"""
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("price", self.price_command))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        bot_logger.log_business_event('application_setup_complete', {
            'handlers_count': len(application.handlers[0]),
            'error_handlers_count': len(application.error_handlers)
        })
        
        return application
    
    async def run(self):
        """Run the telegram bot"""
        bot_logger.log_business_event('bot_startup', {
            'mode': 'polling',
            'authorized_users': len(self.authorized_users)
        })
        
        application = self.setup_application()
        
        try:
            # Start polling
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            bot_logger.log_business_event('bot_started_successfully', {
                'polling_active': True
            })
            
            # Keep running
            await application.updater.idle()
            
        except Exception as e:
            bot_logger.log_error(e, {
                'error_type': 'BotStartupError',
                'error_message': str(e),
                'stack_trace': '',
                'context': {'operation': 'bot_startup'},
                'severity': 'CRITICAL'
            })
            raise
        finally:
            await application.stop()
            await application.shutdown()
            
            bot_logger.log_business_event('bot_shutdown', {
                'reason': 'normal_shutdown'
            })

async def main():
    """Main function with logging setup"""
    # Initialize logging
    logger.info("Starting Telegram Bot with enhanced logging")
    
    try:
        bot = EnhancedTelegramBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=e)
        raise

if __name__ == "__main__":
    asyncio.run(main())