#!/usr/bin/env python3
"""
Forensic Analysis: Why are we not capturing Hyperliquid liquidations?
Checks multiple data sources to identify the issue
"""

import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime, timedelta

# HLP Liquidator address
HLP_LIQUIDATOR = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"

class HyperliquidForensics:
    def __init__(self):
        self.api_base = "https://api.hyperliquid.xyz"
        self.ws_url = "wss://api.hyperliquid.xyz/ws"
        self.trades_captured = 0
        self.liquidations_found = 0

    async def check_hlp_account_status(self):
        """Check if HLP liquidator account is active"""
        print("\n" + "="*60)
        print("1. CHECKING HLP LIQUIDATOR ACCOUNT STATUS")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # Check account state
            payload = {
                "type": "clearinghouseState",
                "user": HLP_LIQUIDATOR
            }

            async with session.post(f"{self.api_base}/info", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        print(f"✅ HLP Account is ACTIVE")
                        print(f"   Account Value: ${float(data.get('crossMarginSummary', {}).get('accountValue', 0)):,.0f}")
                        print(f"   Total Position: ${float(data.get('crossMarginSummary', {}).get('totalNtlPos', 0)):,.0f}")
                    else:
                        print(f"❌ HLP Account returned no data")
                else:
                    print(f"❌ Failed to check HLP account: HTTP {resp.status}")

    async def check_recent_fills(self):
        """Check HLP's recent trades to see if it's liquidating"""
        print("\n" + "="*60)
        print("2. CHECKING HLP RECENT LIQUIDATIONS (REST API)")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            payload = {
                "type": "userFills",
                "user": HLP_LIQUIDATOR
            }

            async with session.post(f"{self.api_base}/info", json=payload) as resp:
                if resp.status == 200:
                    fills = await resp.json()
                    if fills and len(fills) > 0:
                        print(f"✅ Found {len(fills)} recent HLP trades")

                        # Show last 5 liquidations
                        for i, fill in enumerate(fills[:5]):
                            timestamp = datetime.fromtimestamp(fill['time'] / 1000)
                            print(f"\n   Trade {i+1}:")
                            print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"   Coin: {fill.get('coin', 'N/A')}")
                            print(f"   Side: {fill.get('side', 'N/A')}")
                            print(f"   Price: ${float(fill.get('px', 0)):,.2f}")
                            print(f"   Size: {float(fill.get('sz', 0)):.6f}")
                            print(f"   Value: ${float(fill.get('px', 0)) * float(fill.get('sz', 0)):,.2f}")

                        # Check time of last liquidation
                        if fills:
                            last_time = datetime.fromtimestamp(fills[0]['time'] / 1000)
                            time_diff = datetime.now() - last_time
                            print(f"\n⏰ Last HLP liquidation: {time_diff.total_seconds():.0f} seconds ago")

                            if time_diff.total_seconds() > 3600:
                                print(f"⚠️ WARNING: No liquidations in the last hour!")
                    else:
                        print(f"❌ No recent HLP trades found")
                else:
                    print(f"❌ Failed to get fills: HTTP {resp.status}")

    async def test_websocket_trades(self, test_duration=30):
        """Connect to WebSocket and monitor raw trades"""
        print("\n" + "="*60)
        print(f"3. TESTING WEBSOCKET CONNECTION ({test_duration}s)")
        print("="*60)

        try:
            async with websockets.connect(self.ws_url) as ws:
                print(f"✅ Connected to WebSocket")

                # Subscribe to BTC trades
                subscribe = {
                    "method": "subscribe",
                    "subscription": {
                        "type": "trades",
                        "coin": "BTC"
                    }
                }
                await ws.send(json.dumps(subscribe))
                print(f"📡 Subscribed to BTC trades")

                start_time = time.time()
                hlp_trades = []

                while time.time() - start_time < test_duration:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)

                        if data.get('channel') == 'trades':
                            trades = data.get('data', [])
                            for trade in trades:
                                self.trades_captured += 1

                                # Check if HLP is involved
                                users = trade.get('users', [])
                                if len(users) >= 2:
                                    if HLP_LIQUIDATOR.lower() in [u.lower() for u in users]:
                                        self.liquidations_found += 1
                                        hlp_trades.append(trade)

                                        # Print liquidation found
                                        print(f"\n💥 LIQUIDATION FOUND!")
                                        print(f"   Coin: {trade.get('coin')}")
                                        print(f"   Price: ${float(trade.get('px', 0)):,.2f}")
                                        print(f"   Size: {float(trade.get('sz', 0)):.6f}")
                                        print(f"   Users: {users[0][:8]}... vs {users[1][:8]}...")

                                        # Determine side
                                        if users[0].lower() == HLP_LIQUIDATOR.lower():
                                            print(f"   HLP Position: BUYER → SHORT liquidation")
                                        else:
                                            print(f"   HLP Position: SELLER → LONG liquidation")

                                # Print progress every 100 trades
                                if self.trades_captured % 100 == 0:
                                    print(f"   Processed {self.trades_captured} trades, found {self.liquidations_found} liquidations...")

                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error processing message: {e}")

                print(f"\n📊 WebSocket Test Results:")
                print(f"   Duration: {test_duration}s")
                print(f"   Trades captured: {self.trades_captured}")
                print(f"   Liquidations found: {self.liquidations_found}")
                print(f"   Liquidation rate: {self.liquidations_found / max(self.trades_captured, 1) * 100:.2f}%")

                if self.liquidations_found == 0 and self.trades_captured > 0:
                    print(f"\n⚠️ WARNING: Captured {self.trades_captured} trades but ZERO liquidations!")
                    print(f"   Possible issues:")
                    print(f"   1. Low liquidation activity period")
                    print(f"   2. HLP address might have changed")
                    print(f"   3. Need to monitor more coins")

        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")

    async def check_all_coins_for_liquidations(self):
        """Check multiple coins for liquidation activity"""
        print("\n" + "="*60)
        print("4. CHECKING MULTIPLE COINS FOR LIQUIDATIONS")
        print("="*60)

        coins = ["BTC", "ETH", "SOL", "ARB", "PEPE", "WIF", "ENA", "DOGE"]
        total_liquidations = 0

        try:
            async with websockets.connect(self.ws_url) as ws:
                print(f"✅ Connected to WebSocket")

                # Subscribe to multiple coins
                for coin in coins:
                    subscribe = {
                        "method": "subscribe",
                        "subscription": {
                            "type": "trades",
                            "coin": coin
                        }
                    }
                    await ws.send(json.dumps(subscribe))
                    await asyncio.sleep(0.1)

                print(f"📡 Subscribed to {len(coins)} coins: {', '.join(coins)}")
                print(f"⏳ Monitoring for 20 seconds...")

                coin_stats = {coin: {'trades': 0, 'liquidations': 0} for coin in coins}
                start_time = time.time()

                while time.time() - start_time < 20:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)

                        if data.get('channel') == 'trades':
                            trades = data.get('data', [])
                            for trade in trades:
                                coin = trade.get('coin', '')
                                if coin in coin_stats:
                                    coin_stats[coin]['trades'] += 1

                                users = trade.get('users', [])
                                if len(users) >= 2 and HLP_LIQUIDATOR.lower() in [u.lower() for u in users]:
                                    coin_stats[coin]['liquidations'] += 1
                                    total_liquidations += 1
                                    print(f"   💥 {coin} liquidation at ${float(trade.get('px', 0)):,.2f}")

                    except asyncio.TimeoutError:
                        continue

                print(f"\n📊 Multi-Coin Results:")
                for coin, stats in coin_stats.items():
                    if stats['trades'] > 0:
                        print(f"   {coin}: {stats['trades']} trades, {stats['liquidations']} liquidations")

                print(f"\n   Total liquidations across all coins: {total_liquidations}")

                if total_liquidations == 0:
                    print(f"\n⚠️ NO LIQUIDATIONS FOUND ACROSS ANY COINS!")
                    print(f"   This suggests either:")
                    print(f"   1. Market is very quiet (unlikely for all coins)")
                    print(f"   2. HLP address has changed")
                    print(f"   3. Detection logic issue")

        except Exception as e:
            print(f"❌ Multi-coin check failed: {e}")

    async def verify_hlp_address(self):
        """Verify if the HLP address is still the correct liquidator"""
        print("\n" + "="*60)
        print("5. VERIFYING HLP ADDRESS IS CORRECT")
        print("="*60)

        print(f"Current HLP address: {HLP_LIQUIDATOR}")

        # Check if this address appears in recent large trades
        async with aiohttp.ClientSession() as session:
            # Get recent large trades
            payload = {
                "type": "metaAndAssetCtxs"
            }

            async with session.post(f"{self.api_base}/info", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Connected to Hyperliquid API")

                    # The HLP vault info might be in the meta
                    meta = data[0] if isinstance(data, list) else data

                    # Print protocol info
                    if 'universe' in meta:
                        print(f"   Total tradeable assets: {len(meta['universe'])}")

        print(f"\n💡 To verify HLP address:")
        print(f"   1. Check Hyperliquid Discord/Twitter for updates")
        print(f"   2. Look for 'HLP Liquidator' in official docs")
        print(f"   3. Monitor large trades for patterns")

    async def run_all_checks(self):
        """Run all forensic checks"""
        print("\n" + "🔍 "*20)
        print("HYPERLIQUID LIQUIDATION FORENSIC ANALYSIS")
        print("🔍 "*20)

        # 1. Check HLP account
        await self.check_hlp_account_status()

        # 2. Check recent fills
        await self.check_recent_fills()

        # 3. Test WebSocket
        await self.test_websocket_trades(30)

        # 4. Check multiple coins
        await self.check_all_coins_for_liquidations()

        # 5. Verify address
        await self.verify_hlp_address()

        # Summary
        print("\n" + "="*60)
        print("FORENSIC SUMMARY")
        print("="*60)

        if self.liquidations_found == 0:
            print("❌ CRITICAL: No liquidations captured!")
            print("\nRecommended Actions:")
            print("1. Check if HLP address has changed")
            print("2. Monitor during high volatility periods")
            print("3. Expand coin monitoring list")
            print("4. Check Hyperliquid official channels for updates")
        else:
            print(f"✅ Found {self.liquidations_found} liquidations")
            print(f"   Capture rate: {self.liquidations_found}/{self.trades_captured} trades")


async def main():
    forensics = HyperliquidForensics()
    await forensics.run_all_checks()


if __name__ == "__main__":
    asyncio.run(main())