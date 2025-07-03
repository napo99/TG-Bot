# Multi-stage build for Fly.io deployment
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY services/market-data/requirements.txt ./market-data-requirements.txt
COPY services/telegram-bot/requirements.txt ./telegram-bot-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r market-data-requirements.txt
RUN pip install --no-cache-dir -r telegram-bot-requirements.txt

# Copy application code
COPY services/ ./services/

# Create data directory
RUN mkdir -p ./data

# Copy startup script
COPY start-fly.sh ./start-fly.sh
RUN chmod +x start-fly.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start services
CMD ["./start-fly.sh"]