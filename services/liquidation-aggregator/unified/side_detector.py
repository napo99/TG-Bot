"""
Unified Side Detection Module
Correctly detects liquidation side for all exchanges
"""

from typing import Dict, Optional
from enum import Enum


class LiquidationSide(Enum):
    """Liquidation side enumeration"""
    LONG = "LONG"
    SHORT = "SHORT"


class UnifiedSideDetector:
    """
    Universal side detector that handles the different logic per exchange

    IMPORTANT: Each exchange has different conventions:
    - CEX (Binance/Bybit): Order side indicates what the liquidated user was forced to do
    - OKX: Position side directly indicates what position was liquidated
    - Hyperliquid: Must check liquidator position in users array
    """

    # Known liquidator addresses for DEX
    HYPERLIQUID_LIQUIDATOR = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"

    @classmethod
    def detect(cls, exchange: str, data: Dict) -> Optional[LiquidationSide]:
        """
        Detect liquidation side based on exchange-specific logic

        Args:
            exchange: Exchange name (binance, bybit, okx, hyperliquid)
            data: Raw trade/liquidation data from exchange

        Returns:
            LiquidationSide or None if not a liquidation
        """

        exchange = exchange.lower()

        if exchange == 'binance':
            return cls._detect_binance(data)
        elif exchange == 'bybit':
            return cls._detect_bybit(data)
        elif exchange == 'okx':
            return cls._detect_okx(data)
        elif exchange == 'hyperliquid':
            return cls._detect_hyperliquid(data)
        else:
            print(f"Warning: Unknown exchange {exchange}")
            return None

    @classmethod
    def _detect_binance(cls, data: Dict) -> Optional[LiquidationSide]:
        """
        Binance liquidation side detection

        Logic:
        - SELL order = LONG liquidation (user forced to sell their longs)
        - BUY order = SHORT liquidation (user forced to buy to cover shorts)
        """
        order = data.get('o', data)  # Handle both wrapped and unwrapped
        side = order.get('S', '')

        if side == 'SELL':
            return LiquidationSide.LONG
        elif side == 'BUY':
            return LiquidationSide.SHORT

        return None

    @classmethod
    def _detect_bybit(cls, data: Dict) -> Optional[LiquidationSide]:
        """
        Bybit liquidation side detection

        Logic:
        - Sell = LONG liquidation (forced sell of long position)
        - Buy = SHORT liquidation (forced buy to close short)
        """
        # Handle nested data structure
        liq_data = data.get('data', data)
        side = liq_data.get('side', '')

        if side == 'Sell':
            return LiquidationSide.LONG
        elif side == 'Buy':
            return LiquidationSide.SHORT

        return None

    @classmethod
    def _detect_okx(cls, data: Dict) -> Optional[LiquidationSide]:
        """
        OKX liquidation side detection

        Logic:
        - posSide='long' = LONG liquidation
        - posSide='short' = SHORT liquidation

        OKX directly tells us the position side being liquidated
        """
        # OKX may have details in array
        details = data.get('details', [data])

        for detail in details if isinstance(details, list) else [details]:
            pos_side = detail.get('posSide', '')

            if pos_side == 'long':
                return LiquidationSide.LONG
            elif pos_side == 'short':
                return LiquidationSide.SHORT

        return None

    @classmethod
    def _detect_hyperliquid(cls, data: Dict) -> Optional[LiquidationSide]:
        """
        Hyperliquid liquidation side detection

        Logic (CORRECTED):
        - HLP is buyer (users[0]) = SHORT liquidation (buying to close shorts)
        - HLP is seller (users[1]) = LONG liquidation (selling to close longs)

        This is based on the HLP liquidator's role in the trade
        """
        users = data.get('users', [])

        if not users or len(users) < 2:
            return None

        buyer = users[0].lower()
        seller = users[1].lower()
        liquidator = cls.HYPERLIQUID_LIQUIDATOR.lower()

        # Check if HLP is involved
        if buyer == liquidator:
            # HLP is buying = closing someone's short position
            return LiquidationSide.SHORT
        elif seller == liquidator:
            # HLP is selling = closing someone's long position
            return LiquidationSide.LONG

        # Not a liquidation (HLP not involved)
        return None

    @classmethod
    def get_liquidated_user(cls, exchange: str, data: Dict) -> Optional[str]:
        """
        Get the liquidated user address/ID if available

        Args:
            exchange: Exchange name
            data: Raw trade data

        Returns:
            User address/ID or None
        """

        if exchange.lower() == 'hyperliquid':
            users = data.get('users', [])
            if len(users) >= 2:
                buyer = users[0].lower()
                liquidator = cls.HYPERLIQUID_LIQUIDATOR.lower()

                # Return the non-liquidator user
                if buyer == liquidator:
                    return users[1]  # Seller was liquidated
                else:
                    return users[0]  # Buyer was liquidated

        # CEX typically don't provide user info
        return None


# =============================================================================
# TEST SUITE
# =============================================================================

def test_side_detection():
    """Test side detection for all exchanges"""

    print("Testing Unified Side Detection...")
    print("="*50)

    test_cases = [
        # Binance
        {
            'exchange': 'binance',
            'data': {'o': {'S': 'SELL'}},
            'expected': LiquidationSide.LONG,
            'description': 'Binance SELL = LONG liquidation'
        },
        {
            'exchange': 'binance',
            'data': {'o': {'S': 'BUY'}},
            'expected': LiquidationSide.SHORT,
            'description': 'Binance BUY = SHORT liquidation'
        },

        # Bybit
        {
            'exchange': 'bybit',
            'data': {'data': {'side': 'Sell'}},
            'expected': LiquidationSide.LONG,
            'description': 'Bybit Sell = LONG liquidation'
        },
        {
            'exchange': 'bybit',
            'data': {'data': {'side': 'Buy'}},
            'expected': LiquidationSide.SHORT,
            'description': 'Bybit Buy = SHORT liquidation'
        },

        # OKX
        {
            'exchange': 'okx',
            'data': {'posSide': 'long'},
            'expected': LiquidationSide.LONG,
            'description': 'OKX long position = LONG liquidation'
        },
        {
            'exchange': 'okx',
            'data': {'posSide': 'short'},
            'expected': LiquidationSide.SHORT,
            'description': 'OKX short position = SHORT liquidation'
        },

        # Hyperliquid
        {
            'exchange': 'hyperliquid',
            'data': {
                'users': [
                    '0x2e3d94f0562703b25c83308a05046ddaf9a8dd14',  # HLP buyer
                    '0xuser123'
                ]
            },
            'expected': LiquidationSide.SHORT,
            'description': 'Hyperliquid HLP buyer = SHORT liquidation'
        },
        {
            'exchange': 'hyperliquid',
            'data': {
                'users': [
                    '0xuser456',
                    '0x2e3d94f0562703b25c83308a05046ddaf9a8dd14'  # HLP seller
                ]
            },
            'expected': LiquidationSide.LONG,
            'description': 'Hyperliquid HLP seller = LONG liquidation'
        }
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        result = UnifiedSideDetector.detect(test['exchange'], test['data'])

        if result == test['expected']:
            print(f"✅ PASS: {test['description']}")
            passed += 1
        else:
            print(f"❌ FAIL: {test['description']}")
            print(f"   Expected: {test['expected']}, Got: {result}")
            failed += 1

    print("="*50)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = test_side_detection()

    if success:
        print("\n✅ All side detection tests passed!")
    else:
        print("\n❌ Some tests failed, check implementation")