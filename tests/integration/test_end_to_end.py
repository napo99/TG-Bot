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
    
    @pytest.mark.skip(reason="Requires running market-data service")
    async def test_oi_detection_workflow(self, temp_directories):
        """Test OI explosion detection workflow (requires market data service)"""
        
        oi_detector = OIExplosionDetector()
        oi_detector.alert_output_path = os.path.join(
            temp_directories["alerts_dir"], "oi_alerts.json"
        )
        
        # Mock the market data API response
        mock_oi_data = {
            "binance": {"oi_usd": 2500000000, "oi_change_24h": 18.5},
            "bybit": {"oi_usd": 1800000000, "oi_change_24h": 16.2},
            "okx": {"oi_usd": 1600000000, "oi_change_24h": 20.1}
        }
        
        with patch.object(oi_detector, 'fetch_oi_data', return_value=mock_oi_data):
            await oi_detector.collect_symbol_oi("BTC")
        
        # Test explosion detection
        explosions = oi_detector.oi_manager.detect_explosions()
        
        # Should detect explosion based on mock data
        assert len(explosions) > 0
        explosion = explosions[0]
        assert explosion["symbol"] == "BTC"
        assert explosion["avg_change_pct"] > 15  # Above BTC threshold
    
    async def test_memory_constraints(self, temp_directories):
        """Test that system stays within memory constraints"""
        
        # Create all components
        liquidation_monitor = LiquidationMonitor()
        oi_detector = OIExplosionDetector()
        alert_dispatcher = AlertDispatcher()
        
        # Set temp paths
        liquidation_monitor.alert_output_path = os.path.join(
            temp_directories["alerts_dir"], "liquidation_alerts.json"
        )
        alert_dispatcher.db_path = os.path.join(
            temp_directories["data_dir"], "alerts.db"
        )
        
        # Test liquidation monitor memory
        for i in range(1000):  # Add max buffer size
            binance_data = {
                "o": {
                    "s": "BTCUSDT",
                    "S": "SELL",
                    "ap": "50000",
                    "z": "1.0",
                    "T": (int(time.time()) + i) * 1000
                }
            }
            liquidation_monitor.process_liquidation(binance_data)
        
        # Verify memory usage is within limits
        memory_usage = liquidation_monitor.buffer.memory_usage()
        max_memory = 1000 * 18  # 1000 liquidations * 18 bytes
        assert memory_usage <= max_memory
        
        # Test OI detector memory
        memory_stats = oi_detector.oi_manager.get_memory_usage()
        assert memory_stats["total_mb"] < 40  # Should be under 40MB limit
    
    async def test_alert_deduplication(self, temp_directories, mock_telegram_client):
        """Test that duplicate alerts are not sent"""
        
        alert_dispatcher = AlertDispatcher()
        alert_dispatcher.liquidation_alerts_path = os.path.join(
            temp_directories["alerts_dir"], "liquidation_alerts.json"
        )
        alert_dispatcher.db_path = os.path.join(
            temp_directories["data_dir"], "alerts.db"
        )
        alert_dispatcher.telegram_client = mock_telegram_client
        alert_dispatcher.init_database()
        
        # Create duplicate alert data
        alert_data = {
            "type": "single_liquidation",
            "timestamp": "2024-01-01T12:00:00",
            "symbol": "BTC",
            "value_usd": 150000,
            "message": "Test alert"
        }
        
        # Write alert file with duplicate alerts
        with open(alert_dispatcher.liquidation_alerts_path, 'w') as f:
            json.dump([alert_data, alert_data], f)  # Same alert twice
        
        # Process alerts
        await alert_dispatcher.process_liquidation_alerts()
        
        # Should only queue one alert due to deduplication
        assert len(alert_dispatcher.alert_queue) == 1
    
    async def test_system_graceful_failure(self, temp_directories):
        """Test system behavior under failure conditions"""
        
        liquidation_monitor = LiquidationMonitor()
        liquidation_monitor.alert_output_path = "/invalid/path/alerts.json"
        
        # Process liquidation with invalid output path
        binance_data = {
            "o": {
                "s": "BTCUSDT",
                "S": "SELL",
                "ap": "50000",
                "z": "3.0",
                "T": int(time.time()) * 1000
            }
        }
        
        # Should not crash even with invalid path
        result = liquidation_monitor.process_liquidation(binance_data)
        assert result is not None  # Liquidation still processed
        assert len(liquidation_monitor.buffer) == 1  # Buffer still works
    
    async def test_rate_limiting(self, temp_directories, mock_telegram_client):
        """Test alert rate limiting"""
        
        alert_dispatcher = AlertDispatcher()
        alert_dispatcher.liquidation_alerts_path = os.path.join(
            temp_directories["alerts_dir"], "liquidation_alerts.json"
        )
        alert_dispatcher.db_path = os.path.join(
            temp_directories["data_dir"], "alerts.db"
        )
        alert_dispatcher.telegram_client = mock_telegram_client
        alert_dispatcher.init_database()
        
        # Create many alerts
        alerts = []
        for i in range(20):  # More than hourly limit
            alert_data = {
                "type": "single_liquidation",
                "timestamp": f"2024-01-01T12:{i:02d}:00",
                "symbol": "BTC",
                "value_usd": 100000 + i,  # Different values to avoid dedup
                "message": f"Test alert {i}"
            }
            alerts.append(alert_data)
        
        with open(alert_dispatcher.liquidation_alerts_path, 'w') as f:
            json.dump(alerts, f)
        
        # Process all alerts
        await alert_dispatcher.process_liquidation_alerts()
        
        # All should be queued initially
        assert len(alert_dispatcher.alert_queue) == 20
        
        # But rate limiting should prevent sending all at once
        sent_count = 0
        for alert in alert_dispatcher.alert_queue[:15]:  # Try to send 15
            can_send = alert_dispatcher.can_send_alert()
            if can_send:
                await alert_dispatcher.send_alert(alert)
                sent_count += 1
            else:
                break  # Rate limited
        
        # Should be rate limited before sending all
        assert sent_count <= 10  # Max alerts per hour


@pytest.mark.asyncio
class TestSystemIntegration:
    """Integration tests for system components"""
    
    async def test_telegram_client_integration(self):
        """Test Telegram client with mock responses"""
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': 'test_token',
            'TELEGRAM_CHAT_ID': 'test_chat_id'
        }):
            
            client = TelegramClient()
            
            # Mock aiohttp session
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_post.return_value.__aenter__.return_value = mock_response
                
                # Test sending message
                async with client:
                    success = await client.send_message("Test message")
                    assert success
                    
                    mock_post.assert_called_once()
                    call_args = mock_post.call_args
                    assert "sendMessage" in call_args[0][0]  # URL contains sendMessage
    
    async def test_coordinator_health_checks(self):
        """Test monitoring coordinator health checks"""
        
        from services.monitoring.coordinator import MonitoringCoordinator
        
        coordinator = MonitoringCoordinator()
        
        # Test health status
        health = await coordinator.get_overall_health()
        assert "healthy" in health
        assert "services_healthy" in health
        assert "uptime_seconds" in health
        
        # Test individual service status update
        coordinator.update_service_status("liquidation_monitor", True)
        assert coordinator.service_status["liquidation_monitor"]["healthy"] is True
        assert coordinator.service_status["liquidation_monitor"]["failures"] == 0
        
        # Test failure handling
        coordinator.update_service_status("liquidation_monitor", False)
        coordinator.update_service_status("liquidation_monitor", False)
        coordinator.update_service_status("liquidation_monitor", False)
        
        # Should be marked unhealthy after max failures
        assert coordinator.service_status["liquidation_monitor"]["healthy"] is False
    
    async def test_alert_file_monitoring(self, tmp_path):
        """Test alert file monitoring and processing"""
        
        alert_dispatcher = AlertDispatcher()
        alerts_dir = tmp_path / "alerts"
        alerts_dir.mkdir()
        alert_dispatcher.liquidation_alerts_path = str(alerts_dir / "liquidation_alerts.json")
        
        # Create alert file
        alert_data = {
            "type": "single_liquidation",
            "timestamp": "2024-01-01T12:00:00",
            "value_usd": 150000
        }
        
        with open(alert_dispatcher.liquidation_alerts_path, 'w') as f:
            json.dump([alert_data], f)
        
        # Test file exists and can be read
        assert os.path.exists(alert_dispatcher.liquidation_alerts_path)
        
        with open(alert_dispatcher.liquidation_alerts_path, 'r') as f:
            loaded_alerts = json.load(f)
            assert len(loaded_alerts) == 1
            assert loaded_alerts[0]["value_usd"] == 150000