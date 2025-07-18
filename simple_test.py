import subprocess
import sys

def run_simple_test():
    """Simple test to check if the services are running"""
    
    print("=== DOCKER STATUS CHECK ===")
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
        print(f"Docker containers running:")
        print(result.stdout)
        if result.stderr:
            print(f"Docker errors: {result.stderr}")
    except Exception as e:
        print(f"Error checking Docker: {e}")
    
    print("\n=== SIMPLE CURL TEST ===")
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:8001/health'], capture_output=True, text=True, timeout=10)
        print(f"Health check response: {result.stdout}")
        if result.stderr:
            print(f"Curl errors: {result.stderr}")
    except Exception as e:
        print(f"Error with curl: {e}")

if __name__ == "__main__":
    run_simple_test()