#!/bin/bash

# Crypto Assistant Logging System Setup Script
# This script sets up the comprehensive logging infrastructure

set -e

echo "🔧 Setting up Crypto Assistant Logging System..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create log directories
print_status "Creating log directories..."
mkdir -p data/logs/{telegram-bot,market-data,system,aggregated}
mkdir -p data/logs/telegram-bot/{archived,debug}
mkdir -p data/logs/market-data/{archived,debug}
mkdir -p data/logs/system/{archived,debug}

# Set proper permissions
print_status "Setting log directory permissions..."
chmod -R 755 data/logs
chmod -R 777 data/logs/telegram-bot
chmod -R 777 data/logs/market-data
chmod -R 777 data/logs/system

# Create logging configuration file
print_status "Creating logging configuration..."
cat > config/logging.json << 'EOF'
{
  "check_interval_seconds": 10,
  "alert_cooldown_minutes": 15,
  "max_alerts_per_hour": 20,
  "webhook_urls": [],
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": "",
    "to_addresses": []
  },
  "log_files": ["*.log"],
  "exclude_patterns": ["DEBUG"],
  "custom_patterns": {
    "error_patterns": [
      "CRITICAL",
      "FATAL",
      "ERROR",
      "Exception",
      "failed",
      "timeout"
    ],
    "performance_patterns": [
      "slow",
      "timeout",
      "memory",
      "cpu"
    ]
  },
  "retention": {
    "log_files_days": 30,
    "archived_files_days": 90,
    "alert_history_days": 7
  },
  "monitoring": {
    "enabled": true,
    "real_time_alerts": true,
    "performance_tracking": true,
    "error_tracking": true
  }
}
EOF

# Create environment variables for logging
print_status "Setting up logging environment variables..."
cat >> .env << 'EOF'

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/app/logs
LOG_CONSOLE=true
LOG_FILE=true
LOG_MAX_FILE_SIZE=50
LOG_BACKUP_COUNT=5

# Monitoring Configuration
MONITORING_ENABLED=true
REAL_TIME_ALERTS=true
WEBHOOK_ALERTS=false
EMAIL_ALERTS=false

# Performance Thresholds
ERROR_RATE_WARNING=5.0
ERROR_RATE_CRITICAL=10.0
RESPONSE_TIME_WARNING=2000
RESPONSE_TIME_CRITICAL=5000
MEMORY_WARNING=400
MEMORY_CRITICAL=800
EOF

# Install Python dependencies for logging tools
print_status "Installing Python dependencies for logging..."
pip install -r <(cat << 'EOF'
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
aiofiles>=23.0.0
psutil>=5.9.0
EOF
)

# Create log rotation configuration
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/crypto-assistant > /dev/null << 'EOF'
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        docker exec crypto-telegram-bot pkill -USR1 -f python || true
        docker exec crypto-market-data pkill -USR1 -f python || true
    endscript
}

/app/logs/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

# Create systemd service for log monitoring (optional)
print_status "Creating log monitoring service..."
cat > config/crypto-log-monitor.service << 'EOF'
[Unit]
Description=Crypto Assistant Log Monitor
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crypto-assistant
ExecStart=/usr/bin/python3 tools/log_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create log analysis scripts
print_status "Creating log analysis scripts..."

# Daily log report script
cat > scripts/daily_log_report.sh << 'EOF'
#!/bin/bash

# Generate daily log analysis report
REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="data/logs/reports/daily_report_${REPORT_DATE}.json"

echo "Generating daily log report for ${REPORT_DATE}..."

# Create reports directory
mkdir -p data/logs/reports

# Run log analyzer
cd tools
python3 -c "
from log_analyzer import LogAnalyzer
import json

analyzer = LogAnalyzer('/app/logs')
report = analyzer.generate_system_health_report(hours=24)

with open('../${REPORT_FILE}', 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f'Report generated: ${REPORT_FILE}')
print(f'System Health Score: {report.get(\"overall_health_score\", \"N/A\")}')
"

echo "Daily report completed: ${REPORT_FILE}"
EOF

chmod +x scripts/daily_log_report.sh

# Error analysis script
cat > scripts/analyze_errors.sh << 'EOF'
#!/bin/bash

# Analyze recent errors
HOURS=${1:-24}

echo "Analyzing errors from last ${HOURS} hours..."

cd tools
python3 -c "
from log_analyzer import LogAnalyzer
import json

analyzer = LogAnalyzer('/app/logs')
error_analysis = analyzer.analyze_error_patterns(hours=${HOURS})

print('=' * 50)
print('ERROR ANALYSIS REPORT')
print('=' * 50)
print(f'Total Errors: {error_analysis.get(\"total_errors\", 0)}')
print(f'Error Rate: {error_analysis.get(\"error_rate\", 0):.2f}%')
print()

if error_analysis.get('top_error_messages'):
    print('Top Error Messages:')
    for i, error in enumerate(error_analysis['top_error_messages'][:5], 1):
        print(f'{i}. {error[\"message\"]} ({error[\"count\"]} times)')
    print()

if error_analysis.get('critical_errors'):
    print('Critical Errors Requiring Attention:')
    for error in error_analysis['critical_errors'][:3]:
        print(f'- {error.get(\"message\", \"Unknown\")}')
print('=' * 50)
"
EOF

chmod +x scripts/analyze_errors.sh

# Performance monitoring script
cat > scripts/monitor_performance.sh << 'EOF'
#!/bin/bash

# Monitor system performance
HOURS=${1:-1}

echo "Monitoring performance metrics from last ${HOURS} hour(s)..."

cd tools
python3 -c "
from log_analyzer import LogAnalyzer
import json

analyzer = LogAnalyzer('/app/logs')
perf_analysis = analyzer.analyze_performance_metrics(hours=${HOURS})

print('=' * 50)
print('PERFORMANCE ANALYSIS REPORT')
print('=' * 50)

response_times = perf_analysis.get('response_time_analysis', {})
if response_times.get('mean'):
    print(f'Average Response Time: {response_times[\"mean\"]:.2f}ms')
    print(f'95th Percentile: {response_times[\"p95\"]:.2f}ms')
    print(f'99th Percentile: {response_times[\"p99\"]:.2f}ms')
    print()

memory_analysis = perf_analysis.get('memory_usage_analysis', {})
if memory_analysis:
    print('Memory Usage Analysis:')
    print(json.dumps(memory_analysis, indent=2))
    print()

if perf_analysis.get('performance_alerts'):
    print('Performance Alerts:')
    for alert in perf_analysis['performance_alerts'][:5]:
        print(f'- {alert}')

print('=' * 50)
"
EOF

chmod +x scripts/monitor_performance.sh

# Create Docker logging override
print_status "Creating Docker Compose logging override..."
cat > docker-compose.logging.yml << 'EOF'
version: '3.8'

services:
  telegram-bot:
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_DIR=/app/logs
      - LOG_CONSOLE=true
      - LOG_FILE=true
      - SERVICE_NAME=telegram-bot
    volumes:
      - ./data/logs/telegram-bot:/app/logs:rw
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        compress: "true"
        labels: "service=telegram-bot,project=crypto-assistant"

  market-data:
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_DIR=/app/logs
      - LOG_CONSOLE=true
      - LOG_FILE=true
      - SERVICE_NAME=market-data
    volumes:
      - ./data/logs/market-data:/app/logs:rw
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        compress: "true"
        labels: "service=market-data,project=crypto-assistant"

  redis:
    logging:
      driver: "json-file"
      options:
        max-size: "5m"
        max-file: "3"
        compress: "true"
        labels: "service=redis,project=crypto-assistant"
EOF

# Create monitoring startup script
print_status "Creating monitoring startup script..."
cat > scripts/start_monitoring.sh << 'EOF'
#!/bin/bash

# Start log monitoring system
echo "Starting Crypto Assistant Log Monitoring..."

# Check if Docker containers are running
if ! docker ps | grep -q crypto-telegram-bot; then
    echo "Warning: Telegram bot container not running"
fi

if ! docker ps | grep -q crypto-market-data; then
    echo "Warning: Market data container not running"
fi

# Start log monitor in background
cd tools
nohup python3 log_monitor.py > ../data/logs/system/monitor.log 2>&1 &
MONITOR_PID=$!

echo "Log monitor started with PID: ${MONITOR_PID}"
echo ${MONITOR_PID} > ../data/logs/system/monitor.pid

echo "Log monitoring system started successfully!"
echo "Check logs at: data/logs/system/monitor.log"
EOF

chmod +x scripts/start_monitoring.sh

# Create monitoring stop script
cat > scripts/stop_monitoring.sh << 'EOF'
#!/bin/bash

# Stop log monitoring system
echo "Stopping Crypto Assistant Log Monitoring..."

if [ -f data/logs/system/monitor.pid ]; then
    PID=$(cat data/logs/system/monitor.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "Log monitor (PID: ${PID}) stopped"
    else
        echo "Log monitor process not found"
    fi
    rm -f data/logs/system/monitor.pid
else
    echo "No monitor PID file found"
fi

echo "Log monitoring system stopped"
EOF

chmod +x scripts/stop_monitoring.sh

# Create comprehensive logging test script
print_status "Creating logging test script..."
cat > scripts/test_logging.sh << 'EOF'
#!/bin/bash

# Test the logging system
echo "Testing Crypto Assistant Logging System..."

# Test 1: Check log directories
echo "1. Checking log directories..."
for dir in "data/logs/telegram-bot" "data/logs/market-data" "data/logs/system"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing"
    fi
done

# Test 2: Test log analyzer
echo "2. Testing log analyzer..."
cd tools
python3 -c "
from log_analyzer import LogAnalyzer
analyzer = LogAnalyzer('/app/logs')
print('  ✓ Log analyzer initialized successfully')
" 2>/dev/null && echo "  ✓ Log analyzer works" || echo "  ✗ Log analyzer failed"

# Test 3: Test log monitor
echo "3. Testing log monitor..."
python3 -c "
from log_monitor import RealTimeLogMonitor
monitor = RealTimeLogMonitor('/app/logs')
print('  ✓ Log monitor initialized successfully')
" 2>/dev/null && echo "  ✓ Log monitor works" || echo "  ✗ Log monitor failed"

# Test 4: Test structured logger
echo "4. Testing structured logger..."
python3 -c "
import sys
sys.path.append('../services')
from shared.structured_logger import create_structured_logger
logger = create_structured_logger('test', 'test_module')
logger.log_business_event('test_event', {'status': 'success'})
print('  ✓ Structured logger works')
" 2>/dev/null && echo "  ✓ Structured logger works" || echo "  ✗ Structured logger failed"

echo "Logging system test completed!"
EOF

chmod +x scripts/test_logging.sh

# Create log cleanup script
print_status "Creating log cleanup script..."
cat > scripts/cleanup_logs.sh << 'EOF'
#!/bin/bash

# Clean up old logs based on retention policy
RETENTION_DAYS=${1:-30}

echo "Cleaning up logs older than ${RETENTION_DAYS} days..."

# Archive old logs
find data/logs -name "*.log" -type f -mtime +${RETENTION_DAYS} -exec gzip {} \;

# Move archived logs
find data/logs -name "*.log.gz" -type f -exec mv {} data/logs/archived/ \;

# Remove very old archived logs (90 days)
find data/logs/archived -name "*.log.gz" -type f -mtime +90 -delete

# Clean up old reports
find data/logs/reports -name "*.json" -type f -mtime +7 -delete

echo "Log cleanup completed"
EOF

chmod +x scripts/cleanup_logs.sh

# Final setup message
print_status "Logging system setup completed successfully!"
echo ""
echo "📋 Setup Summary:"
echo "  ✓ Log directories created"
echo "  ✓ Configuration files generated"
echo "  ✓ Docker logging configured"
echo "  ✓ Log rotation setup"
echo "  ✓ Monitoring scripts created"
echo "  ✓ Analysis tools ready"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start services with logging: docker-compose -f docker-compose.yml -f docker-compose.logging.yml up -d"
echo "  2. Test logging system: ./scripts/test_logging.sh"
echo "  3. Start monitoring: ./scripts/start_monitoring.sh"
echo "  4. Generate daily report: ./scripts/daily_log_report.sh"
echo ""
echo "📊 Available Commands:"
echo "  • ./scripts/analyze_errors.sh [hours] - Analyze recent errors"
echo "  • ./scripts/monitor_performance.sh [hours] - Monitor performance"
echo "  • ./scripts/cleanup_logs.sh [days] - Clean up old logs"
echo "  • ./scripts/start_monitoring.sh - Start real-time monitoring"
echo "  • ./scripts/stop_monitoring.sh - Stop monitoring"
echo ""
print_status "Comprehensive logging system is ready! 🎉"