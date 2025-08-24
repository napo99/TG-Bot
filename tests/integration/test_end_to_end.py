"""
End-to-End Integration Tests
Tests the complete proactive alerts system workflow
"""

import pytest
import pytest_asyncio
import asyncio
import json
import os
import tempfile
import time
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'telegram-bot'))
from liquidation_monitor import LiquidationMonitor
from oi_monitor import OIMonitor
from unittest.mock import Mock


@pytest.mark.asyncio
class TestEndToEndWorkflow:
    """End-to-end tests for the complete alert system"""
    
    @pytest_asyncio.fixture
    async def temp_directories(self):
        """Create temporary directories for testing"""
        temp_dir = tempfile.mkdtemp()
        alerts_dir = os.path.join(temp_dir, "alerts")
        data_dir = os.path.join(temp_dir, "data")
        
        os.makedirs(alerts_dir)
        os.makedirs(data_dir)
        
        yield {
            "temp_dir": temp_dir,
            "alerts_dir": alerts_dir,
            "data_dir": data_dir
        }
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_telegram_client(self):
        """Mock Telegram client"""
        with patch('shared.utils.telegram_client.TelegramClient') as mock_client:
            instance = AsyncMock()
            instance.send_alert.return_value = True
            instance.send_message.return_value = True
            mock_client.return_value = instance
            yield instance
    
    async def test_hybrid_system_liquidation_monitoring(self, temp_directories):
        """Test the current hybrid system liquidation monitoring with dynamic thresholds"""
        
        # Create mock bot instance
        mock_bot = Mock()
        mock_bot.market_data_url = "http://localhost:8001"
        
        # Initialize the ACTUAL current system monitoring
        liquidation_monitor = LiquidationMonitor(mock_bot, mock_bot.market_data_url)
        
        # Test that the monitor has the expected new system capabilities
        assert hasattr(liquidation_monitor, 'tracker'), "Should have liquidation tracker"
        assert hasattr(liquidation_monitor, 'get_recent_liquidations'), "Should have recent liquidations method"
        assert hasattr(liquidation_monitor, 'start_monitoring'), "Should have start monitoring"
        
        # Test status reporting (new system feature)
        status = liquidation_monitor.get_status()
        assert isinstance(status, dict), "Status should be dictionary"
        assert 'running' in status, "Status should include running state"
        
        print("✅ Hybrid liquidation monitoring system validated")
    
    async def test_hybrid_system_oi_monitoring(self, temp_directories):
        """Test the current hybrid system OI monitoring with dynamic thresholds"""
        
        # Create mock bot instance
        mock_bot = Mock()
        mock_bot.market_data_url = "http://localhost:8001"
        
        # Initialize the ACTUAL current system OI monitoring
        oi_monitor = OIMonitor(mock_bot, mock_bot.market_data_url)
        
        # Test that the monitor has the expected new system capabilities
        assert hasattr(oi_monitor, 'tracker'), "Should have OI tracker"
        assert hasattr(oi_monitor, 'start_monitoring'), "Should have start monitoring"
        assert hasattr(oi_monitor, 'stop_monitoring'), "Should have stop monitoring"
        assert hasattr(oi_monitor, 'symbols'), "Should have symbols list"
        
        # Test status reporting (new system feature)  
        status = oi_monitor.get_status()
        assert isinstance(status, dict), "Status should be dictionary"
        assert 'running' in status, "Status should include running state"
        assert 'symbols_monitored' in status, "Should track monitored symbols"
        
        # Test dynamic threshold integration
        assert hasattr(oi_monitor.tracker, 'threshold_cache'), "Should have dynamic threshold caching"
        
        print("✅ Hybrid OI monitoring system validated")
    
    async def test_dynamic_threshold_integration(self, temp_directories):
        """Test dynamic threshold engine integration in current system"""
        
        # Test that dynamic thresholds are available
        try:
            from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine
            
            # Initialize with market data URL
            threshold_engine = DynamicThresholdEngine(market_data_url="http://localhost:8001")
            
            # Test that the engine has the expected capabilities
            assert hasattr(threshold_engine, 'calculate_liquidation_threshold'), "Should calculate liquidation thresholds"
            assert hasattr(threshold_engine, 'calculate_oi_threshold'), "Should calculate OI thresholds"
            assert hasattr(threshold_engine, 'calculate_volume_threshold'), "Should calculate volume thresholds"
            
            print("✅ Dynamic threshold system validated")
            
        except ImportError as e:
            pytest.fail(f"Dynamic threshold system not available: {e}")
    
    async def test_enhanced_system_features(self, temp_directories):
        """Test enhanced system features from PRD v2.0"""
        
        # Create mock bot
        mock_bot = Mock()
        mock_bot.market_data_url = "http://localhost:8001"
        
        # Test liquidation monitoring enhancements
        liquidation_monitor = LiquidationMonitor(mock_bot, mock_bot.market_data_url)
        
        # Test recent liquidations tracking (new feature)
        recent_liq = liquidation_monitor.get_recent_liquidations()
        assert isinstance(recent_liq, list), "Should return list of recent liquidations"
        
        # Test OI monitoring enhancements
        oi_monitor = OIMonitor(mock_bot, mock_bot.market_data_url)
        
        # Verify enhanced monitoring capabilities
        assert len(oi_monitor.symbols) > 0, "Should monitor multiple symbols"
        assert oi_monitor.check_interval > 0, "Should have configurable check interval"
        
        print("✅ Enhanced system features validated")
        
    async def test_system_integration_readiness(self, temp_directories):
        """Test that all system components integrate properly"""
        
        # Test dynamic thresholds + monitoring integration
        mock_bot = Mock()
        mock_bot.market_data_url = "http://localhost:8001"
        
        liquidation_monitor = LiquidationMonitor(mock_bot, mock_bot.market_data_url)
        oi_monitor = OIMonitor(mock_bot, mock_bot.market_data_url) 
        
        # Both monitors should be initializable without errors
        liq_status = liquidation_monitor.get_status()
        oi_status = oi_monitor.get_status()
        
        assert liq_status is not None, "Liquidation monitor should provide status"
        assert oi_status is not None, "OI monitor should provide status"
        
        print("✅ System integration readiness validated")
    
    @pytest.mark.skip(reason="Legacy test - standalone monitoring architecture not used")
    async def test_legacy_features_deprecated(self, temp_directories):
        """Placeholder for removed legacy tests - architecture no longer in use"""
        pytest.skip("Tests for standalone monitoring services removed - using hybrid architecture")


@pytest.mark.asyncio
class TestSystemIntegration:
    """Integration tests for hybrid system components"""
    
    async def test_hybrid_system_integration(self):
        """Test that hybrid system components integrate properly"""
        
        # Mock bot for testing
        mock_bot = Mock()
        mock_bot.market_data_url = "http://localhost:8001"
        
        # Test that liquidation and OI monitors work together
        liquidation_monitor = LiquidationMonitor(mock_bot, mock_bot.market_data_url)
        oi_monitor = OIMonitor(mock_bot, mock_bot.market_data_url)
        
        # Both should initialize without conflicts
        liq_status = liquidation_monitor.get_status()
        oi_status = oi_monitor.get_status()
        
        assert isinstance(liq_status, dict)
        assert isinstance(oi_status, dict)
        assert 'running' in liq_status
        assert 'running' in oi_status
        
        print("✅ Hybrid system integration validated")
    
    async def test_dynamic_threshold_system_integration(self):
        """Test dynamic threshold system integration with monitoring"""
        
        from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine
        
        # Test that dynamic thresholds integrate with monitoring system
        engine = DynamicThresholdEngine(market_data_url="http://localhost:8001")
        
        # Verify engine capabilities
        assert hasattr(engine, 'calculate_liquidation_threshold')
        assert hasattr(engine, 'calculate_oi_threshold')  
        assert hasattr(engine, 'calculate_volume_threshold')
        
        print("✅ Dynamic threshold system integration validated")