#!/usr/bin/env python3
import subprocess
import os

os.chdir('/Users/screener-m3/projects/crypto-assistant')

def run_git_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

print("=== Git Status ===")
print(run_git_command("git status"))

print("\n=== Current Branch ===")
print(run_git_command("git branch --show-current"))

print("\n=== All Branches ===")
print(run_git_command("git branch -a"))

print("\n=== Commits in aws-deployment not in main ===")
print(run_git_command("git log aws-deployment --not main --oneline"))

print("\n=== Commits in main not in aws-deployment ===")
print(run_git_command("git log main --not aws-deployment --oneline"))

print("\n=== Uncommitted changes ===")
print(run_git_command("git diff --name-only"))

print("\n=== Untracked files ===")
print(run_git_command("git ls-files --others --exclude-standard"))

print("\n=== Remote status ===")
print(run_git_command("git remote -v"))

print("\n=== Compare with remote ===")
print("Local aws-deployment vs origin/aws-deployment:")
print(run_git_command("git rev-list --left-right --count aws-deployment...origin/aws-deployment"))

print("\nLocal main vs origin/main:")
print(run_git_command("git rev-list --left-right --count main...origin/main"))