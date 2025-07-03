# 🆓 AWS Free Tier (12 Months) - Automation Analysis

## 🎯 **AWS Free Tier Specifications**
- **Instance:** t2.micro (1 vCPU, 1GB RAM)
- **Storage:** 30GB EBS storage
- **Network:** 15GB data transfer/month
- **Duration:** 12 months from account creation
- **Cost:** $0 for 12 months, then ~$8.50/month

## 🤖 **Claude Automation Level: 85% Automated**

### **✅ What Claude CAN Automate (Most of the work):**

#### **EC2 Instance Creation & Setup:**
```bash
# 1. Create security group
aws ec2 create-security-group \
  --group-name crypto-bot-sg \
  --description "Security group for crypto bot"

# 2. Configure firewall rules
aws ec2 authorize-security-group-ingress \
  --group-name crypto-bot-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name crypto-bot-sg \
  --protocol tcp \
  --port 8001 \
  --cidr 0.0.0.0/0

# 3. Launch free tier instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t2.micro \
  --key-name your-key-pair \
  --security-groups crypto-bot-sg

# 4. Get instance IP and connect
INSTANCE_IP=$(aws ec2 describe-instances --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
```

#### **Complete Server Setup:**
```bash
# Claude can generate this script and run it:
ssh -i your-key.pem ec2-user@$INSTANCE_IP << 'EOF'
# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository
git clone https://github.com/your-username/crypto-assistant.git
cd crypto-assistant

# Set up environment variables
cat > .env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=your-token-here
TELEGRAM_CHAT_ID=your-chat-id
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
LOG_LEVEL=INFO
ENVEOF

# Start the bot
docker-compose up -d

# Set up auto-restart on reboot
echo "@reboot cd /home/ec2-user/crypto-assistant && docker-compose up -d" | crontab -
EOF
```

### **❌ What You Must Do Manually (15 minutes, one-time):**

#### **1. AWS Account Setup (5 minutes):**
- Create AWS account at aws.amazon.com
- Verify email and phone
- Add credit card (required even for free tier)

#### **2. SSH Key Creation (3 minutes):**
```bash
# You need to create this in AWS console:
# EC2 → Key Pairs → Create Key Pair → Download .pem file
```

#### **3. Get Access Keys (2 minutes):**
```bash
# IAM → Users → Create User → Programmatic Access
# Save the Access Key ID and Secret Access Key
```

#### **4. Initial AWS CLI Setup (5 minutes):**
```bash
# Install AWS CLI on your machine
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure (you provide the keys)
aws configure
```

## 🚀 **Step-by-Step: Free Tier Setup Process**

### **Phase 1: Your Manual Setup (15 minutes total)**

**Step 1: AWS Account (5 min)**
1. Go to aws.amazon.com → "Create AWS Account"
2. Enter email, password, account name
3. Verify phone number
4. Add credit card (won't be charged for free tier)

**Step 2: Create SSH Key (3 min)**
1. AWS Console → EC2 → Key Pairs
2. "Create Key Pair" → Name: "crypto-bot-key"
3. Download the .pem file
4. `chmod 400 crypto-bot-key.pem`

**Step 3: Get Access Keys (2 min)**
1. AWS Console → IAM → Users → "Create User"
2. User name: "claude-automation"
3. Check "Programmatic access"
4. Attach policy: "EC2FullAccess"
5. Save Access Key ID and Secret

**Step 4: AWS CLI Setup (5 min)**
```bash
# Install AWS CLI (I can help with this)
# Then configure with your keys:
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key  
# Default region: us-east-1
# Default output: json
```

### **Phase 2: Claude's Automated Deployment (10 minutes)**

Once you complete Phase 1, I can run these commands:

```bash
# 1. Create security group and rules
aws ec2 create-security-group --group-name crypto-bot-sg --description "Crypto bot security group"
aws ec2 authorize-security-group-ingress --group-name crypto-bot-sg --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name crypto-bot-sg --protocol tcp --port 8001 --cidr 0.0.0.0/0

# 2. Launch free tier instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t2.micro \
  --key-name crypto-bot-key \
  --security-groups crypto-bot-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=crypto-bot}]'

# 3. Wait for instance to be ready
aws ec2 wait instance-running --instance-ids i-1234567890abcdef0

# 4. Get public IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=crypto-bot" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# 5. Set up server automatically
ssh -i crypto-bot-key.pem ec2-user@$INSTANCE_IP < setup-script.sh

# 6. Deploy your bot
scp -i crypto-bot-key.pem docker-compose.yml ec2-user@$INSTANCE_IP:~/
ssh -i crypto-bot-key.pem ec2-user@$INSTANCE_IP "docker-compose up -d"
```

## 📊 **Automation Comparison**

| Service | Your Manual Work | Claude's Automation | Total Setup Time |
|---------|------------------|-------------------|------------------|
| **AWS Free Tier** | 15 min (one-time) | 10 min | 25 min |
| **AWS Lightsail** | 7 min (one-time) | 5 min | 12 min |
| **Railway** | 2 min (GitHub) | 3 min | 5 min |
| **Fly.io Upgrade** | 0 min | 1 min | 1 min |

## 🎯 **Free Tier Pros & Cons**

### **✅ Pros:**
- **FREE for 12 months** (save $120+ vs other options)
- **1GB RAM** (4x better than current Fly.io)
- **Full Linux server** (complete control)
- **Learning experience** (valuable AWS skills)
- **Claude can automate 85%** of the setup

### **❌ Cons:**
- **15 minutes manual setup** (vs 2-7 min for others)
- **More moving parts** (security groups, SSH keys, etc.)
- **After 12 months:** $8.50/month (but still cheaper than others)

## 💡 **Recommendation**

If you want to **save money** and don't mind **15 minutes of initial setup**, the AWS free tier is excellent value:

- **12 months free** = Save $120+
- **1GB RAM** = 4x better performance than current setup
- **Claude automates most of it** after your initial setup

**The 15 minutes you spend now saves you $10/month for a year.**

Want me to guide you through the 15-minute manual setup, then automate everything else?