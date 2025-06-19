#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/screener-m3/projects/crypto-assistant/services/market-data')

import asyncio
from main import MarketDataService

async def debug_technical():
    service = MarketDataService()
    await service.initialize()
    
    try:
        # Test technical indicators directly
        tech_indicators = await service.technical_service.get_technical_indicators("SOL/USDT", "15m", "binance_futures")
        
        print("🔍 Technical Indicators Debug:")
        print(f"Symbol: {tech_indicators.symbol}")
        print(f"Timeframe: {tech_indicators.timeframe}")
        print(f"RSI: {tech_indicators.rsi_14}")
        print(f"VWAP: {tech_indicators.vwap}")
        print(f"ATR: {tech_indicators.atr_14}")
        print(f"Volatility 24h: {tech_indicators.volatility_24h}")
        print(f"Volatility 15m: {tech_indicators.volatility_15m}")
        print(f"ATR USD: {tech_indicators.atr_usd}")
        print(f"Current Price: {tech_indicators.current_price}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_technical())