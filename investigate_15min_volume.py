#!/usr/bin/env python3
"""
15-Minute Volume Data Investigation for BTC
Comprehensive analysis of volume patterns across timeframes
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VolumeData:
    """Data structure for volume analysis"""
    symbol: str
    timeframe: str
    exchange: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    volume_usd: float
    quote_volume: float

@dataclass
class VolumeComparison:
    """Comparison between different volume metrics"""
    symbol: str
    spot_15m_volume: float
    spot_15m_volume_usd: float
    futures_15m_volume: float
    futures_15m_volume_usd: float
    total_15m_volume_usd: float
    volume_ratio_spot_futures: float
    avg_15m_volume_theoretical: float
    current_vs_avg_ratio: float
    volume_pattern: str

class BinanceVolumeInvestigator:
    """Investigate volume patterns across Binance APIs"""
    
    def __init__(self):
        self.session = None
        self.spot_base_url = "https://api.binance.com/api/v3"
        self.futures_base_url = "https://fapi.binance.com/fapi/v1"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_spot_klines(self, symbol: str, interval: str = "15m", limit: int = 1) -> List[VolumeData]:
        """Fetch spot kline data from Binance"""
        url = f"{self.spot_base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_klines(data, symbol, interval, "spot")
                else:
                    logger.error(f"Spot API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching spot data: {e}")
            return []
    
    async def fetch_futures_klines(self, symbol: str, interval: str = "15m", limit: int = 1) -> List[VolumeData]:
        """Fetch futures kline data from Binance"""
        url = f"{self.futures_base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_klines(data, symbol, interval, "futures")
                else:
                    logger.error(f"Futures API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching futures data: {e}")
            return []
    
    async def fetch_spot_24h_ticker(self, symbol: str) -> Dict:
        """Fetch 24h ticker data from Binance Spot"""
        url = f"{self.spot_base_url}/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Spot 24h ticker API error: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching spot 24h ticker: {e}")
            return {}
    
    async def fetch_futures_24h_ticker(self, symbol: str) -> Dict:
        """Fetch 24h ticker data from Binance Futures"""
        url = f"{self.futures_base_url}/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Futures 24h ticker API error: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching futures 24h ticker: {e}")
            return {}
    
    async def fetch_multiple_15m_candles(self, symbol: str, limit: int = 96) -> Tuple[List[VolumeData], List[VolumeData]]:
        """Fetch multiple 15m candles for average calculation"""
        spot_data = await self.fetch_spot_klines(symbol, "15m", limit)
        futures_data = await self.fetch_futures_klines(symbol, "15m", limit)
        return spot_data, futures_data
    
    def _parse_klines(self, data: List, symbol: str, interval: str, exchange: str) -> List[VolumeData]:
        """Parse kline data into VolumeData objects"""
        volume_data = []
        
        for kline in data:
            timestamp = datetime.fromtimestamp(kline[0] / 1000)
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            quote_volume = float(kline[7])
            
            # Calculate USD volume
            volume_usd = volume * close_price
            
            volume_data.append(VolumeData(
                symbol=symbol,
                timeframe=interval,
                exchange=exchange,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                volume_usd=volume_usd,
                quote_volume=quote_volume
            ))
        
        return volume_data
    
    async def comprehensive_volume_analysis(self, symbol: str = "BTCUSDT") -> VolumeComparison:
        """Perform comprehensive volume analysis"""
        logger.info(f"🔍 Starting comprehensive volume analysis for {symbol}")
        
        # Fetch current 15m data
        spot_15m_current = await self.fetch_spot_klines(symbol, "15m", 1)
        futures_15m_current = await self.fetch_futures_klines(symbol, "15m", 1)
        
        # Fetch 24h ticker data
        spot_24h = await self.fetch_spot_24h_ticker(symbol)
        futures_24h = await self.fetch_futures_24h_ticker(symbol)
        
        # Fetch historical 15m data for averaging (96 candles = 24h)
        spot_15m_historical, futures_15m_historical = await self.fetch_multiple_15m_candles(symbol, 96)
        
        # Extract current volumes
        spot_15m_vol = spot_15m_current[0].volume if spot_15m_current else 0
        spot_15m_vol_usd = spot_15m_current[0].volume_usd if spot_15m_current else 0
        
        futures_15m_vol = futures_15m_current[0].volume if futures_15m_current else 0
        futures_15m_vol_usd = futures_15m_current[0].volume_usd if futures_15m_current else 0
        
        # Calculate 24h volumes
        spot_24h_vol = float(spot_24h.get('volume', 0))
        futures_24h_vol = float(futures_24h.get('volume', 0))
        
        # Calculate average 15m volume from historical data
        avg_spot_15m = sum(v.volume for v in spot_15m_historical) / len(spot_15m_historical) if spot_15m_historical else 0
        avg_futures_15m = sum(v.volume for v in futures_15m_historical) / len(futures_15m_historical) if futures_15m_historical else 0
        
        # Calculate theoretical average (24h / 96)
        theoretical_avg_spot = spot_24h_vol / 96 if spot_24h_vol > 0 else 0
        theoretical_avg_futures = futures_24h_vol / 96 if futures_24h_vol > 0 else 0
        
        # Calculate ratios
        total_15m_vol_usd = spot_15m_vol_usd + futures_15m_vol_usd
        volume_ratio = (spot_15m_vol_usd / futures_15m_vol_usd) if futures_15m_vol_usd > 0 else 0
        
        # Current vs average ratio
        current_vs_avg_spot = spot_15m_vol / avg_spot_15m if avg_spot_15m > 0 else 0
        current_vs_avg_futures = futures_15m_vol / avg_futures_15m if avg_futures_15m > 0 else 0
        
        # Determine volume pattern
        if current_vs_avg_spot > 2.0 or current_vs_avg_futures > 2.0:
            pattern = "HIGH_VOLUME"
        elif current_vs_avg_spot < 0.5 or current_vs_avg_futures < 0.5:
            pattern = "LOW_VOLUME"
        else:
            pattern = "NORMAL_VOLUME"
        
        return VolumeComparison(
            symbol=symbol,
            spot_15m_volume=spot_15m_vol,
            spot_15m_volume_usd=spot_15m_vol_usd,
            futures_15m_volume=futures_15m_vol,
            futures_15m_volume_usd=futures_15m_vol_usd,
            total_15m_volume_usd=total_15m_vol_usd,
            volume_ratio_spot_futures=volume_ratio,
            avg_15m_volume_theoretical=theoretical_avg_spot + theoretical_avg_futures,
            current_vs_avg_ratio=(current_vs_avg_spot + current_vs_avg_futures) / 2,
            volume_pattern=pattern
        )
    
    async def test_crypto_assistant_endpoints(self) -> Dict:
        """Test if crypto assistant has 15m volume endpoints"""
        test_results = {}
        
        # Test endpoints that might exist
        endpoints_to_test = [
            "http://localhost:8001/volume_spike",
            "http://localhost:8001/comprehensive_analysis",
            "http://localhost:8001/debug_tickers"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                payload = {
                    "symbol": "BTC/USDT",
                    "timeframe": "15m"
                }
                
                async with self.session.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        test_results[endpoint] = {
                            "status": "success",
                            "data": data
                        }
                    else:
                        test_results[endpoint] = {
                            "status": "error",
                            "code": response.status
                        }
            except Exception as e:
                test_results[endpoint] = {
                    "status": "connection_error",
                    "error": str(e)
                }
        
        return test_results

async def main():
    """Main investigation function"""
    print("🚀 Starting 15-Minute Volume Data Investigation for BTC")
    print("=" * 60)
    
    async with BinanceVolumeInvestigator() as investigator:
        # 1. Comprehensive volume analysis
        print("\n📊 1. COMPREHENSIVE VOLUME ANALYSIS")
        print("-" * 40)
        
        volume_comparison = await investigator.comprehensive_volume_analysis()
        
        print(f"Symbol: {volume_comparison.symbol}")
        print(f"Current 15m Spot Volume: {volume_comparison.spot_15m_volume:,.0f} BTC")
        print(f"Current 15m Spot Volume (USD): ${volume_comparison.spot_15m_volume_usd:,.0f}")
        print(f"Current 15m Futures Volume: {volume_comparison.futures_15m_volume:,.0f} BTC")
        print(f"Current 15m Futures Volume (USD): ${volume_comparison.futures_15m_volume_usd:,.0f}")
        print(f"Total 15m Volume (USD): ${volume_comparison.total_15m_volume_usd:,.0f}")
        print(f"Spot/Futures Ratio: {volume_comparison.volume_ratio_spot_futures:.2f}")
        print(f"Current vs Average Ratio: {volume_comparison.current_vs_avg_ratio:.2f}")
        print(f"Volume Pattern: {volume_comparison.volume_pattern}")
        
        # 2. Raw API response analysis
        print("\n🔍 2. RAW API RESPONSES")
        print("-" * 40)
        
        # Spot 15m data
        spot_data = await investigator.fetch_spot_klines("BTCUSDT", "15m", 1)
        if spot_data:
            print("SPOT 15m Kline Data:")
            print(f"  Timestamp: {spot_data[0].timestamp}")
            print(f"  Open: ${spot_data[0].open_price:,.2f}")
            print(f"  High: ${spot_data[0].high_price:,.2f}")
            print(f"  Low: ${spot_data[0].low_price:,.2f}")
            print(f"  Close: ${spot_data[0].close_price:,.2f}")
            print(f"  Volume: {spot_data[0].volume:,.4f} BTC")
            print(f"  Quote Volume: {spot_data[0].quote_volume:,.2f} USDT")
            print(f"  Volume USD: ${spot_data[0].volume_usd:,.0f}")
        
        # Futures 15m data
        futures_data = await investigator.fetch_futures_klines("BTCUSDT", "15m", 1)
        if futures_data:
            print("\nFUTURES 15m Kline Data:")
            print(f"  Timestamp: {futures_data[0].timestamp}")
            print(f"  Open: ${futures_data[0].open_price:,.2f}")
            print(f"  High: ${futures_data[0].high_price:,.2f}")
            print(f"  Low: ${futures_data[0].low_price:,.2f}")
            print(f"  Close: ${futures_data[0].close_price:,.2f}")
            print(f"  Volume: {futures_data[0].volume:,.4f} BTC")
            print(f"  Quote Volume: {futures_data[0].quote_volume:,.2f} USDT")
            print(f"  Volume USD: ${futures_data[0].volume_usd:,.0f}")
        
        # 3. 24h comparison
        print("\n📈 3. 24H VOLUME COMPARISON")
        print("-" * 40)
        
        spot_24h = await investigator.fetch_spot_24h_ticker("BTCUSDT")
        futures_24h = await investigator.fetch_futures_24h_ticker("BTCUSDT")
        
        if spot_24h:
            spot_24h_vol = float(spot_24h.get('volume', 0))
            spot_24h_quote_vol = float(spot_24h.get('quoteVolume', 0))
            print(f"Spot 24h Volume: {spot_24h_vol:,.2f} BTC")
            print(f"Spot 24h Quote Volume: ${spot_24h_quote_vol:,.0f}")
            print(f"Theoretical Spot 15m Average: {spot_24h_vol/96:,.2f} BTC")
            if spot_data:
                print(f"Current vs Theoretical Average: {(spot_data[0].volume / (spot_24h_vol/96)):.2f}x")
        
        if futures_24h:
            futures_24h_vol = float(futures_24h.get('volume', 0))
            futures_24h_quote_vol = float(futures_24h.get('quoteVolume', 0))
            print(f"Futures 24h Volume: {futures_24h_vol:,.2f} BTC")
            print(f"Futures 24h Quote Volume: ${futures_24h_quote_vol:,.0f}")
            print(f"Theoretical Futures 15m Average: {futures_24h_vol/96:,.2f} BTC")
            if futures_data:
                print(f"Current vs Theoretical Average: {(futures_data[0].volume / (futures_24h_vol/96)):.2f}x")
        
        # 4. Volume pattern analysis
        print("\n🎯 4. VOLUME PATTERN ANALYSIS")
        print("-" * 40)
        
        if spot_data and futures_data:
            total_15m_btc = spot_data[0].volume + futures_data[0].volume
            total_15m_usd = spot_data[0].volume_usd + futures_data[0].volume_usd
            
            print(f"Combined 15m Volume: {total_15m_btc:,.4f} BTC")
            print(f"Combined 15m Volume (USD): ${total_15m_usd:,.0f}")
            
            if spot_24h and futures_24h:
                total_24h_btc = float(spot_24h.get('volume', 0)) + float(futures_24h.get('volume', 0))
                theoretical_avg = total_24h_btc / 96
                
                print(f"24h Total Volume: {total_24h_btc:,.2f} BTC")
                print(f"Theoretical 15m Average: {theoretical_avg:,.2f} BTC")
                print(f"Current vs Average: {(total_15m_btc / theoretical_avg):.2f}x")
                
                if (total_15m_btc / theoretical_avg) > 2.0:
                    print("🔥 HIGH VOLUME DETECTED!")
                elif (total_15m_btc / theoretical_avg) < 0.5:
                    print("😴 LOW VOLUME DETECTED")
                else:
                    print("📊 NORMAL VOLUME RANGE")
        
        # 5. Test crypto assistant endpoints
        print("\n🤖 5. CRYPTO ASSISTANT ENDPOINT TESTING")
        print("-" * 40)
        
        endpoint_results = await investigator.test_crypto_assistant_endpoints()
        for endpoint, result in endpoint_results.items():
            print(f"Endpoint: {endpoint}")
            print(f"  Status: {result['status']}")
            if result['status'] == 'success' and 'data' in result:
                # Show relevant volume data if available
                data = result['data']
                if 'data' in data and 'volume_analysis' in data['data']:
                    vol_analysis = data['data']['volume_analysis']
                    print(f"  Volume Analysis Available: Yes")
                    print(f"  Current Volume: {vol_analysis.get('current_volume', 'N/A')}")
                    print(f"  Volume USD: ${vol_analysis.get('volume_usd', 0):,.0f}")
                    print(f"  Spike Level: {vol_analysis.get('spike_level', 'N/A')}")
                else:
                    print(f"  Volume Analysis Available: No")
            print()
        
        # 6. Summary and recommendations
        print("\n📋 6. SUMMARY AND RECOMMENDATIONS")
        print("-" * 40)
        
        print("Key Findings:")
        print(f"• Current 15m volume is {volume_comparison.current_vs_avg_ratio:.1f}x the average")
        print(f"• Pattern classification: {volume_comparison.volume_pattern}")
        print(f"• Spot/Futures volume ratio: {volume_comparison.volume_ratio_spot_futures:.2f}")
        print(f"• Total 15m volume: ${volume_comparison.total_15m_volume_usd:,.0f}")
        
        print("\nRecommendations for volume analysis:")
        print("• Use 96 candles (24h) for 15m average calculation")
        print("• Monitor both spot and futures volumes")
        print("• Consider volume spikes above 2x average as significant")
        print("• Track volume patterns for better context")
        
        print("\n✅ Investigation Complete!")

if __name__ == "__main__":
    asyncio.run(main())