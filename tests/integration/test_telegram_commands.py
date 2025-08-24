"""
Comprehensive Test Suite for Enhanced Telegram Bot Commands
Tests all commands with dynamic threshold integration and proactive features

This test suite validates:
- Reactive commands (/price, /volume, /oi, /cvd, /profile)  
- Proactive features (/alerts system)
- Dynamic threshold integration
- Error handling and input validation
- Response format validation
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import bot components with correct path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'telegram-bot'))
from main import TelegramBot, MarketDataClient
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes


class MockUpdate:
    """Mock Telegram Update object for testing"""
    
    def __init__(self, user_id: int = 123456, chat_id: int = 789012, text: str = ""):
        self.effective_user = MagicMock()
        self.effective_user.id = user_id
        
        self.message = MagicMock()
        self.message.reply_text = AsyncMock()
        self.message.edit_text = AsyncMock() 
        self.message.delete = AsyncMock()
        
        self.effective_chat = MagicMock()
        self.effective_chat.id = chat_id


class MockContext:
    """Mock Telegram Context object for testing"""
    
    def __init__(self, args: list = None):
        self.args = args or []
        self.bot = MagicMock()


class MockMarketDataResponse:
    """Mock market data API responses"""
    
    @staticmethod
    def success_price_btc() -> Dict[str, Any]:
        """Mock successful BTC price response"""
        return {
            'success': True,
            'data': {
                'base_symbol': 'BTC/USDT',
                'spot_exchange': 'binance',
                'perp_exchange': 'binance',
                'spot': {
                    'price': 50000.0,
                    'change_24h': 2.5,
                    'change_15m': 0.3,
                    'volume_24h': 100000.0,
                    'volume_15m': 5000.0,
                    'delta_24h': 15000.0,
                    'delta_15m': 800.0,
                    'atr_24h': 1500.0,
                    'atr_15m': 150.0
                },
                'perp': {
                    'price': 50050.0,
                    'change_24h': 2.6,
                    'change_15m': 0.35,
                    'volume_24h': 200000.0,
                    'volume_15m': 8000.0,
                    'delta_24h': 25000.0,
                    'delta_15m': 1200.0,
                    'open_interest': 150000.0,
                    'oi_change_24h': 5000.0,
                    'oi_change_15m': 200.0,
                    'funding_rate': 0.0001,
                    'atr_24h': 1600.0,
                    'atr_15m': 160.0
                }
            }
        }
    
    @staticmethod
    def success_volume_analysis() -> Dict[str, Any]:
        """Mock successful volume analysis response"""
        return {
            'success': True,
            'data': {
                'symbol': 'BTCUSDT',
                'spike_level': 'HIGH',
                'spike_percentage': 350.0,
                'current_volume': 125000.0,
                'average_volume': 30000.0,
                'volume_usd': 6250000000.0,
                'is_significant': True
            }
        }
    
    @staticmethod
    def success_cvd_analysis() -> Dict[str, Any]:
        """Mock successful CVD analysis response"""
        return {
            'success': True,
            'data': {
                'symbol': 'BTCUSDT',
                'cvd_trend': 'BULLISH',
                'current_cvd': 250000.0,
                'cvd_change_24h': 15000.0,
                'divergence_detected': False,
                'price_trend': 'BULLISH'
            }
        }
    
    @staticmethod
    def success_oi_analysis() -> Dict[str, Any]:
        """Mock successful OI analysis response"""
        return {
            'success': True,
            'exchange_breakdown': [
                {
                    'exchange': 'binance',
                    'market_breakdown': [
                        {
                            'symbol': 'BTCUSDT',
                            'type': 'USDT',
                            'oi_tokens': 50000.0,
                            'oi_usd': 2500000000.0,
                            'funding_rate': 0.0001,
                            'volume_24h': 100000.0
                        },
                        {
                            'symbol': 'BTCUSDC',
                            'type': 'USDC', 
                            'oi_tokens': 25000.0,
                            'oi_usd': 1250000000.0,
                            'funding_rate': 0.0002,
                            'volume_24h': 50000.0
                        }
                    ]
                }
            ],
            'aggregated_oi': {
                'total_tokens': 75000.0,
                'total_usd': 3750000000.0
            },
            'market_categories': {
                'usdt_stable': {
                    'total_usd': 2500000000.0,
                    'percentage': 66.7
                },
                'usdc_stable': {
                    'total_usd': 1250000000.0,
                    'percentage': 33.3
                },
                'usd_inverse': {
                    'total_usd': 0.0,
                    'percentage': 0.0
                }
            },
            'validation_summary': {
                'successful_exchanges': 1
            },
            'total_markets': 2
        }
    
    @staticmethod
    def success_market_profile() -> Dict[str, Any]:
        """Mock successful market profile response"""
        return {
            'success': True,
            'data': {
                'symbol': 'BTCUSDT',
                'current_price': 50000.0,
                '1h': {
                    'volume_profile': {'poc': 49800.0, 'val': 49500.0, 'vah': 50200.0},
                    'tpo': {'poc': 49850.0, 'val': 49600.0, 'vah': 50100.0},
                    'period': '1h',
                    'candles': 60,
                    'vwap': 49900.0
                },
                '4h': {
                    'volume_profile': {'poc': 49700.0, 'val': 49200.0, 'vah': 50300.0},
                    'tpo': {'poc': 49750.0, 'val': 49300.0, 'vah': 50200.0},
                    'period': '4h',
                    'candles': 240,
                    'vwap': 49850.0
                },
                '1d': {
                    'volume_profile': {'poc': 49500.0, 'val': 48800.0, 'vah': 50500.0},
                    'tpo': {'poc': 49600.0, 'val': 49000.0, 'vah': 50400.0},
                    'period': '1d',
                    'candles': 1440,
                    'vwap': 49750.0
                }
            }
        }
    
    @staticmethod
    def success_comprehensive_analysis() -> Dict[str, Any]:
        """Mock successful comprehensive analysis response"""
        return {
            'success': True,
            'data': {
                'price_data': {
                    'current_price': 50000.0,
                    'change_24h': 2.5
                },
                'volume_analysis': {
                    'current_volume': 125000.0,
                    'volume_usd': 6250000000.0,
                    'spike_level': 'HIGH',
                    'spike_percentage': 350.0,
                    'relative_volume': 3.5
                },
                'cvd_analysis': {
                    'current_cvd': 250000.0,
                    'cvd_change_24h': 15000.0,
                    'cvd_trend': 'BULLISH'
                },
                'technical_indicators': {
                    'rsi_14': 65.0,
                    'vwap': 49900.0,
                    'volatility_24h': 0.04
                },
                'market_sentiment': {
                    'market_control': 'BULLS',
                    'control_strength': 75.0,
                    'aggression_level': 'MODERATE'
                },
                'oi_data': {
                    'open_interest': 150000.0,
                    'open_interest_usd': 7500000000.0,
                    'funding_rate': 0.0001
                }
            }
        }
    
    @staticmethod
    def error_response(error_msg: str = "API Error") -> Dict[str, Any]:
        """Mock error response"""
        return {
            'success': False,
            'error': error_msg
        }


@pytest.fixture
def mock_bot():
    """Create mock TelegramBot instance"""
    bot = TelegramBot()
    bot.market_client = AsyncMock()
    # Mock authorization to always return True for tests
    bot._is_authorized = MagicMock(return_value=True)
    return bot


@pytest.fixture
def mock_update():
    """Create mock Update object"""
    return MockUpdate()


@pytest.fixture
def mock_context_no_args():
    """Create mock Context with no arguments"""
    return MockContext([])


@pytest.fixture
def mock_context_btc():
    """Create mock Context with BTC argument"""
    return MockContext(['BTCUSDT'])


@pytest.fixture
def mock_context_btc_15m():
    """Create mock Context with BTC and 15m timeframe"""
    return MockContext(['BTCUSDT', '15m'])


class TestPriceCommand:
    """Test /price command functionality"""
    
    @pytest.mark.asyncio
    async def test_price_command_success_btc(self, mock_bot, mock_update, mock_context_btc):
        """Test successful /price BTCUSDT command"""
        # Mock the market data response
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.success_price_btc()
        
        await mock_bot.price_command(mock_update, mock_context_btc)
        
        # Verify API was called correctly
        mock_bot.market_client.get_combined_price.assert_called_once_with('BTCUSDT')
        
        # Verify response was sent
        mock_update.message.reply_text.assert_called()
        
        # Check that the response contains expected elements
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "SPOT" in response_text
        assert "PERPETUALS" in response_text
        assert "$50,000" in response_text or "50000" in response_text
        assert "+2.50%" in response_text or "+2.60%" in response_text
        assert "parse_mode" in response_args[1]
    
    @pytest.mark.asyncio
    async def test_price_command_no_args(self, mock_bot, mock_update, mock_context_no_args):
        """Test /price command without symbol argument"""
        await mock_bot.price_command(mock_update, mock_context_no_args)
        
        # Should return error message
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Please provide a symbol" in response_text
        assert "Example:" in response_text
    
    @pytest.mark.asyncio
    async def test_price_command_api_error(self, mock_bot, mock_update, mock_context_btc):
        """Test /price command with API error"""
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.error_response()
        
        await mock_bot.price_command(mock_update, mock_context_btc)
        
        # Should return error message
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Error fetching price" in response_text
    
    @pytest.mark.asyncio
    async def test_price_command_unauthorized(self, mock_bot, mock_update, mock_context_btc):
        """Test /price command with unauthorized user"""
        with patch.object(mock_bot, '_is_authorized', return_value=False):
            await mock_bot.price_command(mock_update, mock_context_btc)
            
            mock_update.message.reply_text.assert_called_once_with("❌ Unauthorized access")


class TestVolumeCommand:
    """Test /volume command functionality"""
    
    @pytest.mark.asyncio
    async def test_volume_command_success(self, mock_bot, mock_update, mock_context_btc_15m):
        """Test successful /volume BTCUSDT 15m command"""
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        
        await mock_bot.volume_command(mock_update, mock_context_btc_15m)
        
        # Verify API was called correctly
        mock_bot.market_client.get_volume_spike.assert_called_once_with('BTCUSDT', '15m')
        
        # Verify response
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "VOLUME ANALYSIS" in response_text
        assert "HIGH" in response_text
        assert "+350%" in response_text or "350.0%" in response_text
        assert "6.3M" in response_text or "$6" in response_text
    
    @pytest.mark.asyncio
    async def test_volume_command_default_timeframe(self, mock_bot, mock_update, mock_context_btc):
        """Test /volume command with default timeframe"""
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        
        await mock_bot.volume_command(mock_update, mock_context_btc)
        
        # Should use 15m as default timeframe
        mock_bot.market_client.get_volume_spike.assert_called_once_with('BTCUSDT', '15m')
    
    @pytest.mark.asyncio
    async def test_volume_command_no_args(self, mock_bot, mock_update, mock_context_no_args):
        """Test /volume command without arguments"""
        await mock_bot.volume_command(mock_update, mock_context_no_args)
        
        # Should return error message
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Please provide a symbol" in response_text


class TestCVDCommand:
    """Test /cvd command functionality"""
    
    @pytest.mark.asyncio
    async def test_cvd_command_success(self, mock_bot, mock_update, mock_context_btc_15m):
        """Test successful /cvd BTCUSDT 1h command"""
        mock_context_1h = MockContext(['BTCUSDT', '1h'])
        mock_bot.market_client.get_cvd.return_value = MockMarketDataResponse.success_cvd_analysis()
        
        await mock_bot.cvd_command(mock_update, mock_context_1h)
        
        # Verify API was called correctly
        mock_bot.market_client.get_cvd.assert_called_once_with('BTCUSDT', '1h')
        
        # Verify response
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "CVD ANALYSIS" in response_text
        assert "BULLISH" in response_text
        assert "250,000" in response_text or "250000" in response_text
        assert "+15,000" in response_text or "15,000" in response_text
        assert "No divergence" in response_text or "divergence" in response_text
    
    @pytest.mark.asyncio
    async def test_cvd_command_default_timeframe(self, mock_bot, mock_update, mock_context_btc):
        """Test /cvd command with default 1h timeframe"""
        mock_bot.market_client.get_cvd.return_value = MockMarketDataResponse.success_cvd_analysis()
        
        await mock_bot.cvd_command(mock_update, mock_context_btc)
        
        # Should use 1h as default timeframe
        mock_bot.market_client.get_cvd.assert_called_once_with('BTCUSDT', '1h')


class TestOICommand:
    """Test /oi command functionality"""
    
    @pytest.mark.asyncio
    async def test_oi_command_success_btc(self, mock_bot, mock_update, mock_context_btc):
        """Test successful /oi BTC command"""
        mock_bot.market_client.get_oi_analysis.return_value = MockMarketDataResponse.success_oi_analysis()
        
        await mock_bot.oi_command(mock_update, mock_context_btc)
        
        # Verify API was called correctly
        mock_bot.market_client.get_oi_analysis.assert_called_once_with('BTCUSDT')
        
        # Verify response
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "OPEN INTEREST ANALYSIS" in response_text
        assert "MARKET TYPE BREAKDOWN" in response_text
        assert "$3.8B" in response_text or "3.8B" in response_text
        assert "USDT" in response_text
        assert "USDC" in response_text
    
    @pytest.mark.asyncio
    async def test_oi_command_default_btc(self, mock_bot, mock_update, mock_context_no_args):
        """Test /oi command with default BTC symbol"""
        mock_bot.market_client.get_oi_analysis.return_value = MockMarketDataResponse.success_oi_analysis()
        
        await mock_bot.oi_command(mock_update, mock_context_no_args)
        
        # Should use BTC as default
        mock_bot.market_client.get_oi_analysis.assert_called_once_with('BTC')


class TestProfileCommand:
    """Test /profile command functionality"""
    
    @pytest.mark.asyncio
    async def test_profile_command_success(self, mock_bot, mock_update, mock_context_btc):
        """Test successful /profile BTC command"""
        mock_bot.market_client.get_market_profile.return_value = MockMarketDataResponse.success_market_profile()
        
        # Mock the loading message
        loading_msg = MagicMock()
        loading_msg.delete = AsyncMock()
        mock_update.message.reply_text.return_value = loading_msg
        
        await mock_bot.profile_command(mock_update, mock_context_btc)
        
        # Verify API was called correctly (symbol gets cleaned: BTCUSDT -> BTCUSDT)
        mock_bot.market_client.get_market_profile.assert_called_once_with('BTCUSDT')
        
        # Verify loading message was sent and deleted
        assert mock_update.message.reply_text.call_count == 2  # Loading message + result
        loading_msg.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_profile_command_default_btc(self, mock_bot, mock_update, mock_context_no_args):
        """Test /profile command with default BTC symbol"""
        mock_bot.market_client.get_market_profile.return_value = MockMarketDataResponse.success_market_profile()
        
        # Mock the loading message
        loading_msg = MagicMock()
        loading_msg.delete = AsyncMock()
        mock_update.message.reply_text.return_value = loading_msg
        
        await mock_bot.profile_command(mock_update, mock_context_no_args)
        
        # Should use BTC as default
        mock_bot.market_client.get_market_profile.assert_called_once_with('BTC')


class TestAnalysisCommand:
    """Test /analysis command functionality"""
    
    @pytest.mark.asyncio
    async def test_analysis_command_success(self, mock_bot, mock_update, mock_context_btc_15m):
        """Test successful /analysis BTCUSDT 15m command"""
        mock_bot.market_client.get_comprehensive_analysis.return_value = MockMarketDataResponse.success_comprehensive_analysis()
        
        await mock_bot.analysis_command(mock_update, mock_context_btc_15m)
        
        # Verify API was called correctly
        mock_bot.market_client.get_comprehensive_analysis.assert_called_once_with('BTCUSDT', '15m')
        
        # Verify response
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "MARKET ANALYSIS" in response_text
        assert "$50,000" in response_text or "50000" in response_text
        assert "BULLS IN CONTROL" in response_text
    
    @pytest.mark.asyncio
    async def test_analysis_command_default_timeframe(self, mock_bot, mock_update, mock_context_btc):
        """Test /analysis command with default timeframe"""
        mock_bot.market_client.get_comprehensive_analysis.return_value = MockMarketDataResponse.success_comprehensive_analysis()
        
        await mock_bot.analysis_command(mock_update, mock_context_btc)
        
        # Should use 15m as default timeframe
        mock_bot.market_client.get_comprehensive_analysis.assert_called_once_with('BTCUSDT', '15m')


class TestProactiveAlerts:
    """Test proactive alert system commands"""
    
    @pytest.mark.asyncio
    async def test_alerts_status_command(self, mock_bot, mock_update, mock_context_no_args):
        """Test /alerts command (status display)"""
        await mock_bot.alerts_command(mock_update, mock_context_no_args)
        
        # Should show status
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Proactive Alert System Status" in response_text
        assert "Liquidation Monitor" in response_text
        assert "OI Explosion Monitor" in response_text
        assert "Commands:" in response_text
        assert "Thresholds:" in response_text
    
    @pytest.mark.asyncio
    async def test_alerts_start_command(self, mock_bot, mock_update):
        """Test /alerts start command"""
        mock_context = MockContext(['start'])
        
        # Mock the _start_monitoring method
        mock_bot._start_monitoring = AsyncMock()
        
        await mock_bot.alerts_command(mock_update, mock_context)
        
        # Should start monitoring
        mock_bot._start_monitoring.assert_called_once()
        
        # Should send confirmation
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Proactive Alert Monitoring Started" in response_text
        assert "Liquidation cascade detection activated" in response_text
    
    @pytest.mark.asyncio
    async def test_alerts_stop_command(self, mock_bot, mock_update):
        """Test /alerts stop command"""
        mock_context = MockContext(['stop'])
        
        # Mock the _stop_monitoring method
        mock_bot._stop_monitoring = AsyncMock()
        
        await mock_bot.alerts_command(mock_update, mock_context)
        
        # Should stop monitoring
        mock_bot._stop_monitoring.assert_called_once()
        
        # Should send confirmation
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Proactive Alert Monitoring Stopped" in response_text
    
    @pytest.mark.asyncio
    async def test_alerts_detailed_status(self, mock_bot, mock_update):
        """Test /alerts status command (detailed)"""
        mock_context = MockContext(['status'])
        
        # Mock monitors with status
        mock_bot.liquidation_monitor = MagicMock()
        mock_bot.liquidation_monitor.get_status.return_value = {
            'running': True,
            'connected': True,
            'total_tracked': 150
        }
        
        mock_bot.oi_monitor = MagicMock()
        mock_bot.oi_monitor.get_status.return_value = {
            'running': True,
            'symbols_monitored': 10,
            'check_interval': 30,
            'total_snapshots': 500
        }
        
        # Mock the _send_detailed_status method
        mock_bot._send_detailed_status = AsyncMock()
        
        await mock_bot.alerts_command(mock_update, mock_context)
        
        # Should send detailed status
        mock_bot._send_detailed_status.assert_called_once_with(mock_update)
    
    @pytest.mark.asyncio
    async def test_liquidations_command(self, mock_bot, mock_update, mock_context_no_args):
        """Test /liquidations command"""
        # Mock the _send_recent_alerts method
        mock_bot._send_recent_alerts = AsyncMock()
        
        await mock_bot.liquidations_command(mock_update, mock_context_no_args)
        
        # Should send recent alerts
        mock_bot._send_recent_alerts.assert_called_once_with(mock_update)


class TestDynamicThresholdIntegration:
    """Test integration with dynamic threshold system"""
    
    @pytest.mark.asyncio
    async def test_dynamic_thresholds_in_alerts_start(self, mock_bot, mock_update):
        """Test that starting alerts uses dynamic thresholds"""
        mock_context = MockContext(['start'])
        
        # Mock monitors and threshold engine
        with patch('main.LiquidationMonitor') as MockLiquidationMonitor:
            with patch('main.OIMonitor') as MockOIMonitor:
                mock_liq_monitor = MockLiquidationMonitor.return_value
                mock_oi_monitor = MockOIMonitor.return_value
                
                await mock_bot.alerts_command(mock_update, mock_context)
                
                # Verify monitors were created with correct parameters
                MockLiquidationMonitor.assert_called_once_with(mock_bot, mock_bot.market_data_url)
                MockOIMonitor.assert_called_once_with(mock_bot, mock_bot.market_data_url)
    
    @pytest.mark.asyncio
    async def test_volume_command_with_dynamic_thresholds(self, mock_bot, mock_update, mock_context_btc):
        """Test that volume command can handle dynamic threshold responses"""
        # Mock response with dynamic threshold values
        dynamic_response = {
            'success': True,
            'data': {
                'symbol': 'BTCUSDT',
                'spike_level': 'EXTREME',  # Dynamic threshold determined this
                'spike_percentage': 750.0,  # Much higher threshold
                'current_volume': 300000.0,
                'average_volume': 40000.0,
                'volume_usd': 15000000000.0,
                'is_significant': True,
                'threshold_source': 'dynamic_tier_1'  # Indicates dynamic calculation
            }
        }
        
        mock_bot.market_client.get_volume_spike.return_value = dynamic_response
        
        await mock_bot.volume_command(mock_update, mock_context_btc)
        
        # Verify response handles extreme spike levels
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "EXTREME" in response_text
        assert "🔥🔥🔥" in response_text  # Should show extreme emoji
        assert "750.0%" in response_text or "+750.0%" in response_text


class TestErrorHandling:
    """Test error handling across all commands"""
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, mock_bot, mock_update, mock_context_btc):
        """Test handling of network timeouts"""
        # Mock network timeout
        mock_bot.market_client.get_combined_price.side_effect = asyncio.TimeoutError("Request timeout")
        
        await mock_bot.price_command(mock_update, mock_context_btc)
        
        # Should handle gracefully
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Error fetching price" in response_text
    
    @pytest.mark.asyncio
    async def test_invalid_symbol_handling(self, mock_bot, mock_update):
        """Test handling of invalid symbols"""
        mock_context = MockContext(['INVALIDSYMBOL'])
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.error_response("Symbol not found")
        
        await mock_bot.price_command(mock_update, mock_context)
        
        # Should return error message
        mock_update.message.reply_text.assert_called()
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        
        assert "Error fetching price" in response_text
        assert "Symbol not found" in response_text
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, mock_bot, mock_update, mock_context_btc):
        """Test handling of malformed API responses"""
        # Mock malformed response
        malformed_response = {
            'success': True,
            'data': {
                'incomplete': 'data'
                # Missing required fields
            }
        }
        
        mock_bot.market_client.get_combined_price.return_value = malformed_response
        
        await mock_bot.price_command(mock_update, mock_context_btc)
        
        # Should handle gracefully (might show partial data or error)
        mock_update.message.reply_text.assert_called()


class TestAuthorizationValidation:
    """Test authorization across all commands"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access_all_commands(self, mock_bot, mock_update):
        """Test that all commands properly check authorization"""
        # Mock unauthorized user
        with patch.object(mock_bot, '_is_authorized', return_value=False):
            commands_to_test = [
                ('price_command', MockContext(['BTCUSDT'])),
                ('volume_command', MockContext(['BTCUSDT'])),
                ('cvd_command', MockContext(['BTCUSDT'])),
                ('oi_command', MockContext(['BTC'])),
                ('profile_command', MockContext(['BTC'])),
                ('analysis_command', MockContext(['BTCUSDT'])),
                ('alerts_command', MockContext(['start'])),
                ('liquidations_command', MockContext([])),
            ]
            
            for command_name, context in commands_to_test:
                # Reset mock
                mock_update.message.reply_text.reset_mock()
                
                # Call command
                command_method = getattr(mock_bot, command_name)
                await command_method(mock_update, context)
                
                # Should return unauthorized message
                mock_update.message.reply_text.assert_called_once_with("❌ Unauthorized access")


class TestResponseFormatValidation:
    """Test response format consistency"""
    
    @pytest.mark.asyncio
    async def test_price_response_format(self, mock_bot, mock_update, mock_context_btc):
        """Test that price command response has consistent format"""
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.success_price_btc()
        
        await mock_bot.price_command(mock_update, mock_context_btc)
        
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        response_kwargs = response_args[1] if len(response_args) > 1 else {}
        
        # Check format elements
        assert "📊" in response_text  # Header emoji
        assert "SPOT" in response_text
        assert "PERPETUALS" in response_text
        assert "🕐" in response_text  # Timestamp
        assert response_kwargs.get('parse_mode') == 'Markdown'
    
    @pytest.mark.asyncio
    async def test_volume_response_format(self, mock_bot, mock_update, mock_context_btc):
        """Test that volume command response has consistent format"""
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        
        await mock_bot.volume_command(mock_update, mock_context_btc)
        
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        response_kwargs = response_args[1] if len(response_args) > 1 else {}
        
        # Check format elements
        assert "📊 **VOLUME ANALYSIS" in response_text
        assert "Spike Level" in response_text
        assert "Volume Change" in response_text
        assert "Updated:" in response_text
        assert response_kwargs.get('parse_mode') == 'Markdown'


class TestLoadAndConcurrency:
    """Test load handling and concurrent request processing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_price_requests(self, mock_bot):
        """Test handling concurrent price requests"""
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.success_price_btc()
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            mock_update = MockUpdate(user_id=123450 + i)
            mock_context = MockContext(['BTCUSDT'])
            task = mock_bot.price_command(mock_update, mock_context)
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without exceptions
        for result in results:
            assert not isinstance(result, Exception)
        
        # Should have made API calls
        assert mock_bot.market_client.get_combined_price.call_count == 10
    
    @pytest.mark.asyncio
    async def test_mixed_command_concurrency(self, mock_bot):
        """Test concurrent execution of different commands"""
        # Mock all required responses
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.success_price_btc()
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        mock_bot.market_client.get_cvd.return_value = MockMarketDataResponse.success_cvd_analysis()
        mock_bot.market_client.get_oi_analysis.return_value = MockMarketDataResponse.success_oi_analysis()
        
        # Create different command tasks
        update1 = MockUpdate(user_id=1)
        update2 = MockUpdate(user_id=2)
        update3 = MockUpdate(user_id=3)
        update4 = MockUpdate(user_id=4)
        
        tasks = [
            mock_bot.price_command(update1, MockContext(['BTCUSDT'])),
            mock_bot.volume_command(update2, MockContext(['BTCUSDT'])),
            mock_bot.cvd_command(update3, MockContext(['BTCUSDT'])),
            mock_bot.oi_command(update4, MockContext(['BTC']))
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete
        for result in results:
            assert not isinstance(result, Exception)
        
        # Each update should have received a response
        for update in [update1, update2, update3, update4]:
            update.message.reply_text.assert_called()


class TestIntegrationScenarios:
    """Test realistic user interaction scenarios"""
    
    @pytest.mark.asyncio
    async def test_typical_user_session(self, mock_bot, mock_update):
        """Test a typical user session with multiple commands"""
        # Mock all required responses
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.success_price_btc()
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        mock_bot.market_client.get_comprehensive_analysis.return_value = MockMarketDataResponse.success_comprehensive_analysis()
        mock_bot._start_monitoring = AsyncMock()
        
        # Simulate user session: price -> volume -> analysis -> enable alerts
        session_commands = [
            (mock_bot.price_command, MockContext(['BTCUSDT'])),
            (mock_bot.volume_command, MockContext(['BTCUSDT', '15m'])),
            (mock_bot.analysis_command, MockContext(['BTCUSDT', '15m'])),
            (mock_bot.alerts_command, MockContext(['start']))
        ]
        
        for command_method, context in session_commands:
            mock_update.message.reply_text.reset_mock()
            await command_method(mock_update, context)
            
            # Each command should send a response
            mock_update.message.reply_text.assert_called()
        
        # Monitoring should be started
        mock_bot._start_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, mock_bot, mock_update):
        """Test error recovery in user session"""
        # First command fails
        mock_bot.market_client.get_combined_price.return_value = MockMarketDataResponse.error_response("Network error")
        
        await mock_bot.price_command(mock_update, MockContext(['BTCUSDT']))
        
        # Should get error message
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        assert "Error fetching price" in response_text
        
        # Second command succeeds
        mock_update.message.reply_text.reset_mock()
        mock_bot.market_client.get_volume_spike.return_value = MockMarketDataResponse.success_volume_analysis()
        
        await mock_bot.volume_command(mock_update, MockContext(['BTCUSDT']))
        
        # Should get successful response
        response_args = mock_update.message.reply_text.call_args
        response_text = response_args[0][0] if response_args else ""
        assert "VOLUME ANALYSIS" in response_text


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short', '--asyncio-mode=auto'])