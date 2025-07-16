# EC2 Instance Monitoring & Auto-Recovery

## 🚨 Why Your Bot Went Down

### Common Causes:
1. **Resource Exhaustion**: t3.micro has only 1GB RAM
2. **Docker Build Operations**: Consume significant memory
3. **Cost-Saving Auto-Stop**: Many users configure this
4. **CPU Credit Depletion**: t3 instances have burst limits

## 🛡️ Prevention & Monitoring Setup

### 1. CloudWatch Alarms (Free Tier)
```bash
# Create instance status alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "TelegramBot-InstanceDown" \
  --alarm-description "Alert when Telegram bot instance is down" \
  --alarm-actions arn:aws:sns:ap-southeast-2:YOUR_ACCOUNT_ID:YOUR_SNS_TOPIC \
  --metric-name StatusCheckFailed \
  --namespace AWS/EC2 \
  --statistic Maximum \
  --dimensions Name=InstanceId,Value=i-0be83d48202d03ef1 \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

### 2. Auto-Recovery Setup
```bash
# Enable auto-recovery for instance
aws ec2 create-instance-recovery-alarm \
  --instance-id i-0be83d48202d03ef1 \
  --alarm-name "TelegramBot-AutoRecover"
```

### 3. External Monitoring (Free Services)
```bash
# UptimeRobot - Free monitoring
# 1. Sign up at https://uptimerobot.com
# 2. Add monitor for http://13.239.14.166:8080/health
# 3. Set check interval to 5 minutes
# 4. Configure email/SMS alerts

# Healthchecks.io - Free tier
# 1. Sign up at https://healthchecks.io
# 2. Create check with 5-minute interval
# 3. Add this to your EC2 crontab:
*/5 * * * * curl -fsS --retry 3 https://hc-ping.com/YOUR_UUID || echo "Health check failed"
```

### 4. Instance Keep-Alive Script
```bash
# Add to EC2 instance crontab
cat > /home/ec2-user/keep_alive.sh << 'EOF'
#!/bin/bash
# Keep services running

cd /home/ec2-user/TG-Bot

# Check if containers are running
if ! docker ps | grep -q telegram-bot; then
    echo "$(date): Restarting services..." >> /var/log/keep_alive.log
    docker-compose -f docker-compose.aws.yml up -d
fi

# Check health
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "$(date): Health check failed, restarting..." >> /var/log/keep_alive.log
    docker-compose -f docker-compose.aws.yml restart telegram-bot
fi

# Clean up old Docker resources to prevent disk full
docker system prune -f --volumes >> /var/log/docker_cleanup.log 2>&1
EOF

chmod +x /home/ec2-user/keep_alive.sh
crontab -e
# Add: */5 * * * * /home/ec2-user/keep_alive.sh
```

### 5. Resource Monitoring
```bash
# Add to EC2 instance
cat > /home/ec2-user/resource_monitor.sh << 'EOF'
#!/bin/bash
# Monitor and alert on resource usage

MEMORY_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')

if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    echo "WARNING: Memory usage critical: $MEMORY_USAGE%" | mail -s "Bot Server Memory Alert" your-email@example.com
fi

if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage critical: $DISK_USAGE%" | mail -s "Bot Server Disk Alert" your-email@example.com
    docker system prune -af
fi
EOF

chmod +x /home/ec2-user/resource_monitor.sh
# Add to crontab: */15 * * * * /home/ec2-user/resource_monitor.sh
```

## 📱 Telegram Self-Monitoring Bot

```python
# monitoring_bot.py - Run on separate cheap VPS or locally
import requests
import time
from telegram import Bot

BOT_TOKEN = "YOUR_MONITORING_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
bot = Bot(token=BOT_TOKEN)

def check_main_bot():
    try:
        response = requests.get("http://13.239.14.166:8080/health", timeout=10)
        if response.status_code != 200:
            bot.send_message(chat_id=CHAT_ID, text="🚨 ALERT: Telegram bot is DOWN! Health check failed.")
            return False
    except:
        bot.send_message(chat_id=CHAT_ID, text="🚨 ALERT: Telegram bot is UNREACHABLE! Instance may be down.")
        return False
    return True

# Check every 5 minutes
while True:
    if not check_main_bot():
        # Send recovery instructions
        bot.send_message(chat_id=CHAT_ID, text="""
Recovery steps:
1. Check AWS Console
2. Run: aws ec2 start-instances --instance-ids i-0be83d48202d03ef1
3. SSH and restart Docker services
        """)
    time.sleep(300)  # 5 minutes
```

## 🎯 Best Practices to Prevent Downtime

1. **Use Larger Instance**: t3.small (2GB RAM) for production
2. **Enable Auto-Recovery**: AWS feature for automatic restart
3. **External Monitoring**: UptimeRobot + Healthchecks.io (both free)
4. **Resource Limits**: Enforce Docker memory limits
5. **Regular Cleanup**: Automated Docker pruning
6. **Backup Bot**: Secondary notification system

## 💰 Cost Considerations

| Solution | Cost | Reliability |
|----------|------|-------------|
| t3.micro + Monitoring | ~$0-5/month | Medium |
| t3.small + Auto-recovery | ~$15/month | High |
| ECS Fargate | ~$20/month | Very High |
| Lambda + API Gateway | ~$0-10/month | Highest |

## 🚀 Immediate Actions

1. **Start the instance now**
2. **Set up UptimeRobot** (free, 5-minute checks)
3. **Enable CloudWatch alarm** (free tier eligible)
4. **Add keep-alive script** to EC2
5. **Document in CLAUDE.md** for future reference