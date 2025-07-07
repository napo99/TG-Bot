# Enhanced /price Command - Rollback Documentation

## Overview
This document provides complete rollback instructions for the enhanced `/price` command implementation to ensure safe deployment and recovery.

## Original Implementation Backup

### Files Modified
1. **services/telegram-bot/main_webhook.py** - Lines 230-307 (price_command function)
2. **services/market-data/main.py** - Lines 351-437 (get_combined_price function)

### Key Functions Changed
- `price_command()` - Telegram bot command handler
- `get_combined_price()` - Market data API endpoint
- `CombinedPriceData` - Data structure (if modified)

## Pre-Enhancement State

### Original /price Command Output Format
```
📊 BTC/USDT

🏪 SPOT
💰 Price: $108,401.8400
🔴 24h: -0.33%
📊 Volume: 9,270 BTC ($1004.9M)

⚡ PERPETUALS
💰 Price: $108,361.1000
🔴 24h: -0.31%
📊 Volume: 100,179 BTC ($10855.5M)
📈 OI: 79,174 BTC ($8579M)
💸 Funding: +0.0046%

🕐 Updated: 15:51:07
```

### Original API Response Structure
```python
@dataclass
class CombinedPriceData:
    base_symbol: str
    spot: Optional[PriceData]
    perp: Optional[PerpData]
    timestamp: datetime

@dataclass
class PriceData:
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float]
    change_24h: Optional[float]
    market_type: str

@dataclass
class PerpData:
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float]
    change_24h: Optional[float]
    open_interest: Optional[float]
    funding_rate: Optional[float]
    funding_rate_change: Optional[float]
```

## Enhanced Implementation Changes

### New Features Added
1. **15m Price Changes**: Short-term price momentum
2. **15m Volume Data**: Recent volume activity
3. **15m Delta Calculations**: Volume momentum indicators
4. **Enhanced Number Formatting**: B/M/K notation with 2 decimal precision
5. **Dual Time Zone Display**: UTC/SGT timestamps
6. **Improved Visual Layout**: Better spacing and icons

### New Data Requirements
- 15-minute OHLCV data from exchanges
- Delta calculations for both 24h and 15m periods
- Enhanced formatting functions

## Rollback Procedures

### Quick Rollback (Emergency)
If issues are detected, immediately revert to git backup:
```bash
git checkout HEAD~1 -- services/telegram-bot/main_webhook.py
git checkout HEAD~1 -- services/market-data/main.py
docker-compose restart
```

### Staged Rollback
1. **Test Environment First**: Validate rollback in staging
2. **Database Backup**: Ensure no data loss
3. **Service Restart**: Restart containers after file revert
4. **Monitoring**: Verify original functionality restored

### Rollback Verification
After rollback, verify:
- [ ] `/price BTC-USDT` returns original format
- [ ] No error messages in logs
- [ ] Response time < 2 seconds
- [ ] All existing functionality works

## Risk Mitigation

### Deployment Strategy
1. **Feature Branch**: Develop in `enhanced-price-display` branch
2. **Gradual Rollout**: Deploy to test environment first
3. **Monitoring**: Real-time error monitoring
4. **Fallback Logic**: Graceful degradation if new data unavailable

### Error Handling
- Fallback to original format if 15m data fails
- Maintain backward compatibility
- Log errors without breaking user experience

## Testing Checklist

### Pre-Deployment
- [ ] Original `/price` command functionality preserved
- [ ] Enhanced features work correctly
- [ ] Error handling tested
- [ ] Performance impact minimal
- [ ] Docker containers restart successfully

### Post-Deployment
- [ ] Monitor error logs for 24 hours
- [ ] User feedback collection
- [ ] Performance metrics within acceptable ranges
- [ ] Rollback procedure tested in staging

## Contact Information
- **Developer**: Claude Code Assistant
- **Deployment Date**: [TO BE FILLED]
- **Git Commit**: [TO BE FILLED]
- **Branch**: enhanced-price-display

## Emergency Contacts
- Check docker logs: `docker-compose logs -f telegram-bot`
- Check API health: `curl http://localhost:8001/health`
- Manual restart: `docker-compose restart`

---
**Note**: This documentation must be kept updated throughout the enhancement process to ensure safe deployment and recovery procedures.