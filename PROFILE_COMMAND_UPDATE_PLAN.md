# Profile Command Update Plan
## Implementation Guide for Next Session

### 📋 CURRENT STATUS
- `/profile` command is **IMPLEMENTED and WORKING** in the Telegram bot
- Bot: `@napo_assistant_bot` (Crypto1 bot)
- File to edit: `/Users/screener-m3/projects/crypto-assistant/services/telegram-bot/main.py`
- Method to modify: `_format_profile_response()` starting at line 537

### 🎯 REQUIRED CHANGES

#### 1. **Remove VA% Line (Line 570)**
- **Current**: `VA%: VP: {vp['value_area_pct']:.1f}% | TPO: {tpo['value_area_pct']:.1f}%`
- **Action**: DELETE this entire line - it's redundant since VA is always ~70%

#### 2. **Remove TPO from Short Timeframes**
- **Current**: TPO shown for all timeframes (1m, 15m, 1h, 4h, 1d)
- **Action**: Remove TPO from 1m, 15m, 1h, 4h - ONLY show for Daily
- **Reason**: TPO should only use 30-minute periods, not arbitrary timeframes

#### 3. **Fix Time Format (Line 612)**
- **Current**: `🕐 {datetime.now().strftime('%H:%M:%S')} UTC`
- **New**: `🕐 {datetime.now().strftime('%H:%M:%S')} UTC / {(datetime.now().replace(hour=(datetime.now().hour + 8) % 24)).strftime('%H:%M:%S')} SGT`
- **Note**: SGT is UTC+8

#### 4. **Reformat Output Display**
Change the format for each timeframe from:
```python
# OLD FORMAT (Lines 567-572)
message += f"""**{tf.upper()}** ({period}, {candles} candles)
VP:  POC: ${vp['poc']:,.0f} | VAL: ${vp['val']:,.0f} | VAH: ${vp['vah']:,.0f} {vp_in_va}
TPO: POC: ${tpo['poc']:,.0f} | VAL: ${tpo['val']:,.0f} | VAH: ${tpo['vah']:,.0f} {tpo_in_va}
VA%: VP: {vp['value_area_pct']:.1f}% | TPO: {tpo['value_area_pct']:.1f}%

"""
```

To:
```python
# NEW FORMAT - Short timeframes (1m, 15m, 1h, 4h)
if tf != '1d':
    message += f"""{tf.upper()} Profile
- VAH: ${vp['vah']:,.0f} {vp_in_va}
- POC: ${vp['poc']:,.0f}
- VAL: ${vp['val']:,.0f}

"""
else:
    # Daily Profile with TPO
    message += f"""Daily Profile
- VAH: ${vp['vah']:,.0f} {vp_in_va}
- POC: ${vp['poc']:,.0f}
- VAL: ${vp['val']:,.0f}
TPO 30m: POC: ${tpo['poc']:,.0f} | VAL: ${tpo['val']:,.0f} | VAH: ${tpo['vah']:,.0f}

"""
```

### 📊 EXPECTED FINAL OUTPUT

```
📊 MARKET PROFILE - BTC
💰 Current: $113,153.99
──────────────────────────────

1M Profile
- VAH: $113,407 ✅
- POC: $113,095
- VAL: $113,027

15M Profile
- VAH: $114,313 ❌
- POC: $114,262
- VAL: $113,296

1H Profile
- VAH: $119,071 ❌
- POC: $117,762
- VAL: $114,125

4H Profile
- VAH: $122,055 ❌
- POC: $118,629
- VAL: $116,008

Daily Profile
- VAH: $119,703 ❌
- POC: $117,569
- VAL: $114,180
TPO 30m: POC: $117,500 | VAL: $114,583 | VAH: $120,543

──────────────────────────────
📍 ANALYSIS
• ⚠️ TRENDING: Price outside value area on most timeframes
• Strategy: Follow trend, breakout continuation likely

📊 KEY LEVELS
- 1H POC: $117,762 (High volume node)
- 4H VA: $116,008 - $122,055
- Daily POC: $117,569 (Major reference)

🕐 12:11:03 UTC / 20:11:03 SGT
```

### 🧪 TESTING STEPS

1. **Edit the file**: `/Users/screener-m3/projects/crypto-assistant/services/telegram-bot/main.py`
2. **Rebuild container**: `docker-compose build telegram-bot`
3. **Restart service**: `docker-compose up -d`
4. **Test commands**:
   - `/profile BTC`
   - `/profile ETH`
   - `/profile SOL`
5. **Verify**:
   - VAH is at top for each timeframe
   - No VA% shown
   - TPO only appears for Daily
   - Time shows both UTC and SGT

### ⚠️ IMPORTANT NOTES

1. **TPO Implementation Issue**: Current TPO calculation is not using proper 30-minute periods. It's using daily candles which is incorrect. Consider fixing the TPO calculation in `profile_calculator.py` in future.

2. **Value Area Always ~70%**: The algorithm targets 70% of volume for value area, so showing the percentage is redundant.

3. **File Locations**:
   - Telegram bot formatting: `/services/telegram-bot/main.py` (line 537+)
   - Profile calculations: `/services/market-data/profile_calculator.py`

4. **Current Branch**: `feature/enhanced-trading-commands`

### 📝 VALIDATION CHECKLIST
- [ ] VAH appears at top of each profile
- [ ] POC in middle
- [ ] VAL at bottom
- [ ] TPO only shows for Daily timeframe
- [ ] No VA% percentages displayed
- [ ] Time format shows UTC / SGT
- [ ] ✅/❌ indicators work correctly
- [ ] Output is more compact than before

### 🚀 DEPLOYMENT COMMANDS
```bash
# After making changes
docker-compose build telegram-bot
docker-compose up -d
docker logs crypto-telegram-bot --tail 20

# Test the command
# In Telegram: /profile BTC
```

### 🔍 TROUBLESHOOTING
- If command doesn't appear: Restart Telegram app
- If bot doesn't respond: Check `docker logs crypto-telegram-bot`
- If format is wrong: Verify line numbers haven't changed in main.py