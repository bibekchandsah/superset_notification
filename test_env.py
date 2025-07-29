#!/usr/bin/env python3
"""
Test script to verify environment variable loading
"""

import os
from dotenv import load_dotenv

print("🧪 Testing environment variable loading...")
print("=" * 50)

# Test 1: Check if .env file exists
if os.path.exists('.env'):
    print("✅ .env file exists")
    with open('.env', 'r') as f:
        content = f.read()
        print("📄 .env file content:")
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                if 'PASSWORD' in line:
                    key, value = line.split('=', 1)
                    print(f"   {key}=***hidden***")
                else:
                    print(f"   {line}")
else:
    print("❌ .env file not found!")

print("\n" + "=" * 50)

# Test 2: Load environment variables
print("🔄 Loading environment variables...")
load_dotenv('.env')

# Test 3: Check loaded values
print("📋 Loaded environment variables:")
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
login_url = os.getenv('LOGIN_URL')
dashboard_url = os.getenv('DASHBOARD_URL')
check_interval = os.getenv('CHECK_INTERVAL')

print(f"   USERNAME: {username}")
print(f"   PASSWORD: {'*' * len(password) if password else 'None'}")
print(f"   LOGIN_URL: {login_url}")
print(f"   DASHBOARD_URL: {dashboard_url}")
print(f"   CHECK_INTERVAL: {check_interval}")

# Test 4: Check for conflicts
print("\n" + "=" * 50)
print("🔍 Checking for environment variable conflicts...")

system_username = os.environ.get('USERNAME')
if system_username and system_username != username:
    print(f"⚠️ System USERNAME conflicts: {system_username}")
else:
    print("✅ No USERNAME conflicts detected")

if not username or not password:
    print("❌ Missing required credentials!")
else:
    print("✅ All required credentials found")