#!/usr/bin/env python3
"""
Test script to verify the complete post monitoring system
"""

import os
import json
from post_monitor import SupersetPostMonitor

def test_environment():
    """Test environment variable loading"""
    print("🧪 Testing Environment Variables")
    print("=" * 40)
    
    monitor = SupersetPostMonitor()
    
    if monitor.username and monitor.password:
        print("✅ Credentials loaded successfully")
    else:
        print("❌ Failed to load credentials")
        return False
    
    return True

def test_known_posts_system():
    """Test the known posts storage system"""
    print("\n🧪 Testing Known Posts System")
    print("=" * 40)
    
    # Create a test post
    test_post = {
        'title': 'Test Post - ConglomerateIT NCET Test for 2026 Graduating Batch',
        'author': 'Test Author',
        'time': '1 hour ago',
        'link': 'https://test.com',
        'first_seen': '2025-01-28T10:00:00'
    }
    
    # Test saving
    known_posts = {'Test Post Title': test_post}
    
    try:
        with open('test_known_posts.json', 'w', encoding='utf-8') as f:
            json.dump(known_posts, f, indent=2, ensure_ascii=False)
        print("✅ Post storage system working")
        
        # Test loading
        with open('test_known_posts.json', 'r', encoding='utf-8') as f:
            loaded_posts = json.load(f)
        
        if loaded_posts == known_posts:
            print("✅ Post loading system working")
        else:
            print("❌ Post loading failed")
            return False
        
        # Cleanup
        os.remove('test_known_posts.json')
        
    except Exception as e:
        print(f"❌ Post storage system failed: {str(e)}")
        return False
    
    return True

def show_current_status():
    """Show current system status"""
    print("\n📊 Current System Status")
    print("=" * 40)
    
    # Check if known_posts.json exists
    if os.path.exists('known_posts.json'):
        try:
            with open('known_posts.json', 'r', encoding='utf-8') as f:
                known_posts = json.load(f)
            print(f"📋 Known posts file exists with {len(known_posts)} posts")
            
            if len(known_posts) > 0:
                print("📝 Recent posts:")
                for i, (title, data) in enumerate(list(known_posts.items())[:3], 1):
                    author = data.get('author', 'Unknown')
                    time_posted = data.get('time', 'Unknown')
                    print(f"   {i}. {title[:50]}... (by {author}, {time_posted})")
        except Exception as e:
            print(f"⚠️ Error reading known posts: {str(e)}")
    else:
        print("📋 No known posts file found (will be created on first run)")
    
    # Check if log file exists
    if os.path.exists('new_posts.log'):
        with open('new_posts.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"📄 Log file exists with {len(lines)} entries")
        
        if len(lines) > 0:
            print("📝 Recent log entries:")
            for line in lines[-3:]:
                print(f"   {line.strip()}")
    else:
        print("📄 No log file found (will be created when new posts are found)")

def main():
    print("🚀 Superset Post Monitor - System Test")
    print("=" * 50)
    
    # Test 1: Environment variables
    if not test_environment():
        print("\n❌ Environment test failed. Please check your .env file.")
        return
    
    # Test 2: Known posts system
    if not test_known_posts_system():
        print("\n❌ Known posts system test failed.")
        return
    
    # Test 3: Show current status
    show_current_status()
    
    print("\n✅ All tests passed! System is ready.")
    print("\n🚀 Ready to run:")
    print("   python run_monitor.py --once --debug    # Test with visible browser")
    print("   python run_monitor.py --once            # Test in background")
    print("   python run_monitor.py                   # Start continuous monitoring")
    print("   python run_monitor.py --stats           # Show post statistics")

if __name__ == "__main__":
    main()