import asyncio
import os
import json
from typing import Dict, Any
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from aiohttp import ClientSession, ClientTimeout
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class MarketDataClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('MARKET_DATA_URL', 'http://localhost:8001')
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            timeout = ClientTimeout(total=30)
            self.session = ClientSession(timeout=timeout)
        return self.session
    
    async def get_price(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/price", json={
                'symbol': symbol,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_balance(self, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/balance", json={
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_positions(self, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/positions", json={
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_pnl(self, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/pnl", json={
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching PNL: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        if self.session:
            await self.session.close()

class TelegramBot:
    def __init__(self):
        self.market_client = MarketDataClient()
        self.authorized_users = set()
        
        # Load authorized users from env (comma-separated chat IDs)
        auth_users = os.getenv('TELEGRAM_CHAT_ID', '')
        if auth_users:
            self.authorized_users.update(auth_users.split(','))
    
    def _is_authorized(self, user_id: str) -> bool:
        return str(user_id) in self.authorized_users or len(self.authorized_users) == 0
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(str(user_id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        welcome_text = """
🚀 **Crypto Trading Assistant**

Available commands:
• `/price <symbol>` - Get current price (e.g., /price BTC/USDT)
• `/balance` - Show account balance
• `/positions` - Show open positions
• `/pnl` - Show P&L summary
• `/help` - Show this help message

Examples:
• `/price BTC/USDT`
• `/price ETH-PERP`
• `/balance`
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        await self.start(update, context)
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Price command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/price BTC/USDT`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Fetching price for {symbol}...")
        
        result = await self.market_client.get_price(symbol)
        
        if result['success']:
            data = result['data']
            price = data['price']
            change_24h = data.get('change_24h', 0)
            volume_24h = data.get('volume_24h', 0)
            
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""
            
            message = f"""
📈 **{symbol}**

💰 Price: **${price:,.4f}**
{change_emoji} 24h Change: **{change_sign}{change_24h:.2f}%**
📊 24h Volume: **{volume_24h:,.2f}**

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching price: {result['error']}")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Balance command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        await update.message.reply_text("⏳ Fetching account balance...")
        
        result = await self.market_client.get_balance()
        
        if result['success']:
            balances = result['data']
            
            if not balances:
                await update.message.reply_text("💰 No balances found or all balances are zero")
                return
            
            message = "💰 **Account Balance**\n\n"
            
            for asset, amount in balances.items():
                if amount > 0.001:  # Filter very small amounts
                    message += f"• **{asset}**: {amount:,.4f}\n"
            
            message += f"\n🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching balance: {result['error']}")
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Positions command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        await update.message.reply_text("⏳ Fetching open positions...")
        
        result = await self.market_client.get_positions()
        
        if result['success']:
            positions = result['data']
            
            if not positions:
                await update.message.reply_text("📊 No open positions found")
                return
            
            message = "📊 **Open Positions**\n\n"
            
            for pos in positions:
                side_emoji = "🟢" if pos['side'] == 'long' else "🔴"
                pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                pnl_sign = "+" if pos['unrealized_pnl'] >= 0 else ""
                
                message += f"""
{side_emoji} **{pos['symbol']}** ({pos['side'].upper()})
📊 Size: {pos['size']:,.4f}
💰 Entry: ${pos['entry_price']:,.4f}
📈 Mark: ${pos['mark_price']:,.4f}
{pnl_emoji} PNL: {pnl_sign}${pos['unrealized_pnl']:,.2f} ({pnl_sign}{pos['percentage']:.2f}%)
"""
            
            message += f"\n🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching positions: {result['error']}")
    
    async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """PNL command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        await update.message.reply_text("⏳ Calculating P&L summary...")
        
        result = await self.market_client.get_pnl()
        
        if result['success']:
            data = result['data']
            total_pnl = data['total_unrealized_pnl']
            avg_percentage = data['average_percentage']
            position_count = data['position_count']
            
            pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
            pnl_sign = "+" if total_pnl >= 0 else ""
            
            message = f"""
📊 **P&L Summary**

{pnl_emoji} **Total Unrealized PNL**: {pnl_sign}${total_pnl:,.2f}
📈 **Average %**: {pnl_sign}{avg_percentage:.2f}%
📊 **Open Positions**: {position_count}

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching P&L: {result['error']}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Error handler"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.message:
            await update.message.reply_text("❌ An error occurred. Please try again later.")

def main():
    """Main function to run the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create bot instance
    bot = TelegramBot()
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("price", bot.price_command))
    application.add_handler(CommandHandler("balance", bot.balance_command))
    application.add_handler(CommandHandler("positions", bot.positions_command))
    application.add_handler(CommandHandler("pnl", bot.pnl_command))
    
    # Add error handler
    application.add_error_handler(bot.error_handler)
    
    logger.info("Starting Telegram bot...")
    
    # Run the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()