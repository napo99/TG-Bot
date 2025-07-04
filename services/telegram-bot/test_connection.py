#!/usr/bin/env python3
import socket
import subprocess
import sys
import os

def test_port(host, port, timeout=10):
    """Test if a port is open on a host"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        return False

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def main():
    host = "13.239.14.166"
    
    print("=== AWS Deployment Debug Report ===")
    print(f"Target Host: {host}")
    print()
    
    # Test basic connectivity
    print("1. Network Connectivity Test:")
    ping_cmd = f"ping -c 3 {host}"
    stdout, stderr, code = run_command(ping_cmd)
    if code == 0:
        print("✅ Host is reachable")
    else:
        print("❌ Host is not reachable via ping")
        print(f"Error: {stderr}")
    print()
    
    # Test SSH port
    print("2. SSH Connection Test:")
    ssh_open = test_port(host, 22)
    if ssh_open:
        print("✅ SSH port (22) is open")
        # Test SSH authentication
        ssh_cmd = f"ssh -i /Users/screener-m3/.ssh/crypto-bot-key.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@{host} 'echo Connected'"
        stdout, stderr, code = run_command(ssh_cmd)
        if code == 0:
            print("✅ SSH authentication successful")
        else:
            print("❌ SSH authentication failed")
            print(f"Error: {stderr}")
    else:
        print("❌ SSH port (22) is not accessible")
    print()
    
    # Test application ports
    print("3. Application Ports Test:")
    ports = [8080, 8001]
    for port in ports:
        is_open = test_port(host, port)
        if is_open:
            print(f"✅ Port {port} is open")
        else:
            print(f"❌ Port {port} is not accessible")
    print()
    
    # AWS CLI checks
    print("4. AWS CLI Commands:")
    
    # Check instance status
    print("Checking EC2 instance status...")
    aws_cmd = f"aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2 --query 'Reservations[0].Instances[0].State.Name' --output text"
    stdout, stderr, code = run_command(aws_cmd)
    if code == 0:
        print(f"Instance State: {stdout}")
    else:
        print(f"AWS CLI Error: {stderr}")
    
    # Check security groups
    print("Checking security groups...")
    sg_cmd = f"aws ec2 describe-security-groups --group-names crypto-bot-sg --region ap-southeast-2 --query 'SecurityGroups[0].IpPermissions[*].{{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Source:IpRanges[*].CidrIp}}' --output table"
    stdout, stderr, code = run_command(sg_cmd)
    if code == 0:
        print("Security Group Rules:")
        print(stdout)
    else:
        print(f"Security Group Error: {stderr}")

if __name__ == "__main__":
    main()