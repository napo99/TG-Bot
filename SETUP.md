# Setup Guide - Crypto Trading Assistant

## Prerequisites

- Docker & Docker Compose installed
- Telegram Bot Token (from @BotFather)
- Exchange API keys (optional for testing, required for live data)

## Quick Start

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd crypto-assistant

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

### 2. Configure Your Bot

**Required Settings in .env:**
```bash
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Your Telegram Chat ID (send /start to @userinfobot to get it)
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Optional Exchange Settings (for live data):**
```bash
# Binance (recommended for testing)
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
BINANCE_TESTNET=true  # Use testnet for safety

# Bybit
BYBIT_API_KEY=your_key
BYBIT_SECRET_KEY=your_secret
BYBIT_TESTNET=true
```

### 3. Start the System

```bash
# Run the startup script
./start.sh

# Or manually with Docker Compose
docker-compose up -d
```

### 4. Test Your Bot

1. Open Telegram
2. Find your bot by username
3. Send `/start` to begin
4. Try commands like:
   - `/price BTC/USDT`
   - `/balance` (requires API keys)
   - `/positions` (requires API keys)

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message | `/start` |
| `/help` | Show available commands | `/help` |
| `/price <symbol>` | Get current price | `/price BTC/USDT` |
| `/balance` | Show account balance | `/balance` |
| `/positions` | Show open positions | `/positions` |
| `/pnl` | Show P&L summary | `/pnl` |

## Security Notes

⚠️ **Important Security Practices:**

1. **API Key Permissions**: Only grant READ permissions to your API keys
2. **Environment Variables**: Never commit .env files to git
3. **Testnet First**: Always test with sandbox/testnet APIs first
4. **Authorized Users**: Set TELEGRAM_CHAT_ID to restrict access

## Troubleshooting

### Bot Not Responding
```bash
# Check if services are running
docker-compose ps

# View bot logs
docker-compose logs telegram-bot

# Restart services
docker-compose restart
```

### Market Data Errors
```bash
# Check market data service
curl http://localhost:8001/health

# View market data logs
docker-compose logs market-data

# Test API keys (check logs for authentication errors)
```

### Common Issues

1. **"Unauthorized access"**: Check TELEGRAM_CHAT_ID in .env
2. **"Exchange not configured"**: Add API keys to .env
3. **Docker errors**: Ensure Docker is running and ports 8001 are available

## Development

### Local Development
```bash
# Run individual services for development
cd services/market-data
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py

# In another terminal
cd services/telegram-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Adding New Features
1. Modify service code
2. Rebuild Docker images: `docker-compose build`
3. Restart services: `docker-compose up -d`

## Next Steps (Phase 2)

- Real-time WebSocket streams (Rust data engine)
- Redis message bus
- PostgreSQL database
- Advanced analytics
- Custom alerts