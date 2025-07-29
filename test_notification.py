#!/usr/bin/env python3
"""
Test script to verify desktop notifications are working
"""

try:
    from plyer import notification
    import time
    
    print("🧪 Testing desktop notification system...")
    
    # Test 1: Simple notification
    print("📱 Sending test notification...")
    notification.notify(
        title="Test Notification",
        message="This is a test notification from Superset Monitor",
        timeout=5
    )
    print("✅ Test notification sent!")
    
    print("⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Test 2: Notification with more details
    print("📱 Sending detailed notification...")
    notification.notify(
        title="New Superset Post!",
        message="ConglomerateIT NCET Test for 2026 Graduating Batch\nBy: Madhusmita Behera • 3 hours ago",
        timeout=10
    )
    print("✅ Detailed notification sent!")
    
    print("\n✅ Notification system test completed!")
    print("💡 If you didn't see any notifications, there might be:")
    print("   - System notification permissions disabled")
    print("   - Notification service not running")
    print("   - Windows notification settings blocking Python apps")
    
except ImportError:
    print("❌ plyer library not installed!")
    print("💡 Install with: pip install plyer")
    
except Exception as e:
    print(f"❌ Notification test failed: {str(e)}")
    print("💡 This might be why you're not seeing notifications in the main script")