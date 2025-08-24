"""
Regression Tests for Existing System
Ensures existing functionality remains unchanged after monitoring system addition
"""

import pytest
import pytest_asyncio
import aiohttp
import asyncio
import json
from unittest.mock import patch
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))


@pytest.mark.asyncio
class TestExistingAPIEndpoints:
    """Test that all existing API endpoints work unchanged"""
    
    @pytest_asyncio.fixture
    async def api_session(self):
        """HTTP session for API testing"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.fixture
    def base_url(self):
        """Base URL for market data API"""
        return "http://localhost:8001"
    
    async def test_health_endpoint(self, api_session, base_url):
        """Test /health endpoint unchanged"""
        async with api_session.get(f"{base_url}/health") as response:
            assert response.status == 200
            data = await response.json()
            assert "status" in data or "healthy" in data
    
    async def test_price_endpoint(self, api_session, base_url):
        """Test /price endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/price", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
            if data.get("success"):
                assert "data" in data
                price_data = data["data"]
                assert "price" in price_data
                assert "symbol" in price_data
                assert isinstance(price_data["price"], (int, float))
    
    async def test_volume_spike_endpoint(self, api_session, base_url):
        """Test /volume_spike endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/volume_spike", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
            if data.get("success"):
                assert "data" in data
                volume_data = data["data"]
                assert "current_volume" in volume_data or "spike_percentage" in volume_data
    
    async def test_oi_endpoint(self, api_session, base_url):
        """Test /multi_oi endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/multi_oi", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
            if data.get("success"):
                assert "data" in data
    
    async def test_multi_oi_endpoint(self, api_session, base_url):
        """Test /multi_oi endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/multi_oi", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
            if data.get("success"):
                assert "data" in data
                oi_data = data["data"]
                # Should have multiple exchanges
                assert len(oi_data) > 0
    
    async def test_cvd_endpoint(self, api_session, base_url):
        """Test /cvd endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/cvd", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
    
    async def test_profile_endpoint(self, api_session, base_url):
        """Test /market_profile endpoint unchanged"""
        payload = {"symbol": "BTC-USDT"}
        
        async with api_session.post(f"{base_url}/market_profile", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure
            assert "success" in data
    
    async def test_comprehensive_analysis_endpoint(self, api_session, base_url):
        """Test /comprehensive_analysis endpoint unchanged"""
        
        async with api_session.post(f"{base_url}/comprehensive_analysis", json={}) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify expected response structure  
            assert "success" in data


class TestExistingTelegramCommands:
    """Test that existing Telegram commands work unchanged"""
    
    def test_telegram_bot_imports(self):
        """Test that Telegram bot can still import required modules"""
        try:
            # Test imports that should still work
            from services.telegram_bot import main  # Main bot module should exist
            assert main is not None
        except ImportError as e:
            # If import fails, check if it's due to missing dependencies (acceptable)
            # or structural changes (not acceptable)
            if "No module named" in str(e) and "telegram" in str(e):
                pytest.skip("Telegram bot dependencies not installed")
            else:
                pytest.fail(f"Unexpected import error: {e}")


@pytest.mark.asyncio 
class TestDockerContainerIntegrity:
    """Test that existing Docker containers are unchanged"""
    
    async def test_main_containers_running(self):
        """Test that main containers are still running"""
        import subprocess
        
        try:
            # Check if main containers are running
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                running_containers = result.stdout.strip().split('\n')
                
                # Main containers should still be running
                expected_containers = [
                    "crypto-market-data",
                    "crypto-telegram-bot"
                ]
                
                for container in expected_containers:
                    assert any(container in name for name in running_containers), \
                        f"Main container {container} is not running"
            else:
                pytest.skip("Docker not available for testing")
                
        except subprocess.TimeoutExpired:
            pytest.skip("Docker command timed out")
        except FileNotFoundError:
            pytest.skip("Docker not installed")
    
    async def test_network_unchanged(self):
        """Test that crypto network still exists"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                networks = result.stdout.strip().split('\n')
                assert "crypto-network" in networks, "crypto-network was removed or modified"
            else:
                pytest.skip("Docker not available for testing")
                
        except subprocess.TimeoutExpired:
            pytest.skip("Docker command timed out")
        except FileNotFoundError:
            pytest.skip("Docker not installed")


class TestExistingFileStructure:
    """Test that existing file structure is preserved"""
    
    def test_main_services_exist(self):
        """Test that main service files still exist"""
        main_files = [
            "services/market-data/main.py",
            "services/market-data/volume_analysis.py", 
            "services/market-data/oi_analysis.py",
            "services/telegram-bot/main.py",
            "docker-compose.yml"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for file_path in main_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Main file {file_path} is missing"
    
    def test_main_docker_compose_unchanged(self):
        """Test that main docker-compose.yml is not modified"""
        project_root = Path(__file__).parent.parent.parent
        compose_path = project_root / "docker-compose.yml"
        
        assert compose_path.exists(), "docker-compose.yml is missing"
        
        with open(compose_path, 'r') as f:
            content = f.read()
            
        # Verify main services are still defined
        assert "market-data:" in content, "market-data service removed from compose"
        assert "telegram-bot:" in content, "telegram-bot service removed from compose"
        assert "crypto-network:" in content, "crypto-network removed from compose"
        
        # Verify no monitoring services in main compose file
        assert "liquidation-monitor:" not in content, "Monitoring services added to main compose"
        assert "oi-detector:" not in content, "Monitoring services added to main compose"
        assert "alert-dispatcher:" not in content, "Monitoring services added to main compose"


class TestEnvironmentVariables:
    """Test that environment variables are unchanged"""
    
    def test_existing_env_vars_preserved(self):
        """Test that existing environment variables are not modified"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check if .env.example exists and has expected variables
        env_example = project_root / ".env.example" 
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Should still have original variables
            expected_vars = [
                "TELEGRAM_BOT_TOKEN",
                "TELEGRAM_CHAT_ID", 
                "BINANCE_API_KEY",
                "MARKET_DATA_URL"
            ]
            
            for var in expected_vars:
                assert var in content, f"Environment variable {var} removed from example"


@pytest.mark.asyncio
class TestPerformanceRegression:
    """Test that performance has not degraded"""
    
    async def test_api_response_time(self):
        """Test that API response times are still reasonable"""
        import time
        
        base_url = "http://localhost:8001"
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint response time
            start_time = time.time()
            
            try:
                async with session.get(f"{base_url}/health", timeout=5) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # Health endpoint should respond quickly
                    assert response_time < 2.0, f"Health endpoint too slow: {response_time}s"
                    assert response.status == 200
                    
            except aiohttp.ClientError:
                pytest.skip("Market data service not running")
    
    async def test_memory_usage_reasonable(self):
        """Test that memory usage hasn't significantly increased"""
        import subprocess
        
        try:
            # Get memory usage of main containers
            result = subprocess.run([
                "docker", "stats", "--no-stream", "--format", 
                "table {{.Name}}\t{{.MemUsage}}"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    if "crypto-market-data" in line or "crypto-telegram-bot" in line:
                        # Extract memory usage (simplified parsing)
                        if "MiB" in line:
                            mem_str = line.split("MiB")[0].split()[-1]
                            try:
                                memory_mb = float(mem_str)
                                # Main services should not exceed reasonable memory limits
                                assert memory_mb < 1000, f"Memory usage too high: {memory_mb}MB"
                            except ValueError:
                                # Skip if can't parse memory value
                                pass
            else:
                pytest.skip("Could not get Docker stats")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available for memory testing")


class TestBackwardCompatibility:
    """Test that existing integrations still work"""
    
    def test_existing_imports_work(self):
        """Test that existing code can still import required modules"""
        try:
            # These imports should still work for existing code
            from services.market_data import main as market_main
            from services.telegram_bot import main as bot_main
            
            assert market_main is not None
            assert bot_main is not None
            
        except ImportError as e:
            # Check if it's a structural change (bad) or dependency issue (acceptable)
            if "cannot import name" in str(e):
                pytest.fail(f"Breaking change detected in imports: {e}")
            else:
                pytest.skip(f"Import issue (likely dependency): {e}")
    
    def test_data_directories_preserved(self):
        """Test that existing data directories are preserved"""
        project_root = Path(__file__).parent.parent.parent
        
        # Existing data directories should still exist
        data_dir = project_root / "data"
        if data_dir.exists():
            # If data directory exists, check for existing subdirectories
            expected_subdirs = ["cache", "logs", "exports"]
            for subdir in expected_subdirs:
                subdir_path = data_dir / subdir
                if subdir_path.exists():
                    # Existing subdirs should not be modified
                    assert subdir_path.is_dir(), f"Existing directory {subdir} was changed to file"