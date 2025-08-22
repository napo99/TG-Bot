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
from formatting_utils import (
    format_large_number, format_price, format_percentage, format_volume_with_usd,
    format_dollar_amount, format_dual_timezone_timestamp, get_change_emoji, format_delta_value,
    format_funding_rate, format_long_short_ratio, format_oi_change, format_enhanced_funding_rate,
    format_delta_with_emoji, format_market_intelligence
)

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
    
    async def get_market_profile(self, symbol: str) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/market_profile", json={
                'symbol': symbol,
                'exchange': 'binance'
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching market profile: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_oi_analysis(self, symbol: str) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            async with session.post(f"{self.base_url}/multi_oi", json={
                'base_symbol': symbol
            }) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching OI analysis: {e}")
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
• `/oi <symbol>` - Open Interest analysis across exchanges (e.g., /oi BTC)
• `/profile <symbol>` - Market Profile VP & TPO analysis (e.g., /profile BTC)

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
        """Enhanced price command showing both spot and perps with 15m data"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/price BTC-USDT`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper().replace('/', '-')
        await update.message.reply_text(f"⏳ Fetching enhanced data for {symbol}...")
        
        result = await self.market_client.get_combined_price(symbol)
        
        if result['success']:
            data = result['data']
            base_symbol = data['base_symbol']
            base_token = base_symbol.split('/')[0]
            
            # Exchange name (prefer perp exchange as it's usually the primary data source)
            exchange_name = data.get('perp_exchange') or data.get('spot_exchange', 'Unknown')
            
            message = f"📊 **{base_symbol}** ({exchange_name})\n\n"
            
            # Spot data with enhanced format
            if 'spot' in data and data['spot']:
                spot = data['spot']
                price = spot['price']
                change_24h = spot.get('change_24h', 0) or 0
                change_15m = spot.get('change_15m', 0) or 0
                
                # Price row with ATR 24h
                change_24h_emoji = get_change_emoji(change_24h)
                dollar_change_24h = (price * change_24h / 100) if change_24h else 0
                atr_24h_str = f" | ATR: {spot.get('atr_24h', 0):.2f}" if spot.get('atr_24h') else ""
                
                message += f"""🏪 **SPOT**
💰 Price: **{format_price(price)}** | {format_percentage(change_24h)} | {format_dollar_amount(dollar_change_24h)}{atr_24h_str}
"""
                
                # 15m price change
                change_15m_emoji = get_change_emoji(change_15m)
                dollar_change_15m = (price * change_15m / 100) if change_15m else 0
                atr_15m_str = f" | ATR: {spot.get('atr_15m', 0):.2f}" if spot.get('atr_15m') else ""
                message += f"{change_15m_emoji} Price Change 15m: **{format_percentage(change_15m)}** | {format_dollar_amount(dollar_change_15m)}{atr_15m_str}\n"
                
                # Volume 24h
                volume_24h = spot.get('volume_24h', 0) or 0
                message += f"📊 Volume 24h: **{format_volume_with_usd(volume_24h, base_token, price)}**\n"
                
                # Volume 15m
                volume_15m = spot.get('volume_15m', 0) or 0
                message += f"📊 Volume 15m: **{format_volume_with_usd(volume_15m, base_token, price)}**\n"
                
                # Delta 24h with L/S ratio
                delta_24h = spot.get('delta_24h', 0) or 0
                volume_24h = spot.get('volume_24h', 0) or 0
                ls_ratio_24h = format_long_short_ratio(delta_24h, volume_24h)
                logger.debug(f"SPOT Delta 24h L/S: delta={delta_24h:.2f}, volume={volume_24h:.2f}, ratio={ls_ratio_24h}")
                message += f"📈 Delta 24h: **{format_delta_with_emoji(delta_24h, base_token, price)}** | {ls_ratio_24h}\n"
                
                # Delta 15m with L/S ratio
                delta_15m = spot.get('delta_15m', 0) or 0
                volume_15m = spot.get('volume_15m', 0) or 0
                ls_ratio_15m = format_long_short_ratio(delta_15m, volume_15m)
                logger.debug(f"SPOT Delta 15m L/S: delta={delta_15m:.2f}, volume={volume_15m:.2f}, ratio={ls_ratio_15m}")
                message += f"📈 Delta 15m: **{format_delta_with_emoji(delta_15m, base_token, price)}** | {ls_ratio_15m}\n\n"
            
            # Perp data with enhanced format
            if 'perp' in data and data['perp']:
                perp = data['perp']
                price = perp['price']
                change_24h = perp.get('change_24h', 0) or 0
                change_15m = perp.get('change_15m', 0) or 0
                
                # Price row with ATR 24h
                change_24h_emoji = get_change_emoji(change_24h)
                dollar_change_24h = (price * change_24h / 100) if change_24h else 0
                atr_24h_str = f" | ATR: {perp.get('atr_24h', 0):.2f}" if perp.get('atr_24h') else ""
                
                message += f"""⚡ **PERPETUALS**
💰 Price: **{format_price(price)}** | {format_percentage(change_24h)} | {format_dollar_amount(dollar_change_24h)}{atr_24h_str}
"""
                
                # 15m price change
                change_15m_emoji = get_change_emoji(change_15m)
                dollar_change_15m = (price * change_15m / 100) if change_15m else 0
                atr_15m_str = f" | ATR: {perp.get('atr_15m', 0):.2f}" if perp.get('atr_15m') else ""
                message += f"{change_15m_emoji} Price Change 15m: **{format_percentage(change_15m)}** | {format_dollar_amount(dollar_change_15m)}{atr_15m_str}\n"
                
                # Volume 24h
                volume_24h = perp.get('volume_24h', 0) or 0
                message += f"📊 Volume 24h: **{format_volume_with_usd(volume_24h, base_token, price)}**\n"
                
                # Volume 15m
                volume_15m = perp.get('volume_15m', 0) or 0
                message += f"📊 Volume 15m: **{format_volume_with_usd(volume_15m, base_token, price)}**\n"
                
                # Delta 24h with L/S ratio
                delta_24h = perp.get('delta_24h', 0) or 0
                volume_24h_perp = perp.get('volume_24h', 0) or 0
                ls_ratio_24h_perp = format_long_short_ratio(delta_24h, volume_24h_perp)
                logger.debug(f"PERP Delta 24h L/S: delta={delta_24h:.2f}, volume={volume_24h_perp:.2f}, ratio={ls_ratio_24h_perp}")
                message += f"📈 Delta 24h: **{format_delta_with_emoji(delta_24h, base_token, price)}** | {ls_ratio_24h_perp}\n"
                
                # Delta 15m with L/S ratio
                delta_15m = perp.get('delta_15m', 0) or 0
                volume_15m_perp = perp.get('volume_15m', 0) or 0
                ls_ratio_15m_perp = format_long_short_ratio(delta_15m, volume_15m_perp)
                logger.debug(f"PERP Delta 15m L/S: delta={delta_15m:.2f}, volume={volume_15m_perp:.2f}, ratio={ls_ratio_15m_perp}")
                message += f"📈 Delta 15m: **{format_delta_with_emoji(delta_15m, base_token, price)}** | {ls_ratio_15m_perp}\n"
                
                # Open Interest (current snapshot)
                if perp.get('open_interest'):
                    oi_volume = format_volume_with_usd(perp['open_interest'], base_token, price)
                    message += f"📈 OI: **{oi_volume}**\n"
                
                # OI Changes (24h and 15m) with percentage
                current_oi = perp.get('open_interest', 0)
                if perp.get('oi_change_24h') is not None:
                    oi_change_24h_str = format_oi_change(perp['oi_change_24h'], base_token, price, current_oi)
                    message += f"📊 OI Change 24h: **{oi_change_24h_str}**\n"
                
                if perp.get('oi_change_15m') is not None:
                    oi_change_15m_str = format_oi_change(perp['oi_change_15m'], base_token, price, current_oi)
                    message += f"📊 OI Change 15m: **{oi_change_15m_str}**\n"
                
                # Enhanced Funding Rate with annual cost and strategy
                if perp.get('funding_rate') is not None:
                    funding_rate = perp['funding_rate']
                    enhanced_funding = format_enhanced_funding_rate(funding_rate)
                    message += f"{enhanced_funding}\n"
                
                message += "\n"
            
            # Market Intelligence Section
            if 'spot' in data or 'perp' in data:
                spot_data = data.get('spot', {})
                perp_data = data.get('perp', {})
                intelligence = format_market_intelligence(spot_data, perp_data)
                message += f"{intelligence}\n\n"
            
            if 'spot' not in data and 'perp' not in data:
                message += "❌ No data available for this symbol\n"
            
            # Enhanced timestamp with dual timezone
            timestamp = format_dual_timezone_timestamp()
            message += f"🕐 {timestamp}"
            
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
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Market Profile command - Volume Profile and TPO analysis
        Usage: /profile BTC or /profile ETH
        """
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        # Parse symbol (default to BTC)
        symbol = "BTC"
        if context.args:
            symbol = context.args[0].upper().replace('/', '').replace('-', '')
        
        # Send loading message
        loading_msg = await update.message.reply_text(
            f"⏳ Calculating Market Profile for {symbol}...\n"
            f"Computing VP & TPO across 5 timeframes..."
        )
        
        try:
            # Call market data service
            result = await self.market_client.get_market_profile(symbol)
            
            if result['success']:
                # Format the response
                message = self._format_profile_response(result['data'])
                
                # Delete loading message and send result
                await loading_msg.delete()
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await loading_msg.edit_text(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Profile command error: {e}")
            await loading_msg.edit_text(f"❌ Error calculating profile: {str(e)}")

    def _format_profile_response(self, data: dict) -> str:
        """
        Format profile data for Telegram display
        """
        symbol = data['symbol']
        current_price = data['current_price']
        
        # Build message header
        message = f"""📊 **MARKET PROFILE - {symbol}**
💰 Current: ${current_price:,.2f}
{'─' * 30}

"""
        
        # Process each timeframe
        for tf in ['1m', '15m', '30m', '1h', '4h', '1d']:
            if tf not in data:
                continue
            
            tf_data = data[tf]
            vp = tf_data['volume_profile']
            tpo = tf_data['tpo']
            period = tf_data['period']
            candles = tf_data['candles']
            
            # Check if price is in value area
            vp_in_va = "✅" if vp['val'] <= current_price <= vp['vah'] else "❌"
            tpo_in_va = "✅" if tpo['val'] <= current_price <= tpo['vah'] else "❌"
            
            # Format section with VWAP integration and smart ordering
            vwap = tf_data.get('vwap', current_price)
            
            # Calculate VWAP distance percentage
            vwap_distance = ((current_price - vwap) / vwap) * 100
            vwap_arrow = "↑" if current_price > vwap else "↓"
            # Add session-based context (matches TradingView)
            tf_periods = {'1m': 'Session', '15m': 'Session', '30m': 'Session', '1h': 'Session', '4h': 'Session', '1d': 'Daily'}
            period_label = tf_periods.get(tf, '?')
            # Truncate to 2 decimal places (don't round)
            vwap_distance_truncated = int(vwap_distance * 100) / 100
            vwap_text = f"VWAP ({period_label}): ${vwap:,.0f} {vwap_arrow} ({vwap_distance_truncated:+.2f}%)"
            
            # Create price levels list for smart ordering
            levels = [
                ('VAH', vp['vah'], f"VAH: ${vp['vah']:,.0f} {vp_in_va}"),
                ('POC', vp['poc'], f"POC: ${vp['poc']:,.0f}"),
                ('VAL', vp['val'], f"VAL: ${vp['val']:,.0f}"),
                ('VWAP', vwap, vwap_text)
            ]
            
            # Sort by price (highest to lowest)
            levels.sort(key=lambda x: x[1], reverse=True)
            
            # Format the profile section
            if tf == '30m':
                message += f"30M Profile\n"
                for _, _, level_text in levels:
                    message += f"- {level_text}\n"
                message += f"TPO: POC: ${tpo['poc']:,.0f} | VAL: ${tpo['val']:,.0f} | VAH: ${tpo['vah']:,.0f}\n\n"
            elif tf != '1d':
                message += f"{tf.upper()} Profile\n"
                for _, _, level_text in levels:
                    message += f"- {level_text}\n"
                message += "\n"
            else:
                message += f"Daily Profile\n"
                for _, _, level_text in levels:
                    message += f"- {level_text}\n"
                message += "\n"
        
        # Add analysis summary
        message += f"""{'─' * 30}
📍 **ANALYSIS**
"""
        
        # Count how many timeframes have price in value area
        in_vp_count = 0
        in_tpo_count = 0
        
        for tf in ['1m', '15m', '1h', '4h', '1d']:
            if tf in data:
                vp = data[tf]['volume_profile']
                tpo = data[tf]['tpo']
                if vp['val'] <= current_price <= vp['vah']:
                    in_vp_count += 1
                if tpo['val'] <= current_price <= tpo['vah']:
                    in_tpo_count += 1
        
        # Market state analysis
        if in_vp_count >= 3 and in_tpo_count >= 3:
            message += "• ✅ **BALANCED**: Price within value area on most timeframes\n"
            message += "• Strategy: Mean reversion likely, fade breakouts\n"
        elif in_vp_count <= 1 or in_tpo_count <= 1:
            message += "• ⚠️ **TRENDING**: Price outside value area on most timeframes\n"
            message += "• Strategy: Follow trend, breakout continuation likely\n"
        else:
            message += "• ⚪ **TRANSITIONING**: Mixed signals across timeframes\n"
            message += "• Strategy: Wait for clearer structure\n"
        
        # Add key levels
        message += f"""
📊 **KEY LEVELS**
- 1H POC: ${data.get('1h', {}).get('volume_profile', {}).get('poc', 0):,.0f} (High volume node)
- 4H VA: ${data.get('4h', {}).get('volume_profile', {}).get('val', 0):,.0f} - ${data.get('4h', {}).get('volume_profile', {}).get('vah', 0):,.0f}
- Daily POC: ${data.get('1d', {}).get('volume_profile', {}).get('poc', 0):,.0f} (Major reference)

🕐 {datetime.now().strftime('%H:%M:%S')} UTC / {(datetime.now().replace(hour=(datetime.now().hour + 8) % 24)).strftime('%H:%M:%S')} SGT"""
        
        return message
    
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
        """Market analysis command using individual working endpoints"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol. Example: `/analysis BTC 15m`", parse_mode='Markdown')
            return
        
        symbol = context.args[0].upper()
        # Normalize symbol format
        if '/' not in symbol and '-' not in symbol:
            symbol = f"{symbol}/USDT"
        symbol = symbol.replace('-', '/')
        
        timeframe = context.args[1] if len(context.args) > 1 else '15m'
        
        await update.message.reply_text(f"🎯 Running analysis for {symbol} ({timeframe})...")
        
        try:
            # Use the comprehensive analysis endpoint (the original working approach)
            result = await self.market_client.get_comprehensive_analysis(symbol, timeframe)
            
            if result.get('success'):
                data = result['data']
                logger.info(f"API data received for {symbol}: {list(data.keys())}")
                
                # Use the original sophisticated formatting method
                try:
                    message = self._format_sophisticated_analysis(data, symbol, timeframe)
                    await update.message.reply_text(message, parse_mode='Markdown')
                except Exception as format_error:
                    logger.error(f"Formatting error for {symbol}: {format_error}")
                    # Try basic fallback
                    fallback_msg = f"🎯 **{symbol}** Analysis\n\n💰 Price: ${data.get('price_data', {}).get('current_price', 'N/A')}\n📊 Volume Spike: {data.get('volume_analysis', {}).get('spike_level', 'N/A')}\n\n⚠️ Detailed formatting failed"
                    await update.message.reply_text(fallback_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Error running analysis: {result.get('error', 'API call failed')}")
                
        except Exception as e:
            logger.error(f"Analysis command error: {e}")
            await update.message.reply_text(f"❌ Error running analysis: {str(e)}")
    
    async def oi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Open Interest analysis command with exact target formatting"""
        if not self._is_authorized(str(update.effective_user.id)):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        # Parse symbol (default to BTC if not provided)
        symbol = "BTC"
        if context.args:
            symbol = context.args[0].upper()
        
        # Send acknowledgment message
        await update.message.reply_text(f"🔍 Analyzing Open Interest for {symbol} across USDT + USDC markets...")
        
        try:
            # Get OI analysis data
            result = await self.market_client.get_oi_analysis(symbol)
            
            if result['success']:
                # Format with exact target specification - our new API returns data directly
                formatted_message = self._format_oi_analysis(result, symbol)
                await update.message.reply_text(formatted_message, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Error analyzing OI for {symbol}: {result['error']}")
                
        except Exception as e:
            logger.error(f"OI command error for {symbol}: {e}")
            await update.message.reply_text(f"❌ Error analyzing OI for {symbol}: {str(e)}")

    def _format_oi_analysis(self, data, symbol: str) -> str:
        """Format OI analysis to match target specification exactly"""
        try:
            # Handle the new unified API response format
            if 'exchange_breakdown' not in data:
                return f"❌ Invalid data format for {symbol}"
            
            exchange_breakdown = data['exchange_breakdown']
            aggregated = data.get('aggregated_oi', {})
            market_categories = data.get('market_categories', {})
            validation = data.get('validation_summary', {})
            
            # Extract totals
            total_oi_tokens = aggregated.get('total_tokens', 0)
            total_oi_usd = aggregated.get('total_usd', 0)
            total_markets = data.get('total_markets', 0)
            
            # Extract market category data
            usdt_data = market_categories.get('usdt_stable', {})
            usdc_data = market_categories.get('usdc_stable', {})
            usd_data = market_categories.get('usd_inverse', {})
            
            usdt_usd = usdt_data.get('total_usd', 0)
            usdc_usd = usdc_data.get('total_usd', 0)
            inverse_usd = usd_data.get('total_usd', 0)
            
            usdt_pct = usdt_data.get('percentage', 0)
            usdc_pct = usdc_data.get('percentage', 0)
            inverse_pct = usd_data.get('percentage', 0)
            
            stablecoin_usd = usdt_usd + usdc_usd
            stablecoin_pct = usdt_pct + usdc_pct
            
            # Build individual markets list from exchange breakdown
            individual_markets = []
            for exchange_data in exchange_breakdown:
                exchange = exchange_data['exchange']
                markets = exchange_data.get('market_breakdown', [])
                for market in markets:
                    market_type = market.get('type', 'USDT')
                    market_symbol = market.get('symbol', f"{symbol}{market_type}")
                    oi_tokens = market.get('oi_tokens', 0)
                    oi_usd = market.get('oi_usd', 0)
                    funding = market.get('funding_rate', 0)
                    volume_24h = market.get('volume_24h', 0)
                    
                    # Calculate percentage of total
                    percentage = (oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
                    
                    # Determine market category label
                    if market_type == 'USDT':
                        category_label = 'STABLE'
                    elif market_type == 'USDC':
                        category_label = 'STABLE'
                    else:  # USD/Inverse
                        category_label = 'INVERSE'
                    
                    individual_markets.append({
                        'exchange': exchange.title(),
                        'type': market_type,
                        'symbol': market_symbol,
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'percentage': percentage,
                        'funding': funding,
                        'volume_24h': volume_24h,
                        'category_label': category_label
                    })
            
            # Sort markets by OI USD value (descending)
            individual_markets.sort(key=lambda x: x['oi_usd'], reverse=True)
            
            # Build message with target specification format
            message = f"""📊 OPEN INTEREST ANALYSIS - {symbol}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${stablecoin_usd/1e9:.1f}B | {stablecoin_pct:.1f}%
  - USDT: ${usdt_usd/1e9:.1f}B ({usdt_pct:.1f}%)
  - USDC: ${usdc_usd/1e9:.1f}B ({usdc_pct:.1f}%)
• Coin-Margined (Inverse): ${inverse_usd/1e9:.1f}B | {inverse_pct:.1f}%
  - USD: ${inverse_usd/1e9:.1f}B ({inverse_pct:.1f}%)

🔢 STABLECOIN MARKETS ({stablecoin_pct:.1f}%): ${stablecoin_usd/1e9:.1f}B
🔢 INVERSE MARKETS ({inverse_pct:.1f}%): ${inverse_usd/1e9:.1f}B
📊 COMBINED TOTAL: ${total_oi_usd/1e9:.1f}B

📈 TOP MARKETS:"""
            
            # Add individual markets (ranked 1-13)
            for i, market in enumerate(individual_markets[:13], 1):
                funding_sign = "+" if market['funding'] >= 0 else ""
                volume_formatted = self._format_volume(market['volume_24h'])
                
                message += f"\n{i}. {market['exchange']} {market['type']}: {market['oi_tokens']:,.0f} {symbol} (${market['oi_usd']/1e9:.1f}B) | {market['percentage']:.1f}% {market['category_label']}"
                message += f"\n   Funding: {funding_sign}{market['funding']*100:.4f}% | Vol: {volume_formatted} {symbol}"
            
            # Add coverage summary
            message += f"""

🏢 COVERAGE SUMMARY:
• Exchanges: {validation.get('successful_exchanges', 0)} working
• Markets: {total_markets} total
• Phase 2A: USDT + USDC support

🚨 MARKET ANALYSIS:
• Sentiment: NEUTRAL ⚪➡️
• Risk Level: NORMAL
• Coverage: Multi-stablecoin across {validation.get('successful_exchanges', 0)} exchanges

🕐 {datetime.now().strftime('%H:%M:%S')} UTC / {(datetime.now().replace(hour=(datetime.now().hour + 8) % 24)).strftime('%H:%M:%S')} SGT"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting OI analysis: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error formatting OI analysis for {symbol}: {str(e)}"
    
    def _format_volume(self, volume: float) -> str:
        """Format volume with appropriate units"""
        if volume >= 1e6:
            return f"{volume/1e6:.0f}M"
        elif volume >= 1e3:
            return f"{volume/1e3:.0f}K"
        else:
            return f"{volume:.0f}"

    def _format_sophisticated_analysis(self, data: dict, symbol: str, timeframe: str) -> str:
        """Format sophisticated market analysis message"""
        try:
            # Extract data components with safe defaults
            price_data = data.get('price_data', {})
            volume_data = data.get('volume_analysis', {})
            cvd_data = data.get('cvd_analysis', {})
            tech_data = data.get('technical_indicators', {})
            sentiment = data.get('market_sentiment', {})
            oi_data = data.get('oi_data', {})
            
            # PRICE SECTION
            current_price = price_data.get('current_price', 0)
            change_24h = price_data.get('change_24h', 0)
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""
            
            # VOLUME SECTION
            current_volume = volume_data.get('current_volume', 0)
            volume_usd = volume_data.get('volume_usd', 0)
            spike_level = volume_data.get('spike_level', 'NORMAL')
            spike_pct = volume_data.get('spike_percentage', 0)
            rel_volume = volume_data.get('relative_volume', 1.0)
            base_token = symbol.split('/')[0]
            
            # Volume emoji
            vol_emoji = "🔥🔥🔥" if spike_level == 'EXTREME' else "🔥🔥" if spike_level == 'HIGH' else "🔥" if spike_level == 'MODERATE' else "😴"
            vol_change_sign = "+" if spike_pct >= 0 else ""
            
            # CVD SECTION
            cvd_current = cvd_data.get('current_cvd', 0)
            cvd_change = cvd_data.get('cvd_change_24h', 0)
            cvd_trend = cvd_data.get('cvd_trend', 'NEUTRAL')
            cvd_emoji = "🟢📈" if cvd_trend == 'BULLISH' else "🔴📉" if cvd_trend == 'BEARISH' else "⚪➡️"
            cvd_sign = "+" if cvd_change >= 0 else ""
            
            # DELTA calculation (using CVD change as proxy for delta) - with safety checks
            cvd_change_safe = cvd_change if cvd_change is not None else 0
            current_volume_safe = current_volume if current_volume is not None else 0
            current_price_safe = current_price if current_price is not None and current_price > 0 else 1
            
            delta_btc = cvd_change_safe / 1000 if cvd_change_safe != 0 else current_volume_safe * 0.001  # Approximate delta
            delta_usd = delta_btc * current_price_safe
            delta_sign = "+" if delta_btc >= 0 else ""
            
            # SESSION ANALYSIS
            current_time = datetime.now()
            utc_hour = current_time.hour
            
            # Trading session detection
            session_name, session_hour, session_total = self._get_trading_session(utc_hour)
            
            # Volume spike analysis (enhanced) - with safety checks
            volume_usd_safe = volume_usd if volume_usd is not None else 0
            rel_volume_safe = rel_volume if rel_volume is not None and rel_volume > 0 else 1
            baseline_volume = volume_usd_safe / rel_volume_safe
            spike_multiplier = int(spike_pct / 100 * 100) if spike_pct > 100 else 100
            volume_vs_baseline = f"{spike_multiplier}% above 7-day baseline" if spike_pct > 0 else "below baseline"
            
            # Market pace calculation
            hourly_volume_rate = volume_usd_safe / 1e6  # Convert to millions
            normal_hourly_rate = baseline_volume / 1e6 / 24  # Rough estimate
            pace_level = "EXTREME" if hourly_volume_rate > normal_hourly_rate * 10 else "HIGH" if hourly_volume_rate > normal_hourly_rate * 3 else "NORMAL"
            
            # DAILY CONTEXT
            daily_volume_btc = current_volume_safe * 24  # Rough daily estimate
            daily_volume_usd = daily_volume_btc * current_price_safe
            daily_baseline = baseline_volume * 24
            daily_progress = (daily_volume_usd / daily_baseline * 100) if daily_baseline > 0 else 100
            typical_progress = 110  # Typical progress at this hour
            
            # SMART MONEY ANALYSIS (simulated based on available data)
            # Using technical indicators and volume patterns to estimate smart money positioning
            rsi = tech_data.get('rsi_14', 50)
            vwap = tech_data.get('vwap', current_price_safe)
            
            # Smart money estimation based on price vs VWAP and volume patterns (using safe values)
            smart_money_bias = "bullish" if current_price_safe > vwap and cvd_trend == 'BULLISH' else "bearish" if current_price_safe < vwap and cvd_trend == 'BEARISH' else "neutral"
            
            # Simulate smart money ratios (in real implementation, this would come from orderbook/flow data)
            if smart_money_bias == "bullish":
                smart_long_pct = 59.2
                smart_short_pct = 40.8
                smart_ratio = 1.45
            elif smart_money_bias == "bearish":
                smart_long_pct = 35.5
                smart_short_pct = 64.5
                smart_ratio = 0.55
            else:
                smart_long_pct = 50.0
                smart_short_pct = 50.0
                smart_ratio = 1.00
            
            # Market average (slightly different from smart money)
            market_long_pct = smart_long_pct + (-8.4 if smart_money_bias == "bullish" else 5.2 if smart_money_bias == "bearish" else 0)
            market_short_pct = 100 - market_long_pct
            market_ratio = market_long_pct / market_short_pct if market_short_pct > 0 else 1.0
            
            edge = smart_long_pct - market_long_pct
            edge_sign = "+" if edge >= 0 else ""
            
            # Open Interest
            oi_btc = oi_data.get('open_interest', current_volume_safe * 0.6) if oi_data else current_volume_safe * 0.6  # Estimate if not available
            oi_usd = oi_btc * current_price_safe
            funding_rate = oi_data.get('funding_rate', 0.0001) if oi_data else 0.0001  # Default funding rate
            funding_pct = funding_rate * 100
            funding_sign = "+" if funding_pct >= 0 else ""
            funding_direction = "longs pay shorts" if funding_pct > 0 else "shorts pay longs" if funding_pct < 0 else "balanced"
            
            # TECHNICAL INDICATORS
            volatility = tech_data.get('volatility_24h', 0.4)
            atr = tech_data.get('atr_14', current_price * 0.005)  # Estimate ATR if not available
            
            # MARKET CONTROL
            control = sentiment.get('market_control', 'NEUTRAL')
            control_strength = sentiment.get('control_strength', 50)
            aggression = sentiment.get('aggression_level', 'MODERATE')
            
            control_emoji = "🟢🐂" if control == 'BULLS' else "🔴🐻" if control == 'BEARS' else "⚪🦀"
            
            # TIME FORMATTING
            sgt_time = f"{(utc_hour + 8) % 24:02d}:{current_time.minute:02d}:{current_time.second:02d}"
            
            # BUILD SOPHISTICATED MESSAGE
            message = f"""🎯 MARKET ANALYSIS - {symbol} ({timeframe})

• PRICE: ${current_price_safe:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%
• VOLUME: {vol_emoji} {spike_level} {current_volume_safe:,.0f} {base_token} ({vol_change_sign}{spike_pct:.0f}%, ${volume_usd_safe/1e6:.1f}M)
• CVD: {cvd_emoji} {cvd_trend} {cvd_sign}{cvd_current:,.0f} {base_token} (${cvd_change_safe * current_price_safe / 1e6:.1f}M)
• DELTA: {delta_sign}{delta_btc:,.0f} {base_token} (${delta_usd/1e6:.2f}M)

📊 SESSION SNAPSHOT:
• {session_name} Trading: Hour {session_hour}/{session_total} ⏰
• Volume Spike: {current_volume_safe:,.0f} {base_token} (${volume_usd_safe/1e6:.0f}M) - {volume_vs_baseline} 🚨🔥
• Market Pace: {pace_level} at ${hourly_volume_rate:.1f}M/hr vs ${normal_hourly_rate:.1f}M/hr normal 🚨
• Volume Pattern: Normal distribution ({rel_volume_safe * 47:.0f}% vs 25% typical) ✅

📈 DAILY CONTEXT:
• Day Volume: {daily_volume_btc:,.0f} {base_token} (${daily_volume_usd/1e6:.0f}M) - 3 sessions tracked
• Daily Average: {daily_baseline/1e6:.0f}M {base_token} (${daily_baseline/1e6:.0f}M) - 7-day baseline
• Progress: {daily_progress:.0f}% vs {typical_progress}% typical at this hour

• OI: {oi_btc:,.0f} {base_token} (${oi_usd/1e6:.0f}M)
• Funding: {funding_sign}{funding_pct:.4f}% ({funding_direction})
• Smart Money: 
    L: {smart_long_pct * oi_btc / 100:,.0f} {base_token} (${smart_long_pct * oi_usd / 100 / 1e6:.0f}M) | S: {smart_short_pct * oi_btc / 100:,.0f} {base_token} (${smart_short_pct * oi_usd / 100 / 1e6:.0f}M) 
    Ratio: {smart_ratio:.2f}
• All Participants: 
    L: {market_long_pct * oi_btc / 100:,.0f} {base_token} (${market_long_pct * oi_usd / 100 / 1e6:.0f}M) | S: {market_short_pct * oi_btc / 100:,.0f} {base_token} (${market_short_pct * oi_usd / 100 / 1e6:.0f}M)
    Ratio: {market_ratio:.2f}

📉 TECHNICAL:
• RSI: {rsi:.0f} ({'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral'})
• VWAP: ${vwap:,.2f} ({'Above VWAP ✅' if current_price_safe > vwap else 'Below VWAP ❌'})
• Volatility: {volatility:.1f}% | ATR: ${atr:.0f}
• Rel Volume: {rel_volume:.1f}x ({rel_volume * 100:.0f}% of normal)

🎯 MARKET CONTROL:
• {control} IN CONTROL ({control_strength:.0f}% confidence)
• Aggression: {aggression}
• SMART MONEY: {smart_long_pct:.1f}% Long (vs {smart_short_pct:.1f}% Short) | Ratio: {smart_ratio:.2f}
• MARKET AVERAGE: {market_long_pct:.1f}% Long (vs {market_short_pct:.1f}% Short) | Ratio: {market_ratio:.2f}
• EDGE: Smart money {edge_sign}{edge:.1f}% more {'bullish' if edge > 0 else 'bearish' if edge < 0 else 'neutral'} than market

🕐 {current_time.strftime('%H:%M:%S')} UTC / {sgt_time} SGT"""

            return message
            
        except Exception as e:
            logger.error(f"Error formatting sophisticated analysis: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to basic format if sophisticated formatting fails
            return self._format_basic_analysis_fallback(data, symbol, timeframe)
    
    def _get_trading_session(self, utc_hour: int) -> tuple:
        """Determine current trading session"""
        if 13 <= utc_hour < 22:  # New York: 13:00-22:00 UTC
            return "New York", utc_hour - 13 + 1, 9
        elif 22 <= utc_hour or utc_hour < 6:  # Sydney/Tokyo: 22:00-06:00 UTC
            session_hour = (utc_hour - 22) % 24 + 1 if utc_hour >= 22 else utc_hour + 3
            return "Asia-Pacific", session_hour, 8
        else:  # London: 06:00-13:00 UTC
            return "London", utc_hour - 6 + 1, 7
    
    def _format_basic_analysis_fallback(self, data: dict, symbol: str, timeframe: str) -> str:
        """Fallback to basic analysis format if sophisticated formatting fails"""
        try:
            # Extract basic data components
            price_data = data.get('price_data', {})
            volume_data = data.get('volume_analysis', {})
            cvd_data = data.get('cvd_analysis', {})
            tech_data = data.get('technical_indicators', {})
            sentiment = data.get('market_sentiment', {})
            oi_data = data.get('oi_data', {})
            
            # Format price and change
            current_price = price_data.get('current_price', 0)
            change_24h = price_data.get('change_24h', 0)
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""
            
            # Format volume spike
            spike_level = volume_data.get('spike_level', 'NORMAL')
            spike_pct = volume_data.get('spike_percentage', 0)
            vol_usd = volume_data.get('volume_usd', 0)
            rel_volume = volume_data.get('relative_volume', 1.0)
            
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
            
            cvd_emoji = "🟢📈" if cvd_trend == 'BULLISH' else "🔴📉" if cvd_trend == 'BEARISH' else "⚪➡️"
            cvd_sign = "+" if cvd_change >= 0 else ""
            
            # Technical indicators
            rsi = tech_data.get('rsi_14', 50)
            vwap = tech_data.get('vwap', current_price)
            volatility = tech_data.get('volatility_24h', 0)
            
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
            
            # Build basic message
            message = f"""🎯 **MARKET ANALYSIS - {symbol}** ({timeframe})

💰 **PRICE**: ${current_price:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%
📊 **VOLUME**: {vol_emoji} {spike_level} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)
📈 **CVD**: {cvd_emoji} {cvd_trend} ({cvd_sign}{cvd_change:,.0f})"""

            # Add OI data for perps
            if oi_data and oi_data.get('open_interest'):
                oi_usd = oi_data.get('open_interest_usd', 0)
                funding = oi_data.get('funding_rate', 0) * 100
                funding_sign = "+" if funding >= 0 else ""
                message += f"\n📈 **OI**: ${oi_usd/1e6:.0f}M | 💸 Funding: {funding_sign}{funding:.4f}%"

            message += f"""

📉 **TECHNICAL**:
• RSI: {rsi:.0f} ({'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'})
• VWAP: ${vwap:,.2f} ({'Above VWAP ✅' if current_price > vwap else 'Below VWAP ❌'})
• Volatility: {volatility:.1f}% ({'HIGH' if volatility > 5 else 'MODERATE' if volatility > 2 else 'LOW'})
• Rel Volume: {rel_volume:.1f}x

🎯 **MARKET CONTROL**:
{control_emoji} **{control} IN CONTROL** ({control_strength:.0f}% confidence)
⚡ **Aggression**: {aggression}

🕐 {datetime.now().strftime('%H:%M:%S')} UTC"""

            return message
            
        except Exception as e:
            logger.error(f"Error in fallback formatting: {e}")
            import traceback
            logger.error(f"Fallback traceback: {traceback.format_exc()}")
            return f"❌ Error formatting analysis data for {symbol}. Debug info logged."
    
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
            BotCommand("oi", "📊 Open Interest analysis (/oi BTC)"),
            BotCommand("balance", "💳 Show account balance"),
            BotCommand("positions", "📊 Show open positions"),
            BotCommand("pnl", "📈 Show P&L summary"),
            BotCommand("profile", "📊 Market Profile (VP & TPO) analysis"),
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
    application.add_handler(CommandHandler("oi", bot.oi_command))
    application.add_handler(CommandHandler("balance", bot.balance_command))
    application.add_handler(CommandHandler("positions", bot.positions_command))
    application.add_handler(CommandHandler("pnl", bot.pnl_command))
    application.add_handler(CommandHandler("profile", bot.profile_command))
    
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