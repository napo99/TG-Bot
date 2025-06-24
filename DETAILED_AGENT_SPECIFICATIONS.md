# ULTRA-DETAILED AGENT SPECIFICATIONS - OI Analysis System

## CRITICAL: EXACT OUTPUT FORMAT REQUIREMENT

Every agent MUST understand this is the **EXACT** target output format:

### INPUT COMMAND:
```
/oi btc
```

### IMMEDIATE ACKNOWLEDGMENT:
```
🔍 Analyzing Open Interest for BTC across USDT + USDC markets...
```

### EXACT TARGET OUTPUT FORMAT:
```
📊 OPEN INTEREST ANALYSIS - BTC

🔢 MARKET TYPE BREAKDOWN:
• Total OI: 322,011 BTC ($32.7B)
• Stablecoin-Margined: $27.7B | 84.9%
  - USDT: $26.8B (82.1%)
  - USDC: $0.9B (2.8%)
• Coin-Margined (Inverse): $4.9B | 15.1%
  - USD: $4.9B (15.1%)

🔢 STABLECOIN MARKETS (84.9%): $27.7B
🔢 INVERSE MARKETS (15.1%): $4.9B
📊 COMBINED TOTAL: $32.7B

📈 TOP MARKETS:
1. Binance USDT: 78,278 BTC ($7.9B) | 24.3% STABLE
   Funding: +0.0050% | Vol: 223K BTC
2. Gate USDT: 60,353 BTC ($6.1B) | 18.7% STABLE
   Funding: +0.0000% | Vol: 869675K BTC
[... continues for all 13 markets, ranked by USD value DESC]

🏢 COVERAGE SUMMARY:
• Exchanges: 5 working
• Markets: 13 total
• Phase 2A: USDT + USDC support

🚨 MARKET ANALYSIS:
• Sentiment: NEUTRAL ⚪➡️
• Risk Level: NORMAL
• Coverage: Multi-stablecoin across 5 exchanges

🕐 15:57:29 UTC / 23:57:29 SGT
```

---

## AGENT 1: BINANCE OI SPECIALIST

**WORKSPACE:** `../crypto-assistant-oi`
**RESPONSIBILITY:** Binance futures OI data collection for ANY crypto asset

### CRITICAL REQUIREMENTS:

1. **API ENDPOINTS TO IMPLEMENT:**
   ```python
   # Binance Futures OI Endpoints
   BINANCE_FUTURES_OI = "https://fapi.binance.com/fapi/v1/openInterest"
   BINANCE_DELIVERY_OI = "https://dapi.binance.com/dapi/v1/openInterest"
   
   # Required for each symbol:
   # - BTCUSDT (linear/stablecoin-margined)
   # - BTCUSDC (linear/stablecoin-margined)  
   # - BTCUSD_PERP (inverse/coin-margined)
   ```

2. **DATA STRUCTURE TO RETURN:**
   ```python
   {
       "exchange": "binance",
       "symbol": "BTC",
       "markets": {
           "USDT": {
               "type": "linear",
               "category": "STABLE",
               "oi_tokens": 78278.0,  # Native BTC amount
               "oi_usd": 7900000000.0,  # USD equivalent
               "funding_rate": 0.0050,  # As decimal
               "volume_tokens": 223000.0,  # 24h volume in BTC
               "symbol_exchange": "BTCUSDT"
           },
           "USDC": {
               "type": "linear", 
               "category": "STABLE",
               "oi_tokens": 6377.0,
               "oi_usd": 600000000.0,
               "funding_rate": 0.0013,
               "volume_tokens": 34000.0,
               "symbol_exchange": "BTCUSDC"
           },
           "USD": {
               "type": "inverse",
               "category": "INVERSE", 
               "oi_tokens": 21949.0,
               "oi_usd": 2200000000.0,
               "funding_rate": 0.0026,
               "volume_tokens": 23219000.0,
               "symbol_exchange": "BTCUSD_PERP"
           }
       }
   }
   ```

3. **VALIDATION RULES:**
   - `oi_tokens * current_price ≈ oi_usd` (within 2% tolerance)
   - Funding rates between -0.1% and +0.1%
   - OI values > 0 (never negative or null)
   - Volume values realistic vs OI ratios

4. **ERROR HANDLING:**
   - If USDC market doesn't exist, return 0 values
   - If API fails, return None for that market
   - If symbol not supported, return empty markets dict

5. **SYMBOL FLEXIBILITY:**
   - Input: "BTC", "ETH", "SOL", "ADA", etc.
   - Auto-generate: BTCUSDT, ETHUSDT, SOLUSDT, etc.
   - Handle case insensitivity

---

## AGENT 2: BYBIT OI SPECIALIST

**WORKSPACE:** `../crypto-assistant-perf`
**RESPONSIBILITY:** Bybit futures OI data collection for ANY crypto asset

### CRITICAL REQUIREMENTS:

1. **API ENDPOINTS TO IMPLEMENT:**
   ```python
   # Bybit V5 API
   BYBIT_OI_URL = "https://api.bybit.com/v5/market/open-interest"
   
   # Categories to handle:
   # - linear (USDT/USDC-margined)
   # - inverse (coin-margined) ← CRITICAL FIX AREA
   ```

2. **BYBIT-SPECIFIC SYMBOL MAPPING:**
   ```python
   def get_bybit_symbols(base_symbol: str):
       return {
           "linear_usdt": f"{base_symbol}USDT",     # BTCUSDT
           "linear_usdc": f"{base_symbol}USDC",     # BTCUSDC  
           "inverse": f"{base_symbol}USD"           # BTCUSD (coin-margined)
       }
   ```

3. **CRITICAL INVERSE CONTRACT HANDLING:**
   ```python
   # For inverse contracts (coin-margined):
   # Bybit returns openInterestValue (USD) and openInterest (contracts)
   # IMPORTANT: Use openInterestValue directly for USD amount
   # Calculate BTC tokens = openInterestValue / current_btc_price
   
   if category == "inverse":
       oi_usd = response["openInterestValue"]  # Use direct USD value
       oi_tokens = oi_usd / current_price      # Calculate tokens from USD
   ```

4. **TARGET BYBIT DATA (BTC Example):**
   ```python
   {
       "exchange": "bybit",
       "symbol": "BTC", 
       "markets": {
           "USDT": {
               "oi_tokens": 53689.0,    # ~$5.4B
               "oi_usd": 5400000000.0,
               "funding_rate": -0.0036,
               "volume_tokens": 127000.0
           },
           "USDC": {
               "oi_tokens": 1257.0,     # ~$0.1B
               "oi_usd": 100000000.0,
               "funding_rate": -0.0017,
               "volume_tokens": 813.0
           },
           "USD": {
               "oi_tokens": 15000.0,    # ~$1.5B (NOT 0!)
               "oi_usd": 1500000000.0,
               "funding_rate": 0.0000,
               "volume_tokens": 767476.0
           }
       }
   }
   ```

5. **CRITICAL SUCCESS CRITERIA:**
   - Bybit USD MUST show >10,000 BTC (not 0)
   - All three markets (USDT, USDC, USD) working
   - Inverse contract math verified

---

## AGENT 3: DATA VALIDATION SPECIALIST

**WORKSPACE:** `../crypto-assistant-symbols`
**RESPONSIBILITY:** Cross-exchange validation and mathematical verification

### CRITICAL REQUIREMENTS:

1. **VALIDATION FRAMEWORK:**
   ```python
   class OIValidator:
       def validate_exchange_data(self, exchange_data):
           # Math validation
           for market in exchange_data["markets"].values():
               calculated_usd = market["oi_tokens"] * current_price
               api_usd = market["oi_usd"]
               variance = abs(calculated_usd - api_usd) / api_usd
               assert variance < 0.02, f"Math error: {variance:.1%} variance"
           
           # Range validation
           assert market["funding_rate"] >= -0.001, "Funding rate too negative"
           assert market["funding_rate"] <= 0.001, "Funding rate too positive"
           assert market["oi_tokens"] > 0, "OI cannot be zero or negative"
   ```

2. **CROSS-EXCHANGE VALIDATION:**
   ```python
   def validate_cross_exchange(self, all_exchange_data):
       # Total OI should be reasonable
       total_oi_usd = sum(all USD values across all exchanges)
       assert 20e9 < total_oi_usd < 50e9, f"Total OI unrealistic: ${total_oi_usd/1e9:.1f}B"
       
       # Stablecoin vs Inverse ratio
       stable_pct = stablecoin_usd / total_oi_usd * 100
       assert 70 < stable_pct < 95, f"Stablecoin % unrealistic: {stable_pct:.1f}%"
   ```

3. **DATA QUALITY CHECKS:**
   - No exchange shows 0 for all markets
   - Funding rates within realistic ranges
   - Volume vs OI ratios make sense
   - Symbol mapping consistency

---

## AGENT 4: INTEGRATION & BOT SPECIALIST

**WORKSPACE:** `../crypto-assistant-testing`
**RESPONSIBILITY:** Complete /oi command implementation with exact output format

### CRITICAL REQUIREMENTS:

1. **BOT COMMAND IMPLEMENTATION:**
   ```python
   @bot.message_handler(commands=['oi'])
   def handle_oi_command(message):
       try:
           # Parse symbol
           parts = message.text.split()
           symbol = parts[1].upper() if len(parts) > 1 else "BTC"
           
           # Send acknowledgment
           bot.send_message(message.chat.id, 
               f"🔍 Analyzing Open Interest for {symbol} across USDT + USDC markets...")
           
           # Get data from market-data service
           response = requests.post(
               'http://localhost:8001/oi_analysis',
               json={'symbol': symbol}
           )
           
           # Format and send result
           formatted_message = format_oi_analysis(response.json(), symbol)
           bot.send_message(message.chat.id, formatted_message)
           
       except Exception as e:
           bot.send_message(message.chat.id, f"❌ Error analyzing OI for {symbol}: {str(e)}")
   ```

2. **EXACT FORMATTING IMPLEMENTATION:**
   ```python
   def format_oi_analysis(data, symbol):
       # Calculate totals
       total_oi_tokens = sum(all native token amounts)
       total_oi_usd = sum(all USD amounts)
       
       # Calculate percentages
       stable_usd = sum(USDT + USDC markets)
       inverse_usd = sum(USD markets)
       stable_pct = stable_usd / total_oi_usd * 100
       inverse_pct = inverse_usd / total_oi_usd * 100
       
       # Create ranking
       all_markets = []
       for exchange in data:
           for market_type, market_data in exchange["markets"].items():
               all_markets.append({
                   "name": f"{exchange['exchange'].title()} {market_type}",
                   "oi_tokens": market_data["oi_tokens"],
                   "oi_usd": market_data["oi_usd"],
                   "percentage": market_data["oi_usd"] / total_oi_usd * 100,
                   "category": market_data["category"],
                   "funding": market_data["funding_rate"],
                   "volume": market_data["volume_tokens"]
               })
       
       # Sort by USD value descending
       all_markets.sort(key=lambda x: x["oi_usd"], reverse=True)
       
       # Format exact output
       message = f"""📊 OPEN INTEREST ANALYSIS - {symbol}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${stable_usd/1e9:.1f}B | {stable_pct:.1f}%
• Coin-Margined (Inverse): ${inverse_usd/1e9:.1f}B | {inverse_pct:.1f}%

📈 TOP MARKETS:"""
       
       # Add each market
       for i, market in enumerate(all_markets, 1):
           message += f"\n{i}. {market['name']}: {market['oi_tokens']:,.0f} {symbol} (${market['oi_usd']/1e9:.1f}B) | {market['percentage']:.1f}% {market['category']}"
           message += f"\n   Funding: {market['funding']:+.4f}% | Vol: {format_volume(market['volume'])} {symbol}"
       
       # Add timestamp
       utc_time = datetime.utcnow().strftime("%H:%M:%S")
       sgt_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%H:%M:%S")
       message += f"\n\n🕐 {utc_time} UTC / {sgt_time} SGT"
       
       return message
   ```

3. **CRITICAL OUTPUT REQUIREMENTS:**
   - **EXACT** emoji usage: 📊 🔢 📈 🏢 🚨 🕐
   - **EXACT** number formatting: 322,011 BTC ($32.7B)
   - **EXACT** percentage formatting: 84.9%
   - **EXACT** funding rate formatting: +0.0050%
   - **EXACT** volume formatting: 223K BTC
   - **EXACT** timestamp formatting: UTC / SGT
   - **EXACT** ranking by USD value (descending)
   - **EXACT** market categorization: STABLE vs INVERSE

4. **ERROR HANDLING:**
   - Unsupported symbol: "❌ {symbol} futures not supported"
   - API failure: "❌ Unable to fetch OI data, please try again"
   - Partial data: Show available exchanges, note missing ones

---

## CRITICAL SUCCESS CRITERIA FOR ALL AGENTS:

1. **Data Accuracy:**
   - Bybit USD shows >10,000 BTC (not 0)
   - Math validation: tokens * price ≈ USD value
   - Realistic total OI (~20-50B USD range)

2. **Output Format:**
   - **EXACTLY** matches the target template
   - All 13 markets ranked by USD value
   - Proper percentage calculations
   - Correct emoji and formatting

3. **Symbol Flexibility:**
   - Works with ANY crypto: /oi btc, /oi eth, /oi sol
   - Proper symbol mapping across exchanges
   - Case insensitive input handling

4. **Performance:**
   - Response time <5 seconds
   - Graceful error handling
   - Partial data support (some exchanges down)

5. **Validation:**
   - No 0 or negative OI values
   - Funding rates within realistic ranges
   - Cross-exchange data consistency

**Each agent MUST implement their piece to contribute to this EXACT target output format.**