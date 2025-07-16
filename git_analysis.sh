#!/bin/bash
cd /Users/screener-m3/projects/crypto-assistant

echo "=== Git Status ==="
git status

echo -e "\n=== Current Branch ==="
git branch --show-current

echo -e "\n=== All Branches ==="
git branch -a

echo -e "\n=== Commits in aws-deployment not in main ==="
git log aws-deployment --not main --oneline

echo -e "\n=== Commits in main not in aws-deployment ==="
git log main --not aws-deployment --oneline

echo -e "\n=== Uncommitted changes ==="
git diff --name-only

echo -e "\n=== Untracked files ==="
git ls-files --others --exclude-standard

echo -e "\n=== Remote status ==="
git remote -v

echo -e "\n=== Fetch status ==="
git fetch --dry-run -v 2>&1

echo -e "\n=== Compare with remote ==="
echo "Local aws-deployment vs origin/aws-deployment:"
git rev-list --left-right --count aws-deployment...origin/aws-deployment

echo -e "\nLocal main vs origin/main:"
git rev-list --left-right --count main...origin/main