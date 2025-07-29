#!/usr/bin/env python3
"""
Simple runner for Superset Post Monitor
"""

import sys
from post_monitor import SupersetPostMonitor

def main():
    print("🚀 Superset Post Monitor")
    print("=" * 40)
    
    monitor = SupersetPostMonitor()
    
    # Check for different modes
    debug_mode = "--debug" in sys.argv
    stats_mode = "--stats" in sys.argv
    headless = not debug_mode
    
    if debug_mode:
        print("🔍 Debug mode enabled - browser will be visible")
    
    if stats_mode:
        print("📊 Showing post statistics...")
        monitor.show_statistics()
        return
    
    if "--once" in sys.argv:
        print("🧪 Running single check...")
        result = monitor.run_once(headless=headless)
        if result:
            print("✅ New posts found!")
        else:
            print("ℹ️ No new posts found.")
        
        # Show statistics after the check
        monitor.show_statistics()
    else:
        print("🔄 Starting continuous monitoring...")
        print("⏰ Checking every 5 minutes")
        print("💡 Press Ctrl+C to stop")
        if debug_mode:
            print("⚠️ Debug mode - browser windows will be visible")
        print("-" * 40)
        
        # Show initial statistics
        monitor.show_statistics()
        
        # Start continuous monitoring
        monitor.run_continuous()

def show_help():
    print("🚀 Superset Post Monitor - Usage:")
    print("=" * 50)
    print("python run_monitor.py                 # Start continuous monitoring")
    print("python run_monitor.py --once          # Run single check")
    print("python run_monitor.py --once --debug  # Run single check with visible browser")
    print("python run_monitor.py --stats         # Show post statistics only")
    print("python run_monitor.py --help          # Show this help")
    print("\nFeatures:")
    print("• Scrolls to load ALL posts from the page")
    print("• Compares post titles to detect new posts")
    print("• Sends desktop notifications for new posts")
    print("• Logs all new posts to new_posts.log")
    print("• Stores known posts in known_posts.json")

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
    else:
        main()