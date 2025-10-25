# PROMPT FOR OPUS - PROFESSIONAL REFACTOR & UX ENHANCEMENT

**Copy-paste this entire prompt to Opus:**

---

## CONTEXT: Quality Gap Analysis

Yesterday (Oct 24-25 morning), you delivered **production-grade code** with comprehensive documentation:
- 13,000+ lines of professional code
- Advanced velocity engine with jerk tracking (3rd derivative - industry first)
- Multi-agent orchestration system
- Performance 2-2,500x better than targets
- Comprehensive documentation (4,242 lines)

This afternoon, Sonnet attempted to help but delivered:
- 190 lines of redundant code
- Basic documentation (635 lines)
- Multiple bugs requiring fixes
- Poor UX (just logs, no visual dashboard)
- Confusion about system architecture

**See detailed comparison**: `OPUS_VS_SONNET_QUALITY_COMPARISON.md`

---

## YOUR MISSION: Professional Refactor & Trader-Actionable UX

Create a **production-grade real-time monitoring system** with the same quality as your work yesterday, specifically matching the excellence of:
- `monitor_liquidations_live.py` from Oct 24 (the nice visual format the user liked)
- Your comprehensive documentation style from ORCHESTRATOR_FINAL_REPORT.md
- Your systematic approach from AGENT1/2/3_IMPLEMENTATION_SUMMARY.md files

---

## REFERENCE: What You Built Yesterday (Oct 24-25)

### Your Morning Plan (ORCHESTRATION_PLAN.md):
Located at: `services/liquidation-aggregator/ORCHESTRATION_PLAN.md`

**Agent 1**: Enhanced WebSocket Manager
- ✅ Velocity tracking (10s, 30s, 60s, 300s)
- ✅ BTC price feed
- ✅ Sub-millisecond latency
- ✅ Redis integration

**Agent 2**: Advanced Velocity Engine
- ✅ Multi-timeframe velocity (100ms, 500ms, 2s, 10s, 60s)
- ✅ Acceleration (2nd derivative)
- ✅ **Jerk (3rd derivative)** - INDUSTRY FIRST
- ✅ Volume-weighted metrics
- ✅ Cross-exchange correlation

**Agent 3**: Signal Generation
- ✅ 6-level market regime detection
- ✅ Multi-factor cascade scoring (6 components)
- ✅ 5-level signal hierarchy (NONE → EXTREME)
- ✅ Redis pub/sub

### Your Deliverables Yesterday:

**Code Files** (all working, production-ready):
- `enhanced_websocket_manager.py` (714 lines)
- `advanced_velocity_engine.py` (632 lines)
- `cascade_risk_calculator.py` (522 lines)
- `cascade_signal_generator.py` (747 lines)
- `market_regime_detector.py` (617 lines)
- `deploy_enhanced_system.py` (290 lines)
- Comprehensive test suites (3,500+ lines)

**Documentation** (professional quality):
- `ORCHESTRATOR_FINAL_REPORT.md` (654 lines, 23KB)
- `AGENT1_IMPLEMENTATION_SUMMARY.md` (561 lines)
- `AGENT2_IMPLEMENTATION_SUMMARY.md` (502 lines)
- `AGENT3_IMPLEMENTATION_SUMMARY.md` (681 lines)
- `VELOCITY_ENGINE_DOCS.md` (897 lines)
- `SIGNAL_GENERATION_DOCS.md` (947 lines)

---

## REFERENCE: User's Favorite Format (Oct 24)

**File**: `monitor_liquidations_live.py` (444 lines)
**What user liked about it**:

```
🔴 HYPERLIQUID LIVE LIQUIDATION MONITOR 🔴
================================================================================
⚡ LIVE | Runtime: 1167s | Trades: 35,266 | Speed: 25.4 trades/sec | Liquidations: 0
================================================================================

📈 LIVE MARKET ACTIVITY:
Coin      Price         Last Size  Side    1h Liq Vol    Time      Status
--------------------------------------------------------------------------------
BTC       $111,600.00   0.0045 BUY         $0.00         0.0s ● LIVE
ETH       $  3,930.00   0.2279 SELL        $0.00         0.0s ● LIVE
SOL       $    193.79   1.9500 SELL        $0.00        11.3s ○ idle
ARB       $      0.32  60.2000 SELL        $0.00        74.7s ○ old
...

⏳ Waiting for liquidations...
Liquidations occur during high volatility. Monitor is actively scanning all trades.
```

**Why user loved this**:
- ✅ Clean, organized visual layout
- ✅ Real-time updates (auto-refresh every 2s)
- ✅ Activity indicators (● LIVE, ● ACT, ○ idle, ○ old)
- ✅ Multi-coin monitoring in fixed table (no flickering)
- ✅ Color-coded by exchange and side
- ✅ Statistics dashboard at top
- ✅ Trade speed metrics
- ✅ Clear waiting message

---

## WHAT NEEDS TO BE BUILT NOW

### PRIMARY GOAL: Production-Grade Real-Time Monitor

Create: **`professional_liquidation_monitor.py`**

A **terminal UI dashboard** that combines:
1. Your advanced analytics (velocity, acceleration, jerk, cascades, regime)
2. The clean UX format from `monitor_liquidations_live.py` (Oct 24)
3. Trader-actionable information in real-time

### REQUIRED FEATURES (Must Have):

#### 1. Header Dashboard (Auto-refresh every 2s)
```
🚀 PROFESSIONAL LIQUIDATION CASCADE MONITOR 🚀
═══════════════════════════════════════════════════════════════════════════════
⚡ LIVE | Runtime: 342s | Events: 1,247 | Throughput: 3.6 events/s
Exchanges: BINANCE ● BYBIT ● OKX ● HYPERLIQUID | Symbols: BTC, ETH, SOL
═══════════════════════════════════════════════════════════════════════════════
```

#### 2. Multi-Timeframe Velocity Panel (Your Agent 2 work)
```
📊 VELOCITY METRICS (BTCUSDT):
Timeframe    Events    Velocity      Acceleration   Jerk          Status
───────────────────────────────────────────────────────────────────────────────
100ms        3         30.0 evt/s    +5.2 evt/s²    +0.8 evt/s³   🔥 RAPID
2s           15        7.5 evt/s     +2.1 evt/s²    +0.3 evt/s³   ⚡ ACTIVE
10s          42        4.2 evt/s     +0.8 evt/s²    -0.1 evt/s³   ✓ NORMAL
60s          180       3.0 evt/s     +0.1 evt/s²     0.0 evt/s³   ✓ STABLE
```

#### 3. Market Regime Indicator (Your Agent 3 work)
```
🌡️  MARKET REGIME: VOLATILE | BTC Price: $67,234.50 (+1.2% | ↑ trending)
Risk Multiplier: 1.8x | Threshold Adjustments: ACTIVE
Volatility: HIGH | Liquidity: MODERATE | Trend: BULLISH
```

#### 4. Exchange Activity Table (Like Oct 24 format)
```
📈 LIVE EXCHANGE ACTIVITY:
Exchange     Symbol   Last Liq      Side    Size        1h Volume    Status
───────────────────────────────────────────────────────────────────────────────
BINANCE      BTC     $67,234.50    LONG    $125,000    $2.4M        ● LIVE
BYBIT        BTC     $67,230.00    SHORT   $45,000     $890K        ● LIVE
OKX          BTC     $67,232.80    LONG    $12,500     $156K        ● ACT
HYPERLIQUID  BTC     $67,235.20    SHORT   $8,900      $47K         ○ idle
```

#### 5. Cascade Detection Panel (Your Agent 2 + 3 work)
```
🚨 CASCADE RISK ANALYSIS:
Symbol    Probability  Signal Level  Risk Score  Contributing Factors
───────────────────────────────────────────────────────────────────────────────
BTC       87.5%       CRITICAL      0.92        Velocity↑ Accel↑ Jerk↑ Volume↑
ETH       34.2%       ELEVATED      0.41        Velocity↑ Correlation↑
SOL       12.1%       NORMAL        0.18        -
```

#### 6. Cross-Exchange Correlation (Your Agent 2 work)
```
🔗 EXCHANGE CORRELATION (60s window):
           BINANCE    BYBIT     OKX       HYPERLIQUID
BINANCE    1.00       0.87      0.72      0.45
BYBIT      0.87       1.00      0.81      0.52
OKX        0.72       0.81      1.00      0.38
HYPERLIQUID 0.45      0.52      0.38      1.00

High correlation (>0.7) = Market-wide cascade risk ⚠️
```

#### 7. Real-Time Alert Stream (Bottom section)
```
⚡ REAL-TIME ALERTS:
[16:42:15] 🚨 CRITICAL CASCADE - BTCUSDT | Prob: 87.5% | Velocity: 8.4 evt/s
[16:42:12] ⚡ VELOCITY SPIKE - BTCUSDT | 10s: 12.3 evt/s (accel: +4.2 evt/s²)
[16:42:08] 💰 INSTITUTIONAL - BINANCE BTC LONG $125,000 @ $67,234.50
[16:42:05] 📊 REGIME CHANGE - VOLATILE → EXTREME | Risk multiplier: 2.5x
[16:42:01] 🔥 JERK ALERT - BTCUSDT | +2.1 evt/s³ (rapid acceleration change)
```

#### 8. Performance Metrics Footer
```
───────────────────────────────────────────────────────────────────────────────
Latency: 0.4ms | Redis: ✓ | Cascade Engine: ✓ | Signals: 47 | Uptime: 5m 42s
Press Ctrl+C to stop and see detailed statistics
```

---

## TECHNICAL REQUIREMENTS

### Must Use Your Existing Code:
1. **Agent 1** (`enhanced_websocket_manager.py`):
   - Subscribe to all exchange streams
   - Get velocity metrics from VelocityTracker
   - Access BTC price feed

2. **Agent 2** (`advanced_velocity_engine.py` + `cascade_risk_calculator.py`):
   - `AdvancedVelocityEngine.calculate_multi_timeframe_velocity()`
   - `AdvancedVelocityEngine.calculate_exchange_correlation()`
   - `CascadeRiskCalculator.calculate_risk()`
   - Get velocity, acceleration, jerk metrics

3. **Agent 3** (`cascade_signal_generator.py` + `market_regime_detector.py`):
   - `MarketRegimeDetector.detect_regime()`
   - `CascadeSignalGenerator.generate_signal()`
   - Get cascade probability and signal level

4. **Redis Integration**:
   - Read velocity metrics: `velocity:{symbol}:current`
   - Read cascade signals: `cascade:probability:{symbol}`
   - Read market regime: `regime:current`

### Display Architecture:
```python
class ProfessionalLiquidationMonitor:
    """
    Production-grade real-time liquidation monitor
    Combines advanced analytics with clean UX
    """

    def __init__(self):
        # Initialize Agent 1: WebSocket streams
        self.websocket_manager = EnhancedWebSocketManager(...)

        # Initialize Agent 2: Velocity engine
        self.velocity_engine = AdvancedVelocityEngine()
        self.risk_calculator = CascadeRiskCalculator()

        # Initialize Agent 3: Signal generation
        self.signal_generator = CascadeSignalGenerator(...)
        self.regime_detector = MarketRegimeDetector()

        # Display state
        self.alert_buffer = deque(maxlen=10)  # Last 10 alerts
        self.exchange_activity = {}
        self.last_update = time.time()

    async def render_dashboard(self):
        """
        Render complete dashboard
        Auto-refresh every 2 seconds
        """
        self.clear_screen()

        # 1. Render header
        self.render_header()

        # 2. Render velocity metrics (Agent 2)
        self.render_velocity_panel()

        # 3. Render market regime (Agent 3)
        self.render_regime_indicator()

        # 4. Render exchange activity table
        self.render_exchange_table()

        # 5. Render cascade risk (Agent 2 + 3)
        self.render_cascade_panel()

        # 6. Render correlation matrix (Agent 2)
        self.render_correlation_matrix()

        # 7. Render alert stream
        self.render_alert_stream()

        # 8. Render footer
        self.render_footer()

    async def on_liquidation(self, event):
        """
        Process liquidation event through analytics pipeline
        Update all panels with new data
        """
        # Update Agent 2: Velocity tracking
        velocity_metrics = self.velocity_engine.calculate_multi_timeframe_velocity(...)

        # Update Agent 2: Risk calculation
        risk = self.risk_calculator.calculate_risk(velocity_metrics)

        # Update Agent 3: Signal generation
        signal = await self.signal_generator.generate_signal(...)

        # Update Agent 3: Regime detection
        regime = self.regime_detector.detect_regime(...)

        # Generate alerts based on thresholds
        if signal.signal_level >= SignalLevel.CRITICAL:
            self.add_alert(f"🚨 CRITICAL CASCADE - {event.symbol} | Prob: {signal.probability:.1%}")

        if velocity_metrics.acceleration > ACCELERATION_ALERT_THRESHOLD:
            self.add_alert(f"⚡ VELOCITY SPIKE - {event.symbol} | Accel: {velocity_metrics.acceleration:.1f}")

        # Trigger re-render
        await self.render_dashboard()
```

### Color Scheme:
- **BINANCE**: Yellow (`\033[93m`)
- **BYBIT**: Cyan (`\033[96m`)
- **OKX**: Blue (`\033[94m`)
- **HYPERLIQUID**: Magenta (`\033[95m`)
- **LONG liquidations**: Red (`\033[91m`)
- **SHORT liquidations**: Green (`\033[92m`)
- **CRITICAL alerts**: Bold Red (`\033[1m\033[91m`)
- **Headers**: Bold Cyan (`\033[1m\033[96m`)

---

## DOCUMENTATION REQUIREMENTS

Create: **`PROFESSIONAL_MONITOR_GUIDE.md`**

Using your documentation style from yesterday (see ORCHESTRATOR_FINAL_REPORT.md), include:

### 1. Executive Summary
- What the monitor does
- Key features at a glance
- Quick start (3 commands)

### 2. Feature Breakdown
For each panel (velocity, regime, cascade, correlation):
- Mathematical foundation
- How to interpret the data
- Trading implications
- Example scenarios

### 3. Usage Guide
```bash
# Basic usage
python professional_liquidation_monitor.py

# With specific exchanges
python professional_liquidation_monitor.py --exchanges binance bybit hyperliquid

# With specific symbols
python professional_liquidation_monitor.py --symbols BTCUSDT ETHUSDT SOLUSDT

# With custom refresh rate
python professional_liquidation_monitor.py --refresh 1.0  # 1 second updates
```

### 4. Interpretation Guide
**Example**: "What does it mean when..."
- Jerk > 2.0 evt/s³: Explosive acceleration building
- Cascade probability > 75%: Imminent cascade, reduce risk
- Correlation > 0.8: Market-wide event, not exchange-specific
- Regime = EXTREME: Widen stop losses, reduce position size

### 5. Trading Playbook
**Actionable strategies based on monitor signals:**

**Scenario 1: Pre-Cascade Detection**
```
Monitor shows:
- Velocity 10s: 8.2 evt/s (rising)
- Acceleration: +3.5 evt/s²
- Jerk: +1.8 evt/s³
- Cascade Prob: 72%
- Signal: WARNING

Action:
→ Reduce position size by 50%
→ Tighten stops to 1.5%
→ Prepare to exit if probability > 80%
```

**Scenario 2: Cross-Exchange Cascade**
```
Monitor shows:
- BINANCE-BYBIT correlation: 0.91
- BINANCE-OKX correlation: 0.87
- All velocities spiking
- Cascade Prob: 89%
- Signal: CRITICAL

Action:
→ Exit all positions immediately
→ Wait for velocity to drop below 2.0 evt/s
→ Re-entry when regime returns to NORMAL
```

### 6. Performance Benchmarks
Document performance (like you did yesterday):
- Latency per panel render
- Memory usage
- CPU usage
- Max events/second handled

### 7. Troubleshooting
Common issues and solutions

---

## CODE QUALITY STANDARDS (Match Your Yesterday's Work)

### Must Have:
1. **Type hints** on all functions
2. **Docstrings** with performance characteristics
3. **Error handling** with graceful degradation
4. **Async/await** properly used
5. **Performance comments** (e.g., "O(1) operation", "<1ms latency")
6. **Memory efficiency** notes
7. **Future Rust migration** comments where applicable

### Example (your style from yesterday):
```python
def calculate_multi_timeframe_velocity(self, symbol: str) -> Optional[MultiTimeframeVelocity]:
    """
    Calculate multi-timeframe velocity with derivatives

    Args:
        symbol: Trading symbol

    Returns:
        MultiTimeframeVelocity metrics or None if insufficient data

    Performance: <0.5ms for typical workloads
    Memory: ~40 bytes per event in buffer
    Complexity: O(n) where n = buffer size (capped at 3000)

    Future: This hot path is designed for Rust migration
    """
    start_time = time.perf_counter()

    # ... implementation ...

    calc_time_ms = (time.perf_counter() - start_time) * 1000
    if calc_time_ms > PERF_WARNING_THRESHOLD_MS:
        logger.warning(f"⚠️ Calculation took {calc_time_ms:.2f}ms")

    return result
```

---

## CLEANUP REQUIREMENTS

### Remove Sonnet's Redundant Code:
1. **Delete**: `test_hyperliquid_live.py` (redundant with your monitor)
2. **Review & merge**: `HYPERLIQUID_TEST_GUIDE.md` → your professional docs
3. **Review & merge**: `SYSTEM_COMPARISON.md` → your ORCHESTRATOR_FINAL_REPORT.md
4. **Fix bugs in**: `deploy_enhanced_system.py` (Sonnet's attribute fix is needed but code quality is poor)

### Consolidate Documentation:
All documentation should match your style from:
- `ORCHESTRATOR_FINAL_REPORT.md`
- `VELOCITY_ENGINE_DOCS.md`
- `SIGNAL_GENERATION_DOCS.md`

No basic README-level docs. Everything should be professional technical documentation.

---

## SUCCESS CRITERIA

### Must Achieve:
1. ✅ Monitor displays ALL Agent 2 metrics (velocity, acceleration, jerk)
2. ✅ Monitor displays ALL Agent 3 metrics (regime, signal level, probability)
3. ✅ Clean UX matching `monitor_liquidations_live.py` from Oct 24
4. ✅ Auto-refresh every 2 seconds without flickering
5. ✅ Color-coded by exchange and liquidation side
6. ✅ Real-time alert stream
7. ✅ Trader-actionable information (not just data dumps)
8. ✅ Professional documentation (like yesterday's work)
9. ✅ Performance metrics displayed in footer
10. ✅ All code has type hints, docstrings, performance notes

### Bonus (If Time Permits):
- Export to CSV/JSON functionality
- Redis pub/sub signal viewer panel
- Historical velocity chart (last 5 minutes)
- Cascade event timeline
- Audio alerts for CRITICAL signals

---

## DELIVERABLES CHECKLIST

### Code Files:
- [ ] `professional_liquidation_monitor.py` (800-1200 lines, production-ready)
- [ ] Updated `deploy_enhanced_system.py` (fix Sonnet's bugs, improve quality)
- [ ] Integration tests for the monitor
- [ ] Cleanup: Delete redundant Sonnet files

### Documentation:
- [ ] `PROFESSIONAL_MONITOR_GUIDE.md` (comprehensive, 800-1200 lines)
- [ ] `TRADING_PLAYBOOK.md` (actionable strategies based on signals)
- [ ] Updated `ORCHESTRATOR_FINAL_REPORT.md` (include monitor in system diagram)
- [ ] `CLEANUP_REPORT.md` (what was removed, what was consolidated)

### Quality Assurance:
- [ ] All code matches yesterday's quality standards
- [ ] All documentation matches yesterday's comprehensive style
- [ ] Performance benchmarks included
- [ ] No redundant code remaining
- [ ] System architecture diagram updated

---

## FINAL NOTES

**What Made Your Oct 24 Work Excellent:**
1. Systematic agent-based approach
2. Comprehensive documentation with math formulas
3. Performance metrics everywhere
4. Production-ready code quality
5. Clear architecture diagrams
6. Professional technical writing
7. Innovation (jerk tracking)
8. Exceeding all targets

**Please replicate that same excellence for this monitor.**

The user loved `monitor_liquidations_live.py` from Oct 24 because it had:
- Clean visual layout
- Real-time updates
- Clear status indicators
- No clutter

The user wants that **same UX quality** but enhanced with:
- Your Agent 2 advanced analytics (velocity/acceleration/jerk)
- Your Agent 3 intelligence (cascade probability, market regime, signals)
- Trader-actionable information

**Think: Bloomberg Terminal quality, not debug logs.**

---

## EXAMPLE OUTPUT (What User Should See)

When running `python professional_liquidation_monitor.py --exchanges binance bybit hyperliquid`:

```
🚀 PROFESSIONAL LIQUIDATION CASCADE MONITOR 🚀
═══════════════════════════════════════════════════════════════════════════════
⚡ LIVE | Runtime: 342s | Events: 1,247 | Throughput: 3.6 events/s
Exchanges: BINANCE ● BYBIT ● HYPERLIQUID | Symbols: BTC, ETH, SOL
═══════════════════════════════════════════════════════════════════════════════

📊 VELOCITY METRICS (BTCUSDT):
Timeframe    Events    Velocity      Acceleration   Jerk          Status
───────────────────────────────────────────────────────────────────────────────
100ms        3         30.0 evt/s    +5.2 evt/s²    +0.8 evt/s³   🔥 RAPID
2s           15        7.5 evt/s     +2.1 evt/s²    +0.3 evt/s³   ⚡ ACTIVE
10s          42        4.2 evt/s     +0.8 evt/s²    -0.1 evt/s³   ✓ NORMAL
60s          180       3.0 evt/s     +0.1 evt/s²     0.0 evt/s³   ✓ STABLE

🌡️  MARKET REGIME: VOLATILE | BTC: $67,234.50 (+1.2% ↑) | Multiplier: 1.8x

📈 LIVE EXCHANGE ACTIVITY:
Exchange     Symbol   Last Liq      Side    Size        1h Volume    Status
───────────────────────────────────────────────────────────────────────────────
BINANCE      BTC     $67,234.50    LONG    $125,000    $2.4M        ● LIVE
BYBIT        BTC     $67,230.00    SHORT   $45,000     $890K        ● LIVE
HYPERLIQUID  BTC     $67,235.20    SHORT   $8,900      $47K         ○ idle

🚨 CASCADE RISK ANALYSIS:
Symbol    Probability  Signal Level  Risk Score  Factors
───────────────────────────────────────────────────────────────────────────────
BTC       87.5%       CRITICAL      0.92        Velocity↑ Accel↑ Jerk↑ Volume↑
ETH       34.2%       ELEVATED      0.41        Velocity↑ Correlation↑
SOL       12.1%       NORMAL        0.18        -

🔗 EXCHANGE CORRELATION (60s): BINANCE-BYBIT: 0.87 ⚠️ | BINANCE-OKX: 0.72

⚡ REAL-TIME ALERTS:
[16:42:15] 🚨 CRITICAL CASCADE - BTCUSDT | Prob: 87.5% | V: 8.4 evt/s
[16:42:12] ⚡ VELOCITY SPIKE - BTCUSDT | 10s: 12.3 evt/s (a: +4.2 evt/s²)
[16:42:08] 💰 INSTITUTIONAL - BINANCE BTC LONG $125K @ $67,234.50
[16:42:05] 📊 REGIME CHANGE - VOLATILE → EXTREME | Multiplier: 2.5x
[16:42:01] 🔥 JERK ALERT - BTCUSDT | +2.1 evt/s³ (rapid accel change)

───────────────────────────────────────────────────────────────────────────────
Latency: 0.4ms | Redis: ✓ | Signals: 47 | Uptime: 5m 42s | Ctrl+C to exit
```

**This is what excellence looks like. Please deliver this.**

---

## QUESTIONS TO ENSURE UNDERSTANDING:

Before you start, confirm:
1. ✅ You understand this should match Oct 24's `monitor_liquidations_live.py` UX quality
2. ✅ You understand this must use ALL of your Agent 2 analytics (velocity/acceleration/jerk)
3. ✅ You understand this must use ALL of your Agent 3 intelligence (regime/signals/probability)
4. ✅ You understand documentation must match your comprehensive style from yesterday
5. ✅ You understand this is trader-actionable, not developer debug logs
6. ✅ You understand Sonnet's redundant code must be removed
7. ✅ You understand this is production-grade, not a prototype

**If yes to all: Begin implementation.**

**Expected time**: 2-3 hours for production-quality delivery (matching yesterday's pace)

---

END OF PROMPT - COPY EVERYTHING ABOVE
