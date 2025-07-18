#!/bin/bash
# EVIDENCE COLLECTION SCRIPT - SYSTEMATIC RECOVERY PLAN
# DO NOT EXECUTE WITHOUT APPROVAL

echo "🔍 EVIDENCE COLLECTION - SYSTEMATIC RECOVERY PLAN"
echo "================================================="
echo "TIMESTAMP: $(date)"
echo ""

echo "📊 GIT HISTORY EVIDENCE:"
echo "------------------------"
echo "Extracting July 1-15, 2025 commits..."
git log --since="2025-07-01" --until="2025-07-15" --oneline --all > git_history_evidence.txt
git log --graph --pretty=format:'%h %ad %s' --date=iso --since="2025-07-01" --until="2025-07-15" > git_timeline_evidence.txt

echo "✅ Git history saved to git_history_evidence.txt"
echo "✅ Git timeline saved to git_timeline_evidence.txt"
echo ""

echo "📁 FILE AUDIT EVIDENCE:"
echo "-----------------------"
echo "Categorizing all files..."

# Python files audit
find . -type f -name "*.py" | grep -v __pycache__ | sort > all_python_files.txt
echo "✅ Python files: $(wc -l < all_python_files.txt) files found"

# Fly.io pollution detection
find . -type f -name "*fly*" > fly_pollution_files.txt
echo "✅ Fly.io files: $(wc -l < fly_pollution_files.txt) files found"

# AWS specific files
find . -type f -name "*aws*" > aws_specific_files.txt
echo "✅ AWS files: $(wc -l < aws_specific_files.txt) files found"

# Docker configurations
find . -type f -name "docker-compose*" > docker_configs.txt
find . -type f -name "Dockerfile*" >> docker_configs.txt
echo "✅ Docker files: $(wc -l < docker_configs.txt) files found"

# Test/Debug pollution
find . -type f -name "*test*" | grep -v tests/ > test_pollution_files.txt
find . -type f -name "*debug*" >> test_pollution_files.txt
find . -type f -name "emergency_*" >> test_pollution_files.txt
echo "✅ Test/Debug pollution: $(wc -l < test_pollution_files.txt) files found"

echo ""
echo "🔍 DEPENDENCY ANALYSIS:"
echo "----------------------"
# Extract all Python imports
echo "Analyzing Python dependencies..."
find . -name "*.py" -exec grep -h "^import\|^from" {} \; | sort | uniq > all_imports.txt
echo "✅ All imports saved to all_imports.txt"

# Requirements files audit
find . -name "requirements.txt" > requirements_files.txt
echo "✅ Requirements files: $(wc -l < requirements_files.txt) files found"

echo ""
echo "📋 ENVIRONMENT ANALYSIS:"
echo "------------------------"
# Environment files
find . -name "*.env*" > env_files.txt
echo "✅ Environment files: $(wc -l < env_files.txt) files found"

# Environment variables in code
grep -r "os.getenv\|os.environ" --include="*.py" . | cut -d: -f1 | sort | uniq > env_usage_files.txt
echo "✅ Files using environment variables: $(wc -l < env_usage_files.txt) files found"

echo ""
echo "🎯 EVIDENCE COLLECTION COMPLETE!"
echo "================================="
echo "Generated files:"
echo "- git_history_evidence.txt"
echo "- git_timeline_evidence.txt" 
echo "- all_python_files.txt"
echo "- fly_pollution_files.txt"
echo "- aws_specific_files.txt"
echo "- docker_configs.txt"
echo "- test_pollution_files.txt"
echo "- all_imports.txt"
echo "- requirements_files.txt"
echo "- env_files.txt"
echo "- env_usage_files.txt"
echo ""
echo "⚠️  NEXT: Review evidence files before proceeding"
echo "⚠️  REQUIRE: Architect approval before any changes"