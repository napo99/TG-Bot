FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed) and create user early
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* \
    && useradd --create-home --shell /bin/bash --uid 1000 app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge \
    && find /usr/local -name "*.pyc" -delete \
    && find /usr/local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy application code and set ownership
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check for telegram bot
HEALTHCHECK --interval=90s --timeout=10s --start-period=30s --retries=2 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-u", "main.py"]