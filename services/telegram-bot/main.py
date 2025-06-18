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
    
    async def get_volume_spike(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/volume_spike", json={
                'symbol': symbol,
                'timeframe': timeframe,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching volume spike: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_cvd(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/cvd", json={
                'symbol': symbol,
                'timeframe': timeframe,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching CVD: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_volume_scan(self, timeframe: str = '15m', min_spike: float = 200) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/volume_scan", json={
                'timeframe': timeframe,
                'min_spike': min_spike
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching volume scan: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_comprehensive_analysis(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/comprehensive_analysis", json={
                'symbol': symbol,
                'timeframe': timeframe,
                'exchange': exchange
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching comprehensive analysis: {e}")
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
        
        # Commands are now registered automatically on bot startup
        
        welcome_text = """
🚀 **Crypto Trading Assistant**

🎯 **Comprehensive Analysis:**
• `/analysis <symbol> [timeframe]` - Complete market snapshot (e.g., /analysis BTC-USDT 15m)

💰 **Price Commands:**
• `/price <symbol>` - Get spot + perps price (e.g., /price BTC-USDT)
• `/top10 spot` - Top 10 spot markets by market cap
• `/top10 perps` - Top 10 perpetual futures by market cap

📊 **Volume Intelligence:**
• `/volume <symbol> [timeframe]` - Volume spike analysis (e.g., /volume BTC-USDT 15m)
• `/cvd <symbol> [timeframe]` - Cumulative Volume Delta (e.g., /cvd ETH-USDT 1h)
• `/volscan [threshold] [timeframe]` - Scan all symbols for volume spikes (e.g., /volscan 200 15m)

💼 **Portfolio Commands:**
• `/balance` - Show account balance
• `/positions` - Show open positions  
• `/pnl` - Show P&L summary

📋 **Other:**
• `/help` - Show this help message

**Examples:**
• `/analysis BTC-USDT 15m` (complete market analysis)
• `/price ETH-USDT` (shows both spot & perps)
• `/volume BTC-USDT 15m` (volume spike detection)
• `/cvd ETH-USDT 1h` (buy/sell pressure analysis)
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
                    oi_usd = perp['open_interest'] * perp['price']
                    message += f"\n📈 OI: **{perp['open_interest']:,.0f} {base_token}** (${oi_usd/1e6:.0f}M)"
                
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
                
                # Shorten symbol name for display and calculate values
                display_symbol = symbol['symbol'].replace('/USDT', '').replace(':USDT', '').replace('-PERP', '')
                volume_usd = volume_24h * price
                
                # Use real market cap if available, otherwise show "N/A"
                market_cap = symbol.get('market_cap')
                if market_cap and market_cap > 0:
                    if market_cap >= 1e9:  # Billions
                        market_cap_display = f"${market_cap/1e9:.1f}B"
                    else:  # Millions
                        market_cap_display = f"${market_cap/1e6:.0f}M"
                else:
                    market_cap_display = "N/A"
                
                message += f"""**{i}.** {display_symbol}
📈 MCap: {market_cap_display} {change_emoji} {change_sign}{change_24h:.2f}%
💰 Price: ${price:,.4f}
📊 Vol: {volume_24h:,.0f} {display_symbol} (${volume_usd/1e6:.0f}M)"""
                
                # Add OI and funding rate for perpetuals
                if symbol.get('market_type') == 'perp':
                    if symbol.get('open_interest'):
                        oi_usd = symbol['open_interest'] * price
                        message += f"\n📈 OI: {symbol['open_interest']:,.0f} {display_symbol} (${oi_usd/1e6:.0f}M)"
                    
                    if symbol.get('funding_rate') is not None:
                        funding_rate = symbol['funding_rate'] * 100  # Convert to percentage
                        funding_emoji = "🟢" if funding_rate >= 0 else "🔴"
                        funding_sign = "+" if funding_rate >= 0 else ""
                        message += f"\n💸 Funding: {funding_emoji} {funding_sign}{funding_rate:.4f}%"
                
                message += "\n\n"
            
            message += f"🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error fetching top {market_type}: {result['error']}")
    
    async def volume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Volume spike analysis command"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/volume BTC-USDT 15m`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper().replace('/', '-').replace('-', '/')
        timeframe = context.args[1] if len(context.args) > 1 else '15m'
        
        await update.message.reply_text(f"⏳ Analyzing volume for {symbol} ({timeframe})...")
        
        result = await self.market_client.get_volume_spike(symbol, timeframe)
        
        if result['success']:
            data = result['data']
            
            # Get spike level emoji
            spike_level = data['spike_level']
            if spike_level == 'EXTREME':
                level_emoji = "🔥🔥🔥"
            elif spike_level == 'HIGH':
                level_emoji = "🔥🔥"
            elif spike_level == 'MODERATE':
                level_emoji = "🔥"
            elif spike_level == 'LOW':
                level_emoji = "📈"
            else:
                level_emoji = "😴"
            
            # Format spike percentage
            spike_pct = data['spike_percentage']
            spike_sign = "+" if spike_pct >= 0 else ""
            
            # Format volumes
            current_vol = data['current_volume']
            avg_vol = data['average_volume']
            vol_usd = data['volume_usd']
            
            # Extract base token
            base_token = symbol.split('/')[0]
            
            message = f"""📊 **VOLUME ANALYSIS - {symbol}**

{level_emoji} **Spike Level**: {spike_level}
📈 **Volume Change**: {spike_sign}{spike_pct:.1f}%
⏰ **Timeframe**: {timeframe}

📊 **Current Volume**: {current_vol:,.0f} {base_token}
💰 **USD Value**: ${vol_usd/1e6:.1f}M
📊 **Average Volume**: {avg_vol:,.0f} {base_token}

🔍 **Analysis**: {'Significant volume activity detected!' if data['is_significant'] else 'Normal trading volume'}

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"""

            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error analyzing volume: {result['error']}")
    
    async def cvd_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """CVD (Cumulative Volume Delta) analysis command"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/cvd BTC-USDT 1h`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper().replace('/', '-').replace('-', '/')
        timeframe = context.args[1] if len(context.args) > 1 else '1h'
        
        await update.message.reply_text(f"⏳ Calculating CVD for {symbol} ({timeframe})...")
        
        result = await self.market_client.get_cvd(symbol, timeframe)
        
        if result['success']:
            data = result['data']
            
            # Get trend emojis
            cvd_trend = data['cvd_trend']
            if cvd_trend == 'BULLISH':
                trend_emoji = "🟢📈"
            elif cvd_trend == 'BEARISH':
                trend_emoji = "🔴📉"
            else:
                trend_emoji = "⚪➡️"
            
            # Format CVD values
            current_cvd = data['current_cvd']
            cvd_change = data['cvd_change_24h']
            change_sign = "+" if cvd_change >= 0 else ""
            
            # Divergence detection
            divergence = data['divergence_detected']
            divergence_text = "⚠️ **DIVERGENCE DETECTED**" if divergence else "✅ No divergence"
            
            message = f"""📈 **CVD ANALYSIS - {symbol}**

{trend_emoji} **CVD Trend**: {cvd_trend}
💹 **Current CVD**: {current_cvd:,.0f}
📊 **24h Change**: {change_sign}{cvd_change:,.0f}
⏰ **Timeframe**: {timeframe}

🔍 **Price vs CVD**: {divergence_text}
📊 **Price Trend**: {data['price_trend']}

💡 **What is CVD?**
Green candles = Buying pressure (+volume)
Red candles = Selling pressure (-volume)
CVD shows cumulative market sentiment

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"""

            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error calculating CVD: {result['error']}")
    
    async def volscan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Volume spike scanning command"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        # Parse arguments
        threshold = float(context.args[0]) if context.args else 200
        timeframe = context.args[1] if len(context.args) > 1 else '15m'
        
        await update.message.reply_text(f"🔍 Scanning for volume spikes >{threshold}% ({timeframe})...")
        
        result = await self.market_client.get_volume_scan(timeframe, threshold)
        
        if result['success']:
            data = result['data']
            spikes = data['spikes']
            
            if not spikes:
                await update.message.reply_text(f"😴 No volume spikes >{threshold}% found in {timeframe} timeframe")
                return
            
            message = f"🔍 **VOLUME SPIKES DETECTED**\n\n"
            message += f"📊 **Threshold**: >{threshold}%\n"
            message += f"⏰ **Timeframe**: {timeframe}\n"
            message += f"🎯 **Found**: {len(spikes)} spike(s)\n\n"
            
            for i, spike in enumerate(spikes[:5], 1):  # Limit to top 5
                symbol = spike['symbol']
                spike_pct = spike['spike_percentage']
                level = spike['spike_level']
                vol_usd = spike['volume_usd']
                
                # Level emoji
                if level == 'EXTREME':
                    emoji = "🔥🔥🔥"
                elif level == 'HIGH':
                    emoji = "🔥🔥"
                elif level == 'MODERATE':
                    emoji = "🔥"
                else:
                    emoji = "📈"
                
                base_token = symbol.split('/')[0]
                
                message += f"**{i}.** {base_token} {emoji}\n"
                message += f"📈 Spike: +{spike_pct:.0f}%\n"
                message += f"💰 Volume: ${vol_usd/1e6:.1f}M\n\n"
            
            if len(spikes) > 5:
                message += f"... and {len(spikes) - 5} more spikes\n"
            
            message += f"🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error scanning volumes: {result['error']}")
    
    async def analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive market analysis command"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/analysis BTC-USDT 15m`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper().replace('/', '-').replace('-', '/')
        timeframe = context.args[1] if len(context.args) > 1 else '15m'
        
        await update.message.reply_text(f"🎯 Running comprehensive analysis for {symbol} ({timeframe})...")
        
        result = await self.market_client.get_comprehensive_analysis(symbol, timeframe)
        
        if result['success']:
            data = result['data']
            
            # Extract data components
            price_data = data.get('price_data', {})
            volume_data = data.get('volume_analysis', {})
            cvd_data = data.get('cvd_analysis', {})
            tech_data = data.get('technical_indicators', {})
            sentiment = data.get('market_sentiment', {})
            oi_data = data.get('oi_data', {})
            long_short_data = data.get('long_short_data', {})
            
            # Format price and change
            current_price = price_data.get('current_price', 0)
            change_24h = price_data.get('change_24h', 0)
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""
            
            # Format volume spike
            spike_level = volume_data.get('spike_level', 'NORMAL')
            spike_pct = volume_data.get('spike_percentage', 0)
            vol_usd = volume_data.get('volume_usd', 0)
            rel_volume = volume_data.get('relative_volume', 1)
            
            # Volume spike emoji
            if spike_level == 'EXTREME':
                vol_emoji = "🔥🔥🔥"
            elif spike_level == 'HIGH':
                vol_emoji = "🔥🔥"
            elif spike_level == 'MODERATE':
                vol_emoji = "🔥"
            else:
                vol_emoji = "😴"
            
            # CVD trend
            cvd_trend = cvd_data.get('cvd_trend', 'NEUTRAL')
            cvd_current = cvd_data.get('current_cvd', 0)
            cvd_change = cvd_data.get('cvd_change_24h', 0)
            current_delta = cvd_data.get('current_delta', 0)
            current_delta_usd = cvd_data.get('current_delta_usd', 0)
            divergence = cvd_data.get('divergence_detected', False)
            
            cvd_emoji = "🟢📈" if cvd_trend == 'BULLISH' else "🔴📉" if cvd_trend == 'BEARISH' else "⚪➡️"
            cvd_sign = "+" if cvd_change >= 0 else ""
            delta_sign = "+" if current_delta >= 0 else ""
            
            # Technical indicators
            rsi = tech_data.get('rsi_14')
            vwap = tech_data.get('vwap')
            volatility = tech_data.get('volatility_24h')
            volatility_15m = tech_data.get('volatility_15m', 0)
            atr_usd = tech_data.get('atr_usd', 0)
            
            # Market sentiment
            control = sentiment.get('market_control', 'NEUTRAL')
            control_strength = sentiment.get('control_strength', 50)
            aggression = sentiment.get('aggression_level', 'LOW')
            
            # Control emoji
            if control == 'BULLS':
                control_emoji = "🟢🐂"
            elif control == 'BEARS':
                control_emoji = "🔴🐻"
            else:
                control_emoji = "⚪🦀"
            
            # Build message in new template format
            base_token = symbol.split('/')[0]
            current_volume_tokens = volume_data.get('current_volume', 0)
            
            # Start with main analysis
            message = f"""🎯 MARKET ANALYSIS - {symbol} ({timeframe})

• PRICE: ${current_price:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%
• VOLUME: {vol_emoji} {spike_level} {current_volume_tokens:,.0f} {base_token} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)
• CVD: {cvd_emoji} {cvd_trend} {cvd_change:,.0f} {base_token} (${cvd_change * current_price / 1e6:.1f}M)
• DELTA: {delta_sign}{current_delta:,.0f} {base_token} (${current_delta_usd/1e6:.2f}M)
"""

            # Add OI and Long/Short data for perps
            if oi_data and oi_data.get('open_interest'):
                oi_tokens = oi_data.get('open_interest', 0)
                oi_usd = oi_data.get('open_interest_usd', 0)
                funding = oi_data.get('funding_rate', 0) * 100
                funding_sign = "+" if funding >= 0 else ""
                funding_direction = "longs pay shorts" if funding >= 0 else "shorts pay longs"
                
                message += f"""• OI: {oi_tokens:,.0f} {base_token} (${oi_usd/1e6:.0f}M) 
• Funding: {funding_sign}{funding:.4f}% ({funding_direction})"""
                
                # Add institutional vs retail long/short data
                if long_short_data:
                    inst_data = long_short_data.get('institutional', {})
                    retail_data = long_short_data.get('retail', {})
                    
                    if inst_data and retail_data:
                        inst_longs = inst_data.get('net_longs_tokens', 0)
                        inst_shorts = inst_data.get('net_shorts_tokens', 0)
                        inst_longs_usd = inst_data.get('net_longs_usd', 0)
                        inst_shorts_usd = inst_data.get('net_shorts_usd', 0)
                        inst_ratio = inst_data.get('long_ratio', 1)
                        
                        ret_longs = retail_data.get('net_longs_tokens', 0)
                        ret_shorts = retail_data.get('net_shorts_tokens', 0)
                        ret_longs_usd = retail_data.get('net_longs_usd', 0)
                        ret_shorts_usd = retail_data.get('net_shorts_usd', 0)
                        ret_ratio = retail_data.get('long_ratio', 1)
                        
                        message += f"""
• Smart Money: 
    L: {inst_longs:,.0f} {base_token} (${inst_longs_usd/1e6:.0f}M) | S: {inst_shorts:,.0f} {base_token} (${inst_shorts_usd/1e6:.0f}M) 
    Ratio: {inst_ratio:.2f}
• All Participants: 
    L: {ret_longs:,.0f} {base_token} (${ret_longs_usd/1e6:.0f}M) | S: {ret_shorts:,.0f} {base_token} (${ret_shorts_usd/1e6:.0f}M)
    Ratio: {ret_ratio:.2f}"""

            # Add technical section
            message += f"""

📉 TECHNICAL:"""
            
            if rsi:
                rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                message += f"\n• RSI: {rsi:.0f} ({rsi_status})"
            
            if vwap and current_price:
                vwap_status = "Above VWAP ✅" if current_price > vwap else "Below VWAP ❌"
                message += f"\n• VWAP: ${vwap:,.2f} ({vwap_status})"
            
            # Add new volatility and ATR line
            if volatility_15m and atr_usd:
                message += f"\n• Volatility: {volatility_15m:.1f}% | ATR: ${atr_usd:,.0f}"
            
            rel_volume_pct = int(rel_volume * 100)
            message += f"\n• Rel Volume: {rel_volume:.1f}x ({rel_volume_pct}% of normal)"

            # Enhanced market control section
            message += f"""
   

🎯 MARKET CONTROL:"""
            
            # Basic control info
            message += f"\n• {control} IN CONTROL ({control_strength:.0f}% confidence)"
            message += f"\n• Aggression: {aggression}"
            
            # Add detailed smart money analysis if available
            if long_short_data:
                inst_data = long_short_data.get('institutional', {})
                retail_data = long_short_data.get('retail', {})
                smart_money_edge = long_short_data.get('smart_money_edge', 0)
                
                if inst_data and retail_data:
                    inst_long_pct = inst_data.get('long_pct', 50)
                    inst_short_pct = inst_data.get('short_pct', 50)
                    ret_long_pct = retail_data.get('long_pct', 50)
                    ret_short_pct = retail_data.get('short_pct', 50)
                    inst_ratio = inst_data.get('long_ratio', 1)
                    ret_ratio = retail_data.get('long_ratio', 1)
                    
                    message += f"\n• SMART MONEY: {inst_long_pct:.1f}% Long (vs {inst_short_pct:.1f}% Short) | Ratio: {inst_ratio:.2f}"
                    message += f"\n• MARKET AVERAGE: {ret_long_pct:.1f}% Long (vs {ret_short_pct:.1f}% Short) | Ratio: {ret_ratio:.2f}"
                    
                    edge_sign = "+" if smart_money_edge >= 0 else ""
                    edge_direction = "more bullish" if smart_money_edge > 0 else "more bearish" if smart_money_edge < 0 else "neutral vs"
                    message += f"\n• EDGE: Smart money {edge_sign}{smart_money_edge:.1f}% {edge_direction} than market"

            # Add dual timezone timestamp
            import pytz
            utc_time = datetime.now(pytz.UTC)
            sgt_time = utc_time.astimezone(pytz.timezone('Asia/Singapore'))
            
            message += f"\n\n🕐 {utc_time.strftime('%H:%M:%S')} UTC / {sgt_time.strftime('%H:%M:%S')} SGT"

            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error running analysis: {result['error']}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Error handler"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.message:
            await update.message.reply_text("❌ An error occurred. Please try again later.")

async def setup_bot_commands(application):
    """Setup bot commands on startup"""
    try:
        commands = [
            BotCommand("start", "🚀 Start the bot and see help"),
            BotCommand("help", "📋 Show available commands"),
            BotCommand("price", "💰 Get spot + perp prices (e.g., /price BTC-USDT)"),
            BotCommand("top10", "🏆 Top 10 markets (/top10 spot or /top10 perps)"),
            BotCommand("analysis", "🎯 Complete market analysis (/analysis BTC-USDT 15m)"),
            BotCommand("volume", "📊 Volume spike analysis (/volume BTC-USDT 15m)"),
            BotCommand("cvd", "📈 Cumulative Volume Delta (/cvd BTC-USDT 1h)"),
            BotCommand("volscan", "🔍 Scan volume spikes (/volscan 200 15m)"),
            BotCommand("balance", "💳 Show account balance"),
            BotCommand("positions", "📊 Show open positions"),
            BotCommand("pnl", "📈 Show P&L summary"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands registered successfully")
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

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
    application.add_handler(CommandHandler("analysis", bot.analysis_command))
    application.add_handler(CommandHandler("volume", bot.volume_command))
    application.add_handler(CommandHandler("cvd", bot.cvd_command))
    application.add_handler(CommandHandler("volscan", bot.volscan_command))
    application.add_handler(CommandHandler("balance", bot.balance_command))
    application.add_handler(CommandHandler("positions", bot.positions_command))
    application.add_handler(CommandHandler("pnl", bot.pnl_command))
    
    # Add error handler
    application.add_error_handler(bot.error_handler)
    
    # Setup bot commands on startup
    async def post_init(application):
        await setup_bot_commands(application)
    
    application.post_init = post_init
    
    logger.info("Starting Telegram bot...")
    
    # Run the bot using the standard method
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()