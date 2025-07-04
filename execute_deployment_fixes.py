#!/usr/bin/env python3

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return the result"""
    print(f"🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False, "", str(e)

def main():
    print("🚀 Starting AWS Deployment Fixes")
    print("=================================")
    
    # Change to project directory
    project_dir = "/Users/screener-m3/projects/crypto-assistant"
    os.chdir(project_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Step 1: Fix Security Groups
    print("\n📋 Step 1: Fixing Security Groups")
    print("==================================")
    
    # Get security group ID
    success, stdout, stderr = run_command(
        'aws ec2 describe-security-groups --group-names "crypto-bot-sg" --region ap-southeast-2 --query "SecurityGroups[0].GroupId" --output text',
        "Getting security group ID"
    )
    
    if success:
        security_group_id = stdout.strip()
        print(f"Security Group ID: {security_group_id}")
        
        # Open port 8080
        success, stdout, stderr = run_command(
            f'aws ec2 authorize-security-group-ingress --group-id {security_group_id} --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region ap-southeast-2',
            "Opening port 8080 for webhook"
        )
        
        # Open port 8001
        success, stdout, stderr = run_command(
            f'aws ec2 authorize-security-group-ingress --group-id {security_group_id} --protocol tcp --port 8001 --cidr 0.0.0.0/0 --region ap-southeast-2',
            "Opening port 8001 for market data"
        )
    else:
        print("❌ Failed to get security group ID")
        print(f"Error: {stderr}")
    
    # Step 2: Copy script to EC2
    print("\n📋 Step 2: Copy script to EC2")
    print("==============================")
    
    success, stdout, stderr = run_command(
        'scp -i ~/.ssh/crypto-bot-key.pem fix-ec2-services.sh ec2-user@13.239.14.166:~/',
        "Copying fix script to EC2"
    )
    
    if success:
        print("✅ Script copied successfully")
    else:
        print("❌ Failed to copy script")
        print(f"Error: {stderr}")
    
    # Step 3: Execute script on EC2
    print("\n📋 Step 3: Execute script on EC2")
    print("=================================")
    
    success, stdout, stderr = run_command(
        'ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "chmod +x fix-ec2-services.sh && ./fix-ec2-services.sh"',
        "Executing fix on EC2 instance"
    )
    
    if success:
        print("✅ Services fixed on EC2")
    else:
        print("❌ Failed to fix services on EC2")
        print(f"Error: {stderr}")
    
    # Step 4: Test health endpoints
    print("\n📋 Step 4: Test Health Endpoints")
    print("=================================")
    
    success, stdout, stderr = run_command(
        'curl -s http://13.239.14.166:8080/health',
        "Testing bot health"
    )
    
    if success:
        print("✅ Bot health check passed")
    else:
        print("❌ Bot health check failed")
    
    success, stdout, stderr = run_command(
        'curl -s http://13.239.14.166:8001/health',
        "Testing market data health"
    )
    
    if success:
        print("✅ Market data health check passed")
    else:
        print("❌ Market data health check failed")
    
    # Step 5: Set webhook
    print("\n📋 Step 5: Set Webhook")
    print("=====================")
    
    success, stdout, stderr = run_command(
        'curl -X POST "https://api.telegram.org/bot8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/setWebhook" -H "Content-Type: application/x-www-form-urlencoded" -d "url=http://13.239.14.166:8080/webhook"',
        "Setting webhook"
    )
    
    if success:
        print("✅ Webhook set successfully")
    else:
        print("❌ Failed to set webhook")
        print(f"Error: {stderr}")
    
    print("\n🎉 AWS Deployment Fixes Complete!")
    print("=================================")

if __name__ == "__main__":
    main()