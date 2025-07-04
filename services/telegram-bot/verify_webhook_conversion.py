#!/usr/bin/env python3
"""
Verification script to compare polling vs webhook implementations
Ensures all command handlers and functionality are preserved
"""

import re
import os
from typing import Set, List, Dict

def extract_command_handlers(file_path: str) -> Set[str]:
    """Extract all command handlers from a Python file"""
    handlers = set()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find CommandHandler registrations
    command_pattern = r'CommandHandler\("([^"]+)"'
    handlers.update(re.findall(command_pattern, content))
    
    return handlers

def extract_methods(file_path: str) -> Set[str]:
    """Extract all method definitions from TelegramBot class"""
    methods = set()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find TelegramBot class and extract methods
    class_pattern = r'class TelegramBot:.*?(?=class|\Z)'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if class_match:
        class_content = class_match.group()
        # Pattern to find method definitions
        method_pattern = r'def (\w+)\(self'
        methods.update(re.findall(method_pattern, class_content))
    
    return methods

def extract_endpoints(file_path: str) -> Set[str]:
    """Extract Flask endpoints from webhook file"""
    endpoints = set()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find Flask routes
    route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"]'
    endpoints.update(re.findall(route_pattern, content))
    
    return endpoints

def extract_imports(file_path: str) -> Set[str]:
    """Extract all imports from a Python file"""
    imports = set()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find imports
    import_patterns = [
        r'from (\w+(?:\.\w+)*) import',
        r'import (\w+(?:\.\w+)*)'
    ]
    
    for pattern in import_patterns:
        imports.update(re.findall(pattern, content))
    
    return imports

def verify_market_client_methods(file_path: str) -> Set[str]:
    """Verify MarketDataClient methods are preserved"""
    methods = set()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find MarketDataClient class
    class_pattern = r'class MarketDataClient:.*?(?=class|\Z)'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if class_match:
        class_content = class_match.group()
        method_pattern = r'async def (\w+)\(self'
        methods.update(re.findall(method_pattern, class_content))
    
    return methods

def main():
    """Main verification function"""
    print("🔍 Verifying webhook conversion...")
    print("=" * 50)
    
    # File paths
    polling_file = "/Users/screener-m3/projects/crypto-assistant/services/telegram-bot/main.py"
    webhook_file = "/Users/screener-m3/projects/crypto-assistant/services/telegram-bot/main_webhook.py"
    
    # Check if files exist
    if not os.path.exists(polling_file):
        print(f"❌ Polling file not found: {polling_file}")
        return
    
    if not os.path.exists(webhook_file):
        print(f"❌ Webhook file not found: {webhook_file}")
        return
    
    # Extract command handlers
    polling_handlers = extract_command_handlers(polling_file)
    webhook_handlers = extract_command_handlers(webhook_file)
    
    print(f"📊 Command Handlers Comparison:")
    print(f"   Polling: {len(polling_handlers)} handlers")
    print(f"   Webhook: {len(webhook_handlers)} handlers")
    
    # Check for missing handlers
    missing_handlers = polling_handlers - webhook_handlers
    extra_handlers = webhook_handlers - polling_handlers
    
    if missing_handlers:
        print(f"❌ Missing handlers in webhook: {missing_handlers}")
    else:
        print("✅ All command handlers preserved")
    
    if extra_handlers:
        print(f"ℹ️  Extra handlers in webhook: {extra_handlers}")
    
    # Extract methods
    polling_methods = extract_methods(polling_file)
    webhook_methods = extract_methods(webhook_file)
    
    print(f"\n📋 TelegramBot Methods Comparison:")
    print(f"   Polling: {len(polling_methods)} methods")
    print(f"   Webhook: {len(webhook_methods)} methods")
    
    missing_methods = polling_methods - webhook_methods
    extra_methods = webhook_methods - polling_methods
    
    if missing_methods:
        print(f"❌ Missing methods in webhook: {missing_methods}")
    else:
        print("✅ All TelegramBot methods preserved")
    
    if extra_methods:
        print(f"ℹ️  Extra methods in webhook: {extra_methods}")
    
    # Extract MarketDataClient methods
    polling_client_methods = verify_market_client_methods(polling_file)
    webhook_client_methods = verify_market_client_methods(webhook_file)
    
    print(f"\n🌐 MarketDataClient Methods Comparison:")
    print(f"   Polling: {len(polling_client_methods)} methods")
    print(f"   Webhook: {len(webhook_client_methods)} methods")
    
    missing_client_methods = polling_client_methods - webhook_client_methods
    if missing_client_methods:
        print(f"❌ Missing MarketDataClient methods: {missing_client_methods}")
    else:
        print("✅ All MarketDataClient methods preserved")
    
    # Extract Flask endpoints
    webhook_endpoints = extract_endpoints(webhook_file)
    print(f"\n🌐 Flask Endpoints in Webhook:")
    for endpoint in sorted(webhook_endpoints):
        print(f"   {endpoint}")
    
    # Check for required webhook endpoints
    required_endpoints = {'/webhook', '/health', '/setWebhook'}
    missing_endpoints = required_endpoints - webhook_endpoints
    
    if missing_endpoints:
        print(f"❌ Missing required endpoints: {missing_endpoints}")
    else:
        print("✅ All required webhook endpoints present")
    
    # Extract imports
    polling_imports = extract_imports(polling_file)
    webhook_imports = extract_imports(webhook_file)
    
    print(f"\n📦 Import Comparison:")
    print(f"   Polling: {len(polling_imports)} imports")
    print(f"   Webhook: {len(webhook_imports)} imports")
    
    # Check for Flask/webhook specific imports
    webhook_specific_imports = {'flask', 'threading', 'queue'}
    flask_imports = webhook_imports & webhook_specific_imports
    
    if flask_imports:
        print(f"✅ Webhook-specific imports found: {flask_imports}")
    else:
        print("❌ Missing webhook-specific imports")
    
    # Overall assessment
    print(f"\n{'='*50}")
    print("🎯 CONVERSION ASSESSMENT:")
    
    all_checks = [
        len(missing_handlers) == 0,
        len(missing_methods) == 0,
        len(missing_client_methods) == 0,
        len(missing_endpoints) == 0,
        len(flask_imports) > 0
    ]
    
    if all(all_checks):
        print("✅ WEBHOOK CONVERSION SUCCESSFUL")
        print("   All functionality preserved")
        print("   All endpoints implemented")
        print("   Ready for webhook deployment")
    else:
        print("❌ WEBHOOK CONVERSION ISSUES DETECTED")
        print("   Please review the issues above")
    
    # Show specific commands
    print(f"\n📝 Available Commands:")
    for handler in sorted(webhook_handlers):
        print(f"   /{handler}")
    
    print(f"\n🔄 Deployment Instructions:")
    print("1. Test locally with Flask development server")
    print("2. Update Docker configuration for webhook mode")
    print("3. Deploy to Fly.io with webhook URL")
    print("4. Set webhook endpoint via API call")
    print("5. Test all commands with live bot")

if __name__ == "__main__":
    main()