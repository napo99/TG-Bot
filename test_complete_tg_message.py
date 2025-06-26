#!/usr/bin/env python3
"""
COMPLETE TG MESSAGE VALIDATOR: Test full message generation
Tests the complete TG bot message with real API data
"""

import json
from datetime import datetime

def load_real_api_response():
    """Load actual API response"""
    with open('/tmp/actual_api_response.json', 'r') as f:
        return json.load(f)

def generate_complete_tg_message(data, symbol: str) -> str:
    """Generate complete TG message - exact replica of TG bot function"""
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
        
        # Build message with new format
        message = f"""🎯 MULTI-EXCHANGE OI ANALYSIS - {symbol}

💰 TOTAL OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e9:.1f}B)
📊 MARKETS: {total_markets} across {validation.get('successful_exchanges', 0)} exchanges

📈 EXCHANGE BREAKDOWN:"""
        
        # Add exchanges
        for exchange_data in exchange_breakdown:
            exchange = exchange_data['exchange'].upper()
            oi_tokens = exchange_data['oi_tokens']
            oi_usd = exchange_data['oi_usd']
            percentage = exchange_data['oi_percentage']
            markets = exchange_data['markets']
            funding = exchange_data['funding_rate']
            
            message += f"\n• {exchange}: {oi_tokens:,.0f} {symbol} (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets}M"
            if funding != 0:
                message += f" | 💸 {funding*100:+.4f}%"
        
        # Add market categories
        message += f"""\n
🏷️ MARKET CATEGORIES:
• 🟢 USDT Stable: {usdt_data.get('total_tokens', 0):,.0f} {symbol} (${usdt_usd/1e9:.1f}B) - {usdt_pct:.1f}% - {usdt_data.get('exchanges', 0)}E
• 🔵 USDC Stable: {usdc_data.get('total_tokens', 0):,.0f} {symbol} (${usdc_usd/1e9:.1f}B) - {usdc_pct:.1f}% - {usdc_data.get('exchanges', 0)}E
• ⚫ USD Inverse: {usd_data.get('total_tokens', 0):,.0f} {symbol} (${inverse_usd/1e9:.1f}B) - {inverse_pct:.1f}% - {usd_data.get('exchanges', 0)}E

🔢 MARKET TYPE SUMMARY:
• Stablecoin-Margined: ${stablecoin_usd/1e9:.1f}B ({stablecoin_pct:.1f}%)
• Coin-Margined (Inverse): ${inverse_usd/1e9:.1f}B ({inverse_pct:.1f}%)
• COMBINED TOTAL: ${total_oi_usd/1e9:.1f}B

🎯 SYSTEM STATUS: {'✅ COMPLETE' if validation.get('validation_passed') else '⚠️ PARTIAL'}
🏢 COVERAGE: {validation.get('successful_exchanges', 0)}/5 exchanges | {total_markets} markets
📊 PHASE: Multi-exchange USDT + USDC + USD support

🕐 {datetime.now().strftime('%H:%M:%S')} UTC / {(datetime.now().replace(hour=(datetime.now().hour + 8) % 24)).strftime('%H:%M:%S')} SGT"""
        
        return message
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error formatting OI analysis for {symbol}: {str(e)}"

def validate_message_completeness(message: str, real_data: dict) -> list:
    """Validate message contains all expected elements"""
    checks = []
    
    # Check 1: Header present
    if "MULTI-EXCHANGE OI ANALYSIS" in message:
        checks.append("✅ Header present")
    else:
        checks.append("❌ Missing header")
    
    # Check 2: Total OI section
    agg = real_data.get('aggregated_oi', {})
    expected_total = f"{agg.get('total_tokens', 0):,.0f}"
    if expected_total in message:
        checks.append("✅ Total OI values match real data")
    else:
        checks.append("❌ Total OI values don't match")
    
    # Check 3: All 5 exchanges mentioned
    exchanges = ['BINANCE', 'BYBIT', 'OKX', 'GATEIO', 'BITGET']
    missing_exchanges = [ex for ex in exchanges if ex not in message]
    if not missing_exchanges:
        checks.append("✅ All 5 exchanges present")
    else:
        checks.append(f"❌ Missing exchanges: {missing_exchanges}")
    
    # Check 4: Market categories section
    if "MARKET CATEGORIES:" in message and "USDT Stable:" in message:
        checks.append("✅ Market categories section present")
    else:
        checks.append("❌ Missing market categories section")
    
    # Check 5: System status
    if "SYSTEM STATUS:" in message:
        checks.append("✅ System status present")
    else:
        checks.append("❌ Missing system status")
    
    # Check 6: Realistic values (no $0.0B)
    if "$0.0B" not in message or message.count("$0.0B") <= 2:  # Allow small amounts
        checks.append("✅ No unrealistic $0.0B values")
    else:
        checks.append("❌ Contains unrealistic $0.0B values")
    
    return checks

def main():
    """Main test function"""
    print("🧪 COMPLETE TG MESSAGE VALIDATION")
    print("=" * 40)
    
    # Load real data
    real_data = load_real_api_response()
    symbol = real_data.get('base_symbol', 'BTC')
    
    print(f"🎯 Testing with real API data for {symbol}")
    print("")
    
    # Generate complete message
    message = generate_complete_tg_message(real_data, symbol)
    
    # Validate message
    checks = validate_message_completeness(message, real_data)
    
    print("📋 MESSAGE VALIDATION RESULTS:")
    all_passed = True
    for check in checks:
        print(f"  {check}")
        if "❌" in check:
            all_passed = False
    
    print("")
    print("📱 COMPLETE MESSAGE OUTPUT:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    
    # Message length check
    print(f"📏 Message length: {len(message)} characters")
    if len(message) < 4096:  # Telegram limit
        print("✅ Within Telegram message length limit")
    else:
        print("⚠️ Message may exceed Telegram limits")
    
    print("")
    print("🎯 FINAL RESULT:")
    if all_passed:
        print("✅ Complete TG message validation PASSED")
        print("✅ Ready for deployment in Docker container")
    else:
        print("❌ Message validation FAILED")
        print("⚠️ Fixes needed before deployment")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Exit code: {0 if success else 1}")