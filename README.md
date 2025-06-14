# Crypto Trading Assistant

A modular crypto trading assistant that integrates with Telegram for portfolio tracking, market analysis, and trade management.

## Architecture

- **telegram-bot**: Python service handling Telegram commands and user interaction
- **market-data**: Python service for fetching market data using ccxt
- **Database**: SQLite for Phase 1, PostgreSQL for production

## Phase 1 Features

- `/price <symbol>` - Get current price
- `/balance` - Show account balance
- `/positions` - Show open positions
- `/pnl` - Show P&L summary

## Setup

1. Copy `.env.example` to `.env` and configure:
   - `TELEGRAM_BOT_TOKEN`
   - Exchange API keys

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Development

Each service is independently deployable and testable.