import subprocess
import sys

print("Running API tests...")

# Run the test script
result = subprocess.run([sys.executable, 'test_direct.py'], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print(f"\nReturn code: {result.returncode}")