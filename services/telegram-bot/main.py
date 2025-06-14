import asyncio
import os
import json
from typing import Dict, Any
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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
    
    async def get_combined_price(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/combined_price", json={
                'symbol': symbol,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching combined price: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_top_symbols(self, market_type: str = 'spot', limit: int = 10, exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/top_symbols", json={
                'market_type': market_type,
                'limit': limit,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching top symbols: {e}")
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
        
        # Set up bot commands for menu (one-time setup)
        try:
            commands = [
                BotCommand("start", "🚀 Start the bot and see help"),
                BotCommand("help", "📋 Show available commands"),
                BotCommand("price", "💰 Get spot + perp prices (e.g., /price BTC-USDT)"),
                BotCommand("top10", "🏆 Top 10 markets (/top10 spot or /top10 perps)"),
                BotCommand("balance", "💳 Show account balance"),
                BotCommand("positions", "📊 Show open positions"),
                BotCommand("pnl", "📈 Show P&L summary"),
            ]
            await context.bot.set_my_commands(commands)
            logger.info("Bot commands registered")
        except Exception as e:
            logger.warning(f"Could not set bot commands: {e}")
        
        welcome_text = """
🚀 **Crypto Trading Assistant**

💰 **Price Commands:**
• `/price <symbol>` - Get spot + perps price (e.g., /price BTC-USDT)
• `/top10 spot` - Top 10 spot markets by volume
• `/top10 perps` - Top 10 perpetual futures by volume

📊 **Portfolio Commands:**
• `/balance` - Show account balance
• `/positions` - Show open positions  
• `/pnl` - Show P&L summary

📋 **Other:**
• `/help` - Show this help message

**Examples:**
• `/price ETH-USDT` (shows both spot & perps)
• `/top10 spot`
• `/top10 perps`
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        await self.start(update, context)
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced price command showing both spot and perps"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/price BTC-USDT`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper().replace('/', '-')
        await update.message.reply_text(f"⏳ Fetching prices for {symbol}...")
        
        result = await self.market_client.get_combined_price(symbol)
        
        if result['success']:
            data = result['data']
            base_symbol = data['base_symbol']
            
            message = f"📊 **{base_symbol}**\n\n"
            
            # Spot data
            if 'spot' in data and data['spot']:
                spot = data['spot']
                change_24h = spot.get('change_24h', 0) or 0
                change_emoji = "🟢" if change_24h >= 0 else "🔴"
                change_sign = "+" if change_24h >= 0 else ""
                
                # Calculate USD volume
                volume_native = spot.get('volume_24h', 0) or 0
                volume_usd = volume_native * spot['price']
                base_token = base_symbol.split('/')[0]
                
                message += f"""🏪 **SPOT**
💰 Price: **${spot['price']:,.4f}**
{change_emoji} 24h: **{change_sign}{change_24h:.2f}%**
📊 Volume: **{volume_native:,.0f} {base_token}** (${volume_usd/1e6:.1f}M)

"""
            
            # Perp data
            if 'perp' in data and data['perp']:
                perp = data['perp']
                change_24h = perp.get('change_24h', 0) or 0
                change_emoji = "🟢" if change_24h >= 0 else "🔴"
                change_sign = "+" if change_24h >= 0 else ""
                
                # Calculate USD volume for perps
                volume_native = perp.get('volume_24h', 0) or 0
                volume_usd = volume_native * perp['price']
                base_token = base_symbol.split('/')[0]
                
                message += f"""⚡ **PERPETUALS**
💰 Price: **${perp['price']:,.4f}**
{change_emoji} 24h: **{change_sign}{change_24h:.2f}%**
📊 Volume: **{volume_native:,.0f} {base_token}** (${volume_usd/1e6:.1f}M)"""
                
                # Add OI and funding rate if available
                if perp.get('open_interest'):
                    message += f"\n📈 OI: **${perp['open_interest']:,.0f}**"
                
                if perp.get('funding_rate') is not None:
                    funding_rate = perp['funding_rate'] * 100  # Convert to percentage
                    funding_emoji = "🟢" if funding_rate >= 0 else "🔴"
                    funding_sign = "+" if funding_rate >= 0 else ""
                    message += f"\n💸 Funding: **{funding_sign}{funding_rate:.4f}%**"
                
                message += "\n"
            
            if 'spot' not in data and 'perp' not in data:
                message += "❌ No data available for this symbol"
            
            message += f"\n🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
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
    
    async def top10_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Top 10 symbols command handler"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please specify market type. Use: `/top10 spot` or `/top10 perps`", parse_mode='Markdown')
            return
        
        market_type = context.args[0].lower()
        if market_type not in ['spot', 'perps']:
            await update.message.reply_text("❌ Invalid market type. Use: `/top10 spot` or `/top10 perps`", parse_mode='Markdown')
            return
        
        # Convert 'perps' to 'perp' for the API
        api_market_type = 'perp' if market_type == 'perps' else market_type
        
        await update.message.reply_text(f"⏳ Fetching top 10 {market_type} markets...")
        
        result = await self.market_client.get_top_symbols(api_market_type, 10)
        
        if result['success']:
            data = result['data']
            symbols = data['symbols']
            market_display = market_type.upper()
            
            message = f"🏆 **TOP 10 {market_display} MARKETS**\n\n"
            
            for i, symbol in enumerate(symbols, 1):
                price = symbol['price']
                change_24h = symbol.get('change_24h', 0) or 0
                volume_24h = symbol.get('volume_24h', 0) or 0
                
                change_emoji = "🟢" if change_24h >= 0 else "🔴"
                change_sign = "+" if change_24h >= 0 else ""
                
                # Shorten symbol name for display and calculate USD volume
                display_symbol = symbol['symbol'].replace('/USDT', '').replace(':USDT', '').replace('-PERP', '')
                volume_usd = volume_24h * price
                
                message += f"""**{i}.** {display_symbol}
💰 ${price:,.4f} {change_emoji} {change_sign}{change_24h:.2f}%
📊 Vol: {volume_24h:,.0f} {display_symbol} (${volume_usd/1e6:.0f}M)

"""
            
            message += f"🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching top {market_type}: {result['error']}")
    
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
    application.add_handler(CommandHandler("top10", bot.top10_command))
    application.add_handler(CommandHandler("balance", bot.balance_command))
    application.add_handler(CommandHandler("positions", bot.positions_command))
    application.add_handler(CommandHandler("pnl", bot.pnl_command))
    
    # Add error handler
    application.add_error_handler(bot.error_handler)
    
    logger.info("Starting Telegram bot...")
    
    # Run the bot using the standard method (commands will be set after first start)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()