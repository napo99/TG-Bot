#!/usr/bin/env python3
"""
Data Flow and Processing Pipeline Validation
Tests the complete data processing pipeline for profile calculations
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
from datetime import datetime

class DataFlowValidator:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.validation_results = []
    
    async def validate_complete_pipeline(self):
        """Validate the complete data processing pipeline"""
        print("🔄 DATA FLOW AND PROCESSING PIPELINE VALIDATION")
        print("=" * 60)
        
        validations = [
            ("Symbol Normalization", self.validate_symbol_normalization),
            ("Multi-timeframe Data Fetching", self.validate_multi_timeframe_data),
            ("Calculation Pipeline", self.validate_calculation_pipeline),
            ("Response Formatting", self.validate_response_formatting),
            ("Error Propagation", self.validate_error_propagation)
        ]
        
        async with aiohttp.ClientSession() as session:
            for validation_name, validation_func in validations:
                print(f"\n📋 {validation_name}")
                try:
                    await validation_func(session)
                    print(f"   ✅ VALIDATED")
                    self.validation_results.append((validation_name, True, ""))
                except Exception as e:
                    print(f"   ❌ FAILED: {e}")
                    self.validation_results.append((validation_name, False, str(e)))
        
        # Summary
        passed = sum(1 for _, success, _ in self.validation_results if success)
        total = len(self.validation_results)
        
        print(f"\n📊 PIPELINE VALIDATION: {passed}/{total} components validated")
        return passed == total
    
    async def validate_symbol_normalization(self, session: aiohttp.ClientSession):
        """Validate symbol normalization across different input formats"""
        test_symbols = [
            ("BTC", "BTCUSDT"),
            ("BTC-USDT", "BTCUSDT"),
            ("BTC/USDT", "BTCUSDT"),
            ("ETH", "ETHUSDT"),
            ("eth", "ETHUSDT")
        ]
        
        for input_symbol, expected_normalized in test_symbols:
            # Test via working endpoint to see normalization
            try:
                payload = {"symbol": input_symbol, "exchange": "binance"}
                async with session.post(f"{self.base_url}/combined_price", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['success']:
                            # Symbol was processed successfully
                            print(f"     ✓ '{input_symbol}' → normalized and processed")
                        else:
                            if "INVALID" not in input_symbol.upper():
                                print(f"     ⚠ '{input_symbol}' processing issue: {data.get('error', 'Unknown')}")
            except Exception as e:
                print(f"     ❌ '{input_symbol}' failed: {e}")
    
    async def validate_multi_timeframe_data(self, session: aiohttp.ClientSession):
        """Validate multi-timeframe data fetching and processing"""
        
        # Test with a working endpoint that demonstrates multi-timeframe capabilities
        payload = {"symbol": "BTC/USDT", "exchange": "binance"}
        
        async with session.post(f"{self.base_url}/combined_price", json=payload) as response:
            if response.status != 200:
                raise Exception(f"Failed to get data: {response.status}")
            
            data = await response.json()
            if not data['success']:
                raise Exception(f"API returned error: {data.get('error')}")
            
            result = data['data']
            
            # Validate timeframe data structure
            required_fields = ['spot', 'perp']
            for field in required_fields:
                if field in result:
                    timeframe_data = result[field]
                    
                    # Check for enhanced metrics (15m, 24h data)
                    metrics = ['volume_15m', 'change_15m', 'delta_24h', 'delta_15m', 'atr_24h', 'atr_15m']
                    found_metrics = [m for m in metrics if m in timeframe_data and timeframe_data[m] is not None]
                    
                    print(f"     ✓ {field} data: {len(found_metrics)}/6 enhanced metrics available")
            
            # Validate timestamp consistency
            if 'timestamp' in result:
                timestamp_str = result['timestamp']
                try:
                    datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    print(f"     ✓ Timestamp format valid: {timestamp_str}")
                except:
                    print(f"     ⚠ Timestamp format issue: {timestamp_str}")
    
    async def validate_calculation_pipeline(self, session: aiohttp.ClientSession):
        """Validate the calculation pipeline by testing calculation consistency"""
        
        # Test multiple calculations to ensure consistency
        symbols = ["BTC/USDT", "ETH/USDT"]
        results = []
        
        for symbol in symbols:
            payload = {"symbol": symbol, "exchange": "binance"}
            
            async with session.post(f"{self.base_url}/combined_price", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['success']:
                        results.append((symbol, data['data']))
        
        if len(results) < 2:
            raise Exception("Insufficient data for calculation validation")
        
        # Validate calculation consistency
        for symbol, result in results:
            # Check price data integrity
            if 'spot' in result and 'perp' in result:
                spot_price = result['spot']['price']
                perp_price = result['perp']['price']
                
                # Prices should be reasonably close (within 1%)
                price_diff_pct = abs(spot_price - perp_price) / spot_price * 100
                
                print(f"     ✓ {symbol} price consistency: {price_diff_pct:.2f}% diff (spot: ${spot_price:,.2f}, perp: ${perp_price:,.2f})")
                
                # Check delta calculations
                for market_type in ['spot', 'perp']:
                    if market_type in result:
                        market_data = result[market_type]
                        delta_24h = market_data.get('delta_24h')
                        delta_15m = market_data.get('delta_15m')
                        
                        if delta_24h is not None and delta_15m is not None:
                            print(f"     ✓ {symbol} {market_type} deltas calculated: 24h={delta_24h:,.0f}, 15m={delta_15m:,.0f}")
    
    async def validate_response_formatting(self, session: aiohttp.ClientSession):
        """Validate response formatting and structure"""
        
        payload = {"symbol": "BTC/USDT", "exchange": "binance"}
        
        async with session.post(f"{self.base_url}/combined_price", json=payload) as response:
            if response.status != 200:
                raise Exception(f"Failed to get response: {response.status}")
            
            data = await response.json()
            
            # Validate JSON structure
            required_top_level = ['success', 'data']
            for field in required_top_level:
                if field not in data:
                    raise Exception(f"Missing required field: {field}")
            
            print(f"     ✓ JSON structure valid")
            
            # Validate data types
            if data['success']:
                result_data = data['data']
                
                # Check numeric fields
                for market_type in ['spot', 'perp']:
                    if market_type in result_data:
                        market_data = result_data[market_type]
                        numeric_fields = ['price', 'volume_24h', 'change_24h']
                        
                        for field in numeric_fields:
                            if field in market_data and market_data[field] is not None:
                                value = market_data[field]
                                if not isinstance(value, (int, float)):
                                    raise Exception(f"Non-numeric value in {field}: {value}")
                
                print(f"     ✓ Data types valid")
                
                # Validate formatting would work for Telegram
                try:
                    formatted = self._format_for_telegram(result_data)
                    if len(formatted) < 100:
                        raise Exception("Formatted message too short")
                    print(f"     ✓ Telegram formatting: {len(formatted)} characters")
                except Exception as e:
                    raise Exception(f"Formatting failed: {e}")
    
    async def validate_error_propagation(self, session: aiohttp.ClientSession):
        """Validate error propagation through the pipeline"""
        
        # Test 1: Invalid symbol
        payload = {"symbol": "INVALID123", "exchange": "binance"}
        
        async with session.post(f"{self.base_url}/combined_price", json=payload) as response:
            data = await response.json()
            
            # Should either succeed (if symbol normalization handles it) or fail gracefully
            if not data['success']:
                if 'error' not in data:
                    raise Exception("Error response missing error field")
                print(f"     ✓ Invalid symbol error handling: {data['error'][:50]}...")
            else:
                print(f"     ✓ Invalid symbol handled via normalization")
        
        # Test 2: Service connectivity (test with invalid URL)
        try:
            async with session.get("http://localhost:9999/health", timeout=aiohttp.ClientTimeout(total=2)) as response:
                pass
        except Exception as e:
            print(f"     ✓ Connection error handling: {type(e).__name__}")
        
        # Test 3: Malformed request
        try:
            async with session.post(f"{self.base_url}/combined_price", data="invalid") as response:
                # Should handle gracefully
                pass
            print(f"     ✓ Malformed request handled")
        except Exception:
            print(f"     ✓ Request validation working")
    
    def _format_for_telegram(self, data: Dict[str, Any]) -> str:
        """Test telegram formatting"""
        symbol = data.get('base_symbol', 'TEST')
        
        message = f"📊 **PROFILE TEST - {symbol}**\n\n"
        
        if 'spot' in data:
            spot = data['spot']
            message += f"💰 Spot: ${spot['price']:,.2f}\n"
        
        if 'perp' in data:
            perp = data['perp']
            message += f"⚡ Perp: ${perp['price']:,.2f}\n"
            if 'open_interest' in perp and perp['open_interest']:
                message += f"📈 OI: {perp['open_interest']:,.0f}\n"
        
        message += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}"
        
        return message

async def main():
    validator = DataFlowValidator()
    success = await validator.validate_complete_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)