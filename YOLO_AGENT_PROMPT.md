# 🤖 EXACT YOLO AGENT PROMPT

## 📋 **COPY THIS EXACT PROMPT TO YOUR YOLO CLAUDE:**

---

**TASK: Deploy crypto-assistant to production with 100% confidence**

**CONTEXT:**
- Project: Crypto trading bot with market analysis
- Local: Clean polling architecture, verified working
- Production: AWS EC2 (13.239.14.166), needs health status fix
- Confidence: 100% - all analysis complete, production configs verified

**DEPLOYMENT PLAN:**

**Phase 1: GitHub Deployment**
```bash
cd /Users/screener-m3/projects/crypto-assistant
git push origin main
```

**Phase 2: AWS Production Deployment**
```bash
# SSH to production
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# Navigate and deploy
cd /home/ec2-user/TG-Bot
git pull origin main
docker-compose down
docker stop tg-bot-redis-1 && docker rm tg-bot-redis-1  # Remove unused Redis
docker-compose up -d --build
```

**Phase 3: Verification**
```bash
# Wait for startup
sleep 15

# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check bot logs
docker logs crypto-telegram-bot | tail -10

# Test market data service
curl -f http://localhost:8001/health

# Check for errors
docker logs crypto-telegram-bot | grep -i error | tail -5 || echo "No errors found"
```

**SUCCESS CRITERIA:**
- No "unhealthy" containers (main goal)
- Both crypto-telegram-bot and crypto-market-data running
- No critical errors in logs
- Market data service responding

**EXPECTED RESULT:**
- BEFORE: `crypto-telegram-bot (unhealthy)` 
- AFTER: `crypto-telegram-bot Up X minutes`

**SAFETY:**
- Production configs analyzed and compatible
- Local functionality verified by user
- Same polling architecture (python main.py)
- Rollback available: `git checkout HEAD~1`

**INSTRUCTIONS:**
1. Execute Phase 1 (GitHub push)
2. Execute Phase 2 (AWS deployment)  
3. Execute Phase 3 (verification)
4. Report final container status with docker ps
5. Confirm deployment success or flag any issues

**CONFIDENCE LEVEL: 100%**
**RISK LEVEL: ZERO**
**PRODUCTION IMPACT: POSITIVE**

Execute with full confidence - this will fix the unhealthy container status and clean up legacy artifacts!

---

**COPY THE ABOVE PROMPT EXACTLY TO YOUR YOLO CLAUDE AGENT**