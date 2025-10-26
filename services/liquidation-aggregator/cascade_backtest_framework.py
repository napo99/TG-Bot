"""
Cascade Detection Backtesting Framework
Validate our detection algorithms against historical cascade events
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import asyncpg
import pandas as pd
import numpy as np
from collections import defaultdict

from professional_cascade_detector import ProfessionalCascadeDetector, CascadeSignal
from market_data_aggregator import MarketDataAggregator, MarketContext


@dataclass
class CascadeEvent:
    """Known historical cascade event for validation"""
    timestamp: float
    event_name: str
    severity: str  # minor, moderate, major, extreme
    duration_seconds: int
    total_liquidations: float
    price_drop_pct: float
    exchanges_affected: List[str]
    notes: str


@dataclass
class BacktestResult:
    """Results from backtesting cascade detection"""
    # Detection metrics
    true_positives: int = 0      # Correctly detected cascades
    false_positives: int = 0     # False alarms
    false_negatives: int = 0     # Missed cascades
    true_negatives: int = 0      # Correctly identified calm periods

    # Timing metrics
    avg_detection_lag_ms: float = 0.0   # How fast we detect
    fastest_detection_ms: float = 0.0
    slowest_detection_ms: float = 0.0

    # Severity accuracy
    severity_accuracy: float = 0.0      # How well we gauge severity

    # Performance metrics
    precision: float = 0.0    # TP / (TP + FP)
    recall: float = 0.0       # TP / (TP + FN)
    f1_score: float = 0.0     # Harmonic mean of precision and recall

    # Trading metrics (what really matters)
    profit_factor: float = 0.0          # Gross profit / Gross loss
    sharpe_ratio: float = 0.0           # Risk-adjusted returns
    max_drawdown_pct: float = 0.0       # Worst peak-to-trough
    win_rate: float = 0.0                # Profitable trades %


class CascadeBacktester:
    """
    Backtest cascade detection against known historical events
    This validates if our detection actually works!
    """

    def __init__(self):
        self.detector = ProfessionalCascadeDetector()
        self.aggregator = MarketDataAggregator()

        # Known cascade events (you'd load these from a database)
        self.known_cascades = [
            CascadeEvent(
                timestamp=1652140800,  # May 9, 2022 - Luna collapse
                event_name="Luna/UST Collapse",
                severity="extreme",
                duration_seconds=7200,
                total_liquidations=1_500_000_000,
                price_drop_pct=25.0,
                exchanges_affected=["binance", "ftx", "okx", "bybit"],
                notes="Triggered by UST depeg, cascaded across entire market"
            ),
            CascadeEvent(
                timestamp=1647302400,  # March 15, 2022 - Fed rate hike
                event_name="Fed Rate Hike Cascade",
                severity="moderate",
                duration_seconds=3600,
                total_liquidations=500_000_000,
                price_drop_pct=8.0,
                exchanges_affected=["binance", "coinbase", "kraken"],
                notes="Macro-driven liquidation cascade"
            ),
            CascadeEvent(
                timestamp=1620777600,  # May 12, 2021 - Elon tweet cascade
                event_name="Elon Energy FUD",
                severity="major",
                duration_seconds=1800,
                total_liquidations=800_000_000,
                price_drop_pct=15.0,
                exchanges_affected=["binance", "huobi", "okx"],
                notes="Tweet-triggered cascade, very rapid"
            ),
            # Add more historical events...
        ]

    async def backtest_detection(
        self,
        historical_data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Run backtest on historical liquidation data
        """
        print(f"🔬 Starting backtest from {start_date} to {end_date}")

        result = BacktestResult()
        detection_lags = []

        # Process historical data chronologically
        for timestamp in historical_data['timestamp'].unique():
            events = historical_data[historical_data['timestamp'] == timestamp]

            # Process each liquidation event
            for _, event in events.iterrows():
                event_dict = event.to_dict()
                metrics = await self.detector.process_liquidation(event_dict)

                # Check if we're in a known cascade window
                in_cascade = self._is_in_cascade_window(timestamp)
                detected_cascade = metrics.signal.value >= CascadeSignal.ALERT.value

                # Update confusion matrix
                if in_cascade and detected_cascade:
                    result.true_positives += 1
                    # Calculate detection lag
                    lag = self._calculate_detection_lag(timestamp, metrics)
                    detection_lags.append(lag)
                elif not in_cascade and detected_cascade:
                    result.false_positives += 1
                elif in_cascade and not detected_cascade:
                    result.false_negatives += 1
                else:
                    result.true_negatives += 1

        # Calculate performance metrics
        if detection_lags:
            result.avg_detection_lag_ms = np.mean(detection_lags)
            result.fastest_detection_ms = np.min(detection_lags)
            result.slowest_detection_ms = np.max(detection_lags)

        # Calculate precision, recall, F1
        if result.true_positives + result.false_positives > 0:
            result.precision = result.true_positives / (result.true_positives + result.false_positives)

        if result.true_positives + result.false_negatives > 0:
            result.recall = result.true_positives / (result.true_positives + result.false_negatives)

        if result.precision + result.recall > 0:
            result.f1_score = 2 * (result.precision * result.recall) / (result.precision + result.recall)

        return result

    async def backtest_trading_strategy(
        self,
        historical_data: pd.DataFrame,
        initial_capital: float = 100_000
    ) -> Dict:
        """
        Backtest actual trading performance
        This is what really matters - does it make money?
        """
        trades = []
        capital = initial_capital
        position = 0
        entry_price = 0

        peak_capital = capital
        max_drawdown = 0

        print(f"💰 Backtesting trading strategy with ${initial_capital:,.0f}")

        for timestamp in historical_data['timestamp'].unique():
            events = historical_data[historical_data['timestamp'] == timestamp]

            # Get current price (simplified - use real price data)
            current_price = events['price'].mean()

            # Process events through detector
            for _, event in events.iterrows():
                metrics = await self.detector.process_liquidation(event.to_dict())

                # Trading logic based on cascade detection
                if metrics.signal.value >= CascadeSignal.CRITICAL.value and position == 0:
                    # Enter short position on cascade detection
                    position = -capital * 0.1 / current_price  # Risk 10% per trade
                    entry_price = current_price
                    trades.append({
                        'timestamp': timestamp,
                        'action': 'short',
                        'price': current_price,
                        'size': abs(position),
                        'signal': metrics.signal.name
                    })

                elif position < 0 and metrics.signal.value <= CascadeSignal.WATCH.value:
                    # Exit short when cascade ends
                    pnl = (entry_price - current_price) * abs(position)
                    capital += pnl

                    trades.append({
                        'timestamp': timestamp,
                        'action': 'cover',
                        'price': current_price,
                        'size': abs(position),
                        'pnl': pnl,
                        'capital': capital
                    })

                    position = 0

                    # Track drawdown
                    if capital > peak_capital:
                        peak_capital = capital
                    drawdown = (peak_capital - capital) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)

        # Calculate trading metrics
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

        total_profit = sum(t['pnl'] for t in profitable_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))

        # Calculate Sharpe ratio (simplified)
        if trades:
            returns = [t.get('pnl', 0) / initial_capital for t in trades]
            if len(returns) > 1:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(365)  # Annualized
            else:
                sharpe = 0
        else:
            sharpe = 0

        return {
            'total_trades': len(trades),
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(profitable_trades) / len(trades) if trades else 0,
            'total_pnl': capital - initial_capital,
            'roi_pct': ((capital - initial_capital) / initial_capital) * 100,
            'profit_factor': total_profit / total_loss if total_loss > 0 else float('inf'),
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown * 100,
            'final_capital': capital,
            'trades': trades
        }

    def _is_in_cascade_window(self, timestamp: float) -> bool:
        """Check if timestamp is within a known cascade event"""
        for cascade in self.known_cascades:
            if (cascade.timestamp <= timestamp <=
                cascade.timestamp + cascade.duration_seconds):
                return True
        return False

    def _calculate_detection_lag(
        self,
        timestamp: float,
        metrics
    ) -> float:
        """Calculate how quickly we detected the cascade"""
        for cascade in self.known_cascades:
            if cascade.timestamp <= timestamp <= cascade.timestamp + cascade.duration_seconds:
                # How long after cascade start did we detect it?
                return (timestamp - cascade.timestamp) * 1000  # Convert to ms
        return 0

    def generate_report(
        self,
        detection_result: BacktestResult,
        trading_result: Dict
    ) -> str:
        """
        Generate comprehensive backtest report
        """
        report = f"""
        ═══════════════════════════════════════════════════════════════
        CASCADE DETECTION BACKTEST REPORT
        ═══════════════════════════════════════════════════════════════

        📊 DETECTION PERFORMANCE:
        ─────────────────────────────────────────────────────────────
        True Positives:  {detection_result.true_positives:,} (Correctly detected)
        False Positives: {detection_result.false_positives:,} (False alarms)
        False Negatives: {detection_result.false_negatives:,} (Missed cascades)
        True Negatives:  {detection_result.true_negatives:,} (Correct calm periods)

        Precision: {detection_result.precision:.2%} (How accurate our alerts are)
        Recall:    {detection_result.recall:.2%} (How many cascades we catch)
        F1 Score:  {detection_result.f1_score:.2%} (Overall detection quality)

        ⏱️ TIMING METRICS:
        ─────────────────────────────────────────────────────────────
        Average Detection Lag: {detection_result.avg_detection_lag_ms:.0f}ms
        Fastest Detection:     {detection_result.fastest_detection_ms:.0f}ms
        Slowest Detection:     {detection_result.slowest_detection_ms:.0f}ms

        💰 TRADING PERFORMANCE:
        ─────────────────────────────────────────────────────────────
        Total Trades:      {trading_result['total_trades']}
        Win Rate:          {trading_result['win_rate']:.2%}
        Profit Factor:     {trading_result['profit_factor']:.2f}

        Total P&L:         ${trading_result['total_pnl']:,.2f}
        ROI:               {trading_result['roi_pct']:.2f}%
        Sharpe Ratio:      {trading_result['sharpe_ratio']:.2f}
        Max Drawdown:      {trading_result['max_drawdown_pct']:.2f}%

        Final Capital:     ${trading_result['final_capital']:,.2f}

        🎯 VERDICT:
        ─────────────────────────────────────────────────────────────
        """

        # Provide assessment
        if detection_result.f1_score > 0.8 and trading_result['sharpe_ratio'] > 1.5:
            report += "✅ EXCELLENT: System is production-ready!"
        elif detection_result.f1_score > 0.6 and trading_result['sharpe_ratio'] > 1.0:
            report += "🟡 GOOD: System works but needs optimization"
        else:
            report += "🔴 POOR: System needs significant improvements"

        report += f"""

        📝 RECOMMENDATIONS:
        ─────────────────────────────────────────────────────────────
        """

        # Add specific recommendations
        if detection_result.precision < 0.7:
            report += "• Reduce false positives by tightening thresholds\n"
        if detection_result.recall < 0.7:
            report += "• Improve cascade detection by lowering thresholds\n"
        if detection_result.avg_detection_lag_ms > 5000:
            report += "• Speed up detection - current lag is too high\n"
        if trading_result['max_drawdown_pct'] > 20:
            report += "• Implement better risk management - drawdown too high\n"
        if trading_result['win_rate'] < 0.4:
            report += "• Improve entry timing or signal quality\n"

        report += """
        ═══════════════════════════════════════════════════════════════
        """

        return report


class BacktestingFramework:
    """
    End-to-end backtesting utility that encapsulates data loading and execution.

    Data sources in priority order:
    1. TimescaleDB (`liquidations_significant` table)
    2. CSV exports under `data/backtest/*.csv`
    3. Mock fixtures for tests and offline development
    """

    REQUIRED_COLUMNS = [
        'timestamp',
        'exchange',
        'symbol',
        'side',
        'quantity',
        'usd_value',
        'price'
    ]

    def __init__(
        self,
        csv_dir: str = "data/backtest",
        mock_dir: str = "data/mock",
        backtester: Optional[CascadeBacktester] = None
    ):
        self.csv_dir = Path(csv_dir)
        self.mock_dir = Path(mock_dir)
        self.backtester = backtester or CascadeBacktester()
        self.timescale_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'liquidations'),
            'user': os.getenv('DB_USER', os.getenv('USER', 'postgres')),
            'password': os.getenv('DB_PASSWORD', '')
        }

    async def load_data(
        self,
        source: str = 'timescale',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load historical liquidation data from the requested source."""
        source = source.lower()

        if source == 'timescale':
            return await self._load_from_timescale(start_date, end_date)
        if source == 'csv':
            return self._load_from_csv()
        if source == 'mock':
            return self._load_mock()

        raise ValueError(f"Unsupported data source '{source}'")

    async def _load_from_timescale(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> pd.DataFrame:
        """Query TimescaleDB for liquidation events."""
        start = start_date or (datetime.utcnow() - timedelta(days=7))
        end = end_date or datetime.utcnow()

        query = """
            SELECT time, exchange, symbol, side, quantity, value_usd, price
            FROM liquidations_significant
            WHERE time BETWEEN $1 AND $2
            ORDER BY time ASC
        """

        logging.info(
            "Loading backtest data from TimescaleDB (%s → %s)",
            start.isoformat(),
            end.isoformat()
        )

        try:
            pool = await asyncpg.create_pool(
                **self.timescale_config,
                min_size=1,
                max_size=4,
                command_timeout=60
            )
        except Exception as exc:
            raise ConnectionError(
                "Failed to connect to TimescaleDB. Verify DB_HOST/DB_PORT/DB_NAME credentials "
                "and ensure the database is reachable."
            ) from exc

        try:
            async with pool.acquire() as conn:
                try:
                    rows = await conn.fetch(query, start, end)
                except asyncpg.exceptions.UndefinedTableError as exc:
                    raise RuntimeError(
                        "TimescaleDB missing table 'liquidations_significant'. Run migrations before backtesting."
                    ) from exc
        finally:
            await pool.close()

        if not rows:
            raise RuntimeError("TimescaleDB query returned no liquidation data")

        dataframe = pd.DataFrame([dict(row) for row in rows])
        dataframe.rename(columns={'time': 'timestamp', 'value_usd': 'usd_value'}, inplace=True)
        return self._standardize_dataframe(dataframe)

    def _load_from_csv(self) -> pd.DataFrame:
        """Load liquidation history from CSV exports."""
        if not self.csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {self.csv_dir}")

        frames: List[pd.DataFrame] = []
        for csv_file in sorted(self.csv_dir.glob("*.csv")):
            logging.info("Loading backtest CSV %s", csv_file)
            frames.append(pd.read_csv(csv_file))

        if not frames:
            raise FileNotFoundError(f"No CSV files located in {self.csv_dir}")

        dataframe = pd.concat(frames, ignore_index=True)
        return self._standardize_dataframe(dataframe)

    def _load_mock(self) -> pd.DataFrame:
        """Load synthetic data for testing/offline usage."""
        mock_file = self.mock_dir / "test_data.json"
        if mock_file.exists():
            logging.info("Loading mock backtest data from %s", mock_file)
            with open(mock_file) as f:
                payload = json.load(f)
        else:
            logging.info("Mock file missing, generating synthetic dataset")
            payload = self._generate_mock_payload()

        dataframe = pd.DataFrame(payload)
        return self._standardize_dataframe(dataframe)

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names, types, and ordering."""
        df = df.copy()
        column_map = {
            'time': 'timestamp',
            'value_usd': 'usd_value',
            'notional': 'usd_value',
            'amount': 'quantity'
        }
        df.rename(columns=column_map, inplace=True)

        if 'timestamp' not in df.columns:
            raise ValueError("Dataset missing mandatory 'timestamp' column")

        # Convert timestamps to epoch seconds
        if not np.issubdtype(df['timestamp'].dtype, np.number):
            ts = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
            if ts.isna().all():
                raise ValueError("Unable to parse timestamps in dataset")
            df['timestamp'] = ts.view('int64') / 1_000_000_000

        df['side'] = df['side'].str.lower()

        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Dataset missing required fields: {', '.join(missing)}")

        standardized = df[self.REQUIRED_COLUMNS].dropna().copy()
        standardized.sort_values('timestamp', inplace=True)
        standardized.reset_index(drop=True, inplace=True)
        return standardized

    def _generate_mock_payload(self, rows: int = 720) -> List[Dict[str, Any]]:
        """Generate deterministic synthetic data for tests."""
        base_time = time.time()
        data = []
        for idx in range(rows):
            timestamp = base_time - idx * 60  # 1-minute intervals
            price = 40000 + np.random.randn() * 500
            quantity = max(np.random.exponential(0.5), 0.01)
            usd_value = price * quantity
            data.append({
                'timestamp': timestamp,
                'exchange': np.random.choice(['binance', 'bybit', 'okx']),
                'symbol': 'BTCUSDT',
                'side': np.random.choice(['long', 'short']),
                'quantity': quantity,
                'usd_value': usd_value,
                'price': price
            })
        return data



# Example usage
async def run_comprehensive_backtest(
    source: str = 'timescale',
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    symbols: Optional[List[str]] = None,
    export_path: str = 'backtest_results.json'
) -> Tuple[BacktestResult, Dict[str, Any]]:
    """
    Complete backtest workflow
    """
    framework = BacktestingFramework()
    backtester = framework.backtester

    # Load historical data (simplified - you'd load from database)
    print("📚 Loading historical liquidation data...")
    try:
        sample_data = await framework.load_data(source=source, start_date=start_date, end_date=end_date)
    except Exception as exc:
        logging.warning("Falling back to mock dataset (%s)", exc)
        sample_data = await framework.load_data(source='mock')

    if symbols:
        sample_data = sample_data[sample_data['symbol'].isin(symbols)]
        if sample_data.empty:
            raise ValueError(f"No records found for requested symbols: {', '.join(symbols)}")

    print(f"   • Source: {source}")
    print(f"   • Rows loaded: {len(sample_data):,}")
    if symbols:
        print(f"   • Symbols: {', '.join(symbols)}")
    if start_date and end_date:
        print(f"   • Range: {start_date.isoformat()} → {end_date.isoformat()}")

    # Run detection backtest
    print("\n🔬 Running detection backtest...")
    detection_result = await backtester.backtest_detection(
        sample_data,
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

    # Run trading backtest
    print("\n💰 Running trading strategy backtest...")
    trading_result = await backtester.backtest_trading_strategy(sample_data)

    # Generate report
    report = backtester.generate_report(detection_result, trading_result)
    print(report)

    # Save results
    with open(export_path, 'w') as f:
        json.dump({
            'detection': asdict(detection_result),
            'trading': trading_result,
            'report': report
        }, f, indent=2)

    print(f"\n✅ Backtest complete! Results saved to {export_path}")

    return detection_result, trading_result


if __name__ == "__main__":
    asyncio.run(run_comprehensive_backtest())
