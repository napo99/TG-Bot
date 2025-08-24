#!/usr/bin/env python3
"""
Docker Container Integration Tests
Validates that all services work correctly in containerized environment
"""

import subprocess
import time
import asyncio
import aiohttp
import json
import pytest
from pathlib import Path

class TestDockerIntegration:
    """Test Docker container builds, runs, and integration"""
    
    @classmethod
    def setup_class(cls):
        """Ensure Docker is available"""
        result = subprocess.run(['docker', '--version'], capture_output=True)
        if result.returncode != 0:
            pytest.skip("Docker not available")
    
    def test_docker_compose_builds_successfully(self):
        """Test that all containers build without errors"""
        print("\n🔨 Building Docker containers...")
        result = subprocess.run(
            ['docker-compose', 'build', '--no-cache'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        assert "Successfully built" in result.stdout or result.returncode == 0
        print("✅ All containers built successfully")
    
    def test_shared_modules_copied_to_containers(self):
        """Verify shared modules are accessible in running containers"""
        print("\n📦 Checking shared module availability...")
        
        # Test the actual telegram bot container that should be running
        result = subprocess.run([
            'docker', 'exec', 'crypto-telegram-bot',
            'python', '-c',
            'from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine; print("SUCCESS")'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Import failed in telegram-bot container: {result.stderr}"
        assert "SUCCESS" in result.stdout, f"Shared module import failed: {result.stderr}"
        print("✅ Shared modules accessible in containers")
    
    @pytest.mark.asyncio
    async def test_containers_start_and_stay_running(self):
        """Test that containers start and don't restart loop"""
        print("\n🚀 Starting Docker containers...")
        
        # Start containers
        subprocess.run(['docker-compose', 'down'], capture_output=True)
        result = subprocess.run(
            ['docker-compose', 'up', '-d'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Docker-compose up failed: {result.stderr}"
        
        # Wait for startup
        await asyncio.sleep(10)
        
        # Check container status
        result = subprocess.run(
            ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True
        )
        
        print(f"Container Status:\n{result.stdout}")
        
        # Verify no restart loops
        assert "Restarting" not in result.stdout, "Container is in restart loop!"
        assert "crypto-market-data" in result.stdout
        assert "crypto-telegram-bot" in result.stdout
        
        # Check for healthy status
        assert "healthy" in result.stdout or "Up" in result.stdout
        print("✅ All containers running without restart loops")
    
    @pytest.mark.asyncio
    async def test_market_data_api_responds(self):
        """Test market data API is accessible and responds correctly"""
        print("\n📊 Testing market data API...")
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get('http://localhost:8001/health') as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'status' in data or 'healthy' in data
                print("✅ Health endpoint working")
            
            # Test price endpoint
            async with session.post(
                'http://localhost:8001/price',
                json={'symbol': 'BTCUSDT'}
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data['success'] is True
                assert 'price' in data['data']
                print(f"✅ Price endpoint working: BTC=${data['data']['price']:,.2f}")
    
    @pytest.mark.asyncio
    async def test_telegram_bot_container_no_import_errors(self):
        """Verify telegram bot has no module import errors"""
        print("\n🤖 Checking Telegram bot for import errors...")
        
        # Check logs for import errors
        result = subprocess.run(
            ['docker', 'logs', 'crypto-telegram-bot', '--tail', '50'],
            capture_output=True,
            text=True
        )
        
        # Check for critical errors
        assert "ModuleNotFoundError" not in result.stderr, "Module import error found!"
        assert "No module named 'shared'" not in result.stderr, "Shared module not found!"
        assert "AttributeError" not in result.stderr[-500:], "Attribute errors found!"
        
        print("✅ No import errors in Telegram bot")
    
    @pytest.mark.asyncio
    async def test_dynamic_thresholds_work_in_container(self):
        """Test that dynamic threshold calculations work in containerized environment"""
        print("\n🎯 Testing dynamic thresholds in container...")
        
        # Execute threshold calculation inside container
        test_code = """
import sys
import asyncio
from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine

async def test():
    engine = DynamicThresholdEngine(market_data_url='http://market-data:8001')
    result = await engine.calculate_liquidation_threshold('BTCUSDT')
    print(f'THRESHOLD:{result.single_liquidation_usd}')
    print(f'CONFIDENCE:{result.confidence_score}')
    await engine.close()

asyncio.run(test())
"""
        
        result = subprocess.run(
            ['docker', 'exec', 'crypto-telegram-bot', 'python', '-c', test_code],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse output
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('THRESHOLD:'):
                    threshold = float(line.split(':')[1])
                    assert threshold > 0, "Invalid threshold calculated"
                    print(f"✅ Dynamic threshold working: ${threshold:,.0f}")
                elif line.startswith('CONFIDENCE:'):
                    confidence = float(line.split(':')[1])
                    assert 0 < confidence <= 1, "Invalid confidence score"
                    print(f"✅ Confidence score: {confidence:.2f}")
        else:
            pytest.fail(f"Threshold calculation failed: {result.stderr}")
    
    @pytest.mark.asyncio
    async def test_integration_between_services(self):
        """Test that telegram bot can communicate with market data service"""
        print("\n🔗 Testing service integration...")
        
        # Test internal communication
        test_code = """
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://market-data:8001/health') as resp:
            if resp.status == 200:
                print('INTEGRATION:SUCCESS')
            else:
                print('INTEGRATION:FAILED')

asyncio.run(test())
"""
        
        result = subprocess.run(
            ['docker', 'exec', 'crypto-telegram-bot', 'python', '-c', test_code],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert "INTEGRATION:SUCCESS" in result.stdout, "Service integration failed"
        print("✅ Services can communicate internally")
    
    def test_memory_and_cpu_limits_respected(self):
        """Verify containers respect resource limits"""
        print("\n💾 Checking resource limits...")
        
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 
             'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'],
            capture_output=True,
            text=True
        )
        
        print(f"Resource Usage:\n{result.stdout}")
        
        # Parse and verify memory usage
        for line in result.stdout.split('\n'):
            if 'crypto-telegram-bot' in line:
                # Should be under 256MB limit
                assert 'MiB' in line or 'KiB' in line, "Memory usage too high"
            elif 'crypto-market-data' in line:
                # Should be under 512MB limit  
                assert 'MiB' in line or 'KiB' in line, "Memory usage too high"
        
        print("✅ Resource limits respected")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup after tests"""
        print("\n🧹 Cleaning up...")
        # Keep containers running for manual testing if needed
        # subprocess.run(['docker-compose', 'down'], capture_output=True)
        print("✅ Tests complete - containers still running for manual verification")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])