#!/usr/bin/env python3
"""
Setup script for Superset Post Monitor
"""

import os
import shutil

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("📝 Please edit .env file with your credentials")
        else:
            print("❌ .env.example not found")
    else:
        print("ℹ️ .env file already exists")

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    os.system("pip install -r requirements.txt")

def main():
    print("🚀 Setting up Superset Post Monitor")
    print("=" * 40)
    
    create_env_file()
    install_requirements()
    
    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your credentials")
    print("2. Run: python post_monitor.py")

if __name__ == "__main__":
    main()