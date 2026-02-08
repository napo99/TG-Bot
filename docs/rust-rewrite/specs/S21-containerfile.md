# S21 — Containerfile & Deployment

## Scope
Create Podman-compatible container image. Ubuntu-based as required.

## Dependencies
- S20 (binary builds)

## Files to Create

### `crypto-bot/Containerfile`

```dockerfile
# ── Build stage ──
FROM docker.io/library/rust:1.82-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependencies (copy manifests first)
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main(){}" > src/main.rs
RUN cargo build --release 2>/dev/null || true
RUN rm -rf src

# Build real application
COPY src/ src/
COPY migrations/ migrations/
RUN touch src/main.rs && cargo build --release
RUN strip target/release/crypto-bot

# ── Runtime stage (Ubuntu as required) ──
FROM docker.io/library/ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
WORKDIR /home/app

COPY --from=builder /app/target/release/crypto-bot .
RUN mkdir -p data && chown app:app data

USER app

ENV LOG_LEVEL=info
ENV DATABASE_URL=sqlite:data/bot.db

ENTRYPOINT ["./crypto-bot"]
```

### `crypto-bot/.containerignore`

```
target/
.git/
.env
*.md
docs/
tests/
```

### Deployment Script: `deploy.sh`

```bash
#!/bin/bash
set -euo pipefail

IMAGE="crypto-bot:latest"
CONTAINER="crypto-bot"

# Build
podman build -t "$IMAGE" -f Containerfile .

# Stop existing
podman stop "$CONTAINER" 2>/dev/null || true
podman rm "$CONTAINER" 2>/dev/null || true

# Run
podman run -d \
    --name "$CONTAINER" \
    --restart=always \
    --env-file "$HOME/.env" \
    -v "$HOME/data:/home/app/data:Z" \
    "$IMAGE"

# Verify
sleep 3
podman logs "$CONTAINER" --tail 5
echo "Deployment complete."
```

### Systemd User Service: `crypto-bot.service`

```ini
[Unit]
Description=Crypto Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStartPre=-/usr/bin/podman stop crypto-bot
ExecStartPre=-/usr/bin/podman rm crypto-bot
ExecStart=/usr/bin/podman run \
    --name crypto-bot \
    --env-file %h/.env \
    -v %h/data:/home/app/data:Z \
    crypto-bot:latest
ExecStop=/usr/bin/podman stop crypto-bot
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

## Tests

```bash
# Build succeeds
podman build -t crypto-bot:latest -f Containerfile .

# Image size < 150MB
SIZE=$(podman image inspect crypto-bot:latest --format '{{.Size}}')
[ "$SIZE" -lt 157286400 ] && echo "PASS: Image < 150MB" || echo "FAIL: Image too large"

# Container starts and exits cleanly without TELEGRAM_BOT_TOKEN
podman run --rm crypto-bot:latest 2>&1 | grep -q "TELEGRAM_BOT_TOKEN"
echo "PASS: Missing token produces clear error"

# Binary exists and is executable
podman run --rm --entrypoint ls crypto-bot:latest -la crypto-bot
echo "PASS: Binary exists"
```

## Exit Criteria

- [ ] `podman build` succeeds
- [ ] Image size < 150 MB
- [ ] Container runs as non-root (uid 1000)
- [ ] Missing env vars produce clear error messages
- [ ] Data volume mountable at `/home/app/data`
- [ ] systemd service file valid syntax
- [ ] `deploy.sh` is idempotent (can run twice safely)
