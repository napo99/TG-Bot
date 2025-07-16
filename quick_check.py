#!/usr/bin/env python3
"""
SIMPLE DIAGNOSTIC TOOL - For Claude to quickly identify issues
Purpose: One tool, quick answers, simple fixes
"""

import docker
import requests
import psutil
import time
from typing import Dict, List

def check_docker() -> Dict:
    """Check if Docker is working"""
    try:
        client = docker.from_env()
        client.ping()
        return {"status": "ok", "message": "Docker running"}
    except Exception as e:
        return {"status": "error", "message": f"Docker issue: {e}"}

def check_containers() -> Dict:
    """Check crypto-assistant containers"""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        # Expected containers
        expected = ["telegram-bot", "market-data"]
        results = {}
        
        for expected_name in expected:
            found = False
            for container in containers:
                if expected_name in container.name.lower():
                    found = True
                    results[expected_name] = {
                        "status": container.status,
                        "healthy": container.status == "running"
                    }
                    break
            
            if not found:
                results[expected_name] = {
                    "status": "missing",
                    "healthy": False
                }
        
        all_healthy = all(r["healthy"] for r in results.values())
        
        return {
            "status": "ok" if all_healthy else "error",
            "containers": results,
            "all_healthy": all_healthy
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Container check failed: {e}"}

def check_apis() -> Dict:
    """Check if APIs are responding"""
    endpoints = [
        ("telegram", "http://localhost:8080/health"),
        ("market_data", "http://localhost:8001/health"),
        ("analysis", "http://localhost:8001/comprehensive_analysis")
    ]
    
    results = {}
    
    for name, url in endpoints:
        try:
            if "analysis" in name:
                response = requests.post(url, 
                    json={"symbol": "BTC/USDT", "timeframe": "15m"}, 
                    timeout=5)
            else:
                response = requests.get(url, timeout=5)
            
            results[name] = {
                "status": "ok" if response.status_code == 200 else "error",
                "code": response.status_code
            }
        except Exception as e:
            results[name] = {
                "status": "error",
                "error": str(e)
            }
    
    all_ok = all(r["status"] == "ok" for r in results.values())
    
    return {
        "status": "ok" if all_ok else "error",
        "endpoints": results,
        "all_ok": all_ok
    }

def check_system() -> Dict:
    """Check system resources"""
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        
        # For AWS t3.micro (1GB), anything over 85% is critical
        memory_critical = memory.percent > 85
        memory_warning = memory.percent > 70
        
        return {
            "status": "critical" if memory_critical else "warning" if memory_warning else "ok",
            "memory_percent": round(memory.percent, 1),
            "memory_available_mb": round(memory.available / 1024**2, 0),
            "cpu_percent": round(cpu, 1),
            "disk_percent": round((disk.used / disk.total) * 100, 1),
            "memory_critical": memory_critical
        }
    except Exception as e:
        return {"status": "error", "message": f"System check failed: {e}"}

def run_diagnosis() -> Dict:
    """Run complete diagnosis"""
    print("🔍 Running diagnosis...")
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "docker": check_docker(),
        "containers": check_containers(),
        "apis": check_apis(),
        "system": check_system()
    }
    
    # Determine overall health
    issues = []
    
    if results["docker"]["status"] != "ok":
        issues.append("Docker not working")
    
    if results["containers"]["status"] != "ok":
        issues.append("Containers not running")
    
    if results["apis"]["status"] != "ok":
        issues.append("APIs not responding")
    
    if results["system"]["status"] == "critical":
        issues.append("Critical memory usage")
    
    results["overall"] = {
        "healthy": len(issues) == 0,
        "issues": issues
    }
    
    return results

def print_diagnosis(results: Dict):
    """Print diagnosis results"""
    print("\n" + "="*50)
    print("🏥 CRYPTO ASSISTANT DIAGNOSIS")
    print("="*50)
    print(f"Time: {results['timestamp']}")
    
    # Overall status
    if results["overall"]["healthy"]:
        print("✅ SYSTEM HEALTHY")
    else:
        print("❌ ISSUES DETECTED:")
        for issue in results["overall"]["issues"]:
            print(f"   • {issue}")
    
    print("\n🔍 DETAILS:")
    
    # Docker
    docker = results["docker"]
    emoji = "✅" if docker["status"] == "ok" else "❌"
    print(f"   {emoji} Docker: {docker.get('message', docker['status'])}")
    
    # Containers
    containers = results["containers"]
    if "containers" in containers:
        for name, info in containers["containers"].items():
            emoji = "✅" if info["healthy"] else "❌"
            print(f"   {emoji} {name}: {info['status']}")
    
    # APIs
    apis = results["apis"]
    if "endpoints" in apis:
        for name, info in apis["endpoints"].items():
            emoji = "✅" if info["status"] == "ok" else "❌"
            error = f" ({info.get('error', info.get('code', ''))})" if info["status"] != "ok" else ""
            print(f"   {emoji} {name}_api{error}")
    
    # System
    system = results["system"]
    if "memory_percent" in system:
        memory_emoji = "🚨" if system.get("memory_critical") else "⚠️" if system["memory_percent"] > 70 else "✅"
        print(f"   {memory_emoji} Memory: {system['memory_percent']}% ({system['memory_available_mb']:.0f}MB free)")
        print(f"   📊 CPU: {system['cpu_percent']}%")
    
    # Quick fixes
    if not results["overall"]["healthy"]:
        print("\n🔧 QUICK FIXES:")
        for issue in results["overall"]["issues"]:
            if "docker" in issue.lower():
                print("   → Start Docker service")
            elif "container" in issue.lower():
                print("   → Run: docker-compose up -d")
            elif "api" in issue.lower():
                print("   → Check logs: docker-compose logs")
            elif "memory" in issue.lower():
                print("   → Clean up: docker system prune")
                print("   → Restart: docker-compose restart")

def main():
    """Main function"""
    import sys
    
    # Simple command line handling
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        import json
        results = run_diagnosis()
        print(json.dumps(results, indent=2))
    else:
        results = run_diagnosis()
        print_diagnosis(results)

if __name__ == "__main__":
    main()