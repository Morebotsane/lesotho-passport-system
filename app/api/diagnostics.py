# app/api/diagnostics.py
"""
Database query performance diagnostics endpoint.
Use this to identify slow queries and optimization opportunities.
"""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import User

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/query-performance")
def test_query_performance(db: Session = Depends(get_db)):
    """
    Run various database queries to identify performance bottlenecks.
    Watch your console/terminal for 🐌 SLOW QUERY warnings.
    
    Returns timing information for different query patterns.
    """
    results = {}
    
    # ========== TEST 1: Simple SELECT ==========
    print("\n" + "="*50)
    print("TEST 1: Simple SELECT query")
    print("="*50)
    start = time.time()
    notifications = db.query(Notification).limit(10).all()
    elapsed = time.time() - start
    results['test_1_simple_select'] = {
        "description": "SELECT * FROM notifications LIMIT 10",
        "time_seconds": round(elapsed, 3),
        "records_returned": len(notifications)
    }
    
    # ========== TEST 2: COUNT Query ==========
    print("\n" + "="*50)
    print("TEST 2: COUNT query")
    print("="*50)
    start = time.time()
    total_count = db.query(Notification).count()
    elapsed = time.time() - start
    results['test_2_count'] = {
        "description": "SELECT COUNT(*) FROM notifications",
        "time_seconds": round(elapsed, 3),
        "total_records": total_count
    }
    
    # ========== TEST 3: Filtered Query (No Index) ==========
    print("\n" + "="*50)
    print("TEST 3: Filtered query by status")
    print("="*50)
    start = time.time()
    pending = db.query(Notification).filter(
        Notification.status == NotificationStatus.PENDING  # FIXED: Using enum
    ).all()
    elapsed = time.time() - start
    results['test_3_filtered_status'] = {
        "description": "SELECT * WHERE status = 'pending'",
        "time_seconds": round(elapsed, 3),
        "records_found": len(pending)
    }
    
    # ========== TEST 4: JOIN Query ==========
    print("\n" + "="*50)
    print("TEST 4: JOIN query (notifications + users)")
    print("="*50)
    start = time.time()
    try:
        notifications_with_users = db.query(Notification).join(
            User, Notification.sender_id == User.id
        ).limit(10).all()
        elapsed = time.time() - start
        results['test_4_join'] = {
            "description": "SELECT * FROM notifications JOIN users ON sender_id LIMIT 10",
            "time_seconds": round(elapsed, 3),
            "records_returned": len(notifications_with_users)
        }
    except Exception as e:
        results['test_4_join'] = {
            "description": "JOIN test skipped",
            "error": str(e),
            "time_seconds": 0
        }
    
    # ========== TEST 5: ORDER BY Query (Potentially Slow) ==========
    print("\n" + "="*50)
    print("TEST 5: ORDER BY created_at")
    print("="*50)
    start = time.time()
    sorted_notifications = db.query(Notification).order_by(
        Notification.created_at.desc()
    ).limit(20).all()
    elapsed = time.time() - start
    results['test_5_order_by'] = {
        "description": "SELECT * ORDER BY created_at DESC LIMIT 20",
        "time_seconds": round(elapsed, 3),
        "records_returned": len(sorted_notifications)
    }
    
    # ========== TEST 6: Multiple Filters ==========
    print("\n" + "="*50)
    print("TEST 6: Multiple WHERE conditions")
    print("="*50)
    start = time.time()
    complex_filter = db.query(Notification).filter(
        Notification.status == NotificationStatus.SENT,  # FIXED: Using enum
        Notification.notification_type == NotificationType.READY_FOR_PICKUP  # FIXED: Using real type
    ).limit(10).all()
    elapsed = time.time() - start
    results['test_6_multiple_filters'] = {
        "description": "SELECT * WHERE status='sent' AND type='ready_for_pickup'",
        "time_seconds": round(elapsed, 3),
        "records_returned": len(complex_filter)
    }
    
    # ========== TEST 7: Accessing Relationships (N+1 Problem Test) ==========
    print("\n" + "="*50)
    print("TEST 7: Accessing relationships (N+1 detection)")
    print("="*50)
    start = time.time()
    notifications = db.query(Notification).limit(5).all()
    # Now access the sender for each notification (this might trigger N+1!)
    sender_names = []
    for notif in notifications:
        if notif.sender:  # This triggers a new query for EACH notification!
            sender_names.append(notif.sender.full_name)
    elapsed = time.time() - start
    results['test_7_n_plus_1'] = {
        "description": "Load 5 notifications, then access sender for each (N+1 problem)",
        "time_seconds": round(elapsed, 3),
        "records_returned": len(notifications),
        "sender_count": len(sender_names),
        "note": "Watch for multiple SELECT queries in console - indicates N+1 problem"
    }
    
    # ========== TEST 8: Filter by notification type ==========
    print("\n" + "="*50)
    print("TEST 8: Filter by notification_type")
    print("="*50)
    start = time.time()
    pickup_reminders = db.query(Notification).filter(
        Notification.notification_type == NotificationType.PICKUP_REMINDER
    ).limit(10).all()
    elapsed = time.time() - start
    results['test_8_filter_by_type'] = {
        "description": "SELECT * WHERE notification_type = 'pickup_reminder'",
        "time_seconds": round(elapsed, 3),
        "records_returned": len(pickup_reminders)
    }
    
    # ========== SUMMARY ==========
    # Filter out any skipped tests
    valid_results = {k: v for k, v in results.items() if v.get('time_seconds', 0) > 0}
    
    if valid_results:
        slowest = max(valid_results.items(), key=lambda x: x[1]['time_seconds'])
        
        print("\n" + "="*50)
        print("🏁 DIAGNOSTIC SUMMARY")
        print("="*50)
        print(f"Slowest query: {slowest[0]}")
        print(f"Time: {slowest[1]['time_seconds']}s")
        print("\nCheck console above for 🐌 SLOW QUERY warnings (>100ms)")
        print("="*50 + "\n")
        
        return {
            "message": "✅ Query diagnostics complete. Check console logs for details.",
            "results": results,
            "slowest_query": {
                "test": slowest[0],
                "time": slowest[1]['time_seconds'],
                "description": slowest[1]['description']
            },
            "instructions": "Look for 🐌 SLOW QUERY warnings in your terminal"
        }
    else:
        return {
            "message": "⚠️ No valid test results",
            "results": results
        }


@router.get("/table-stats")
def get_table_statistics(db: Session = Depends(get_db)):
    """
    Get basic statistics about your database tables.
    Helps identify which tables are large and might need indexing.
    """
    stats = {}
    
    # Notifications table - using proper enums
    stats['notifications'] = {
        "total_records": db.query(Notification).count(),
        "by_status": {
            "pending": db.query(Notification).filter(
                Notification.status == NotificationStatus.PENDING
            ).count(),
            "sent": db.query(Notification).filter(
                Notification.status == NotificationStatus.SENT
            ).count(),
            "delivered": db.query(Notification).filter(
                Notification.status == NotificationStatus.DELIVERED
            ).count(),
            "failed": db.query(Notification).filter(
                Notification.status == NotificationStatus.FAILED
            ).count(),
        },
        "by_type": {
            "ready_for_pickup": db.query(Notification).filter(
                Notification.notification_type == NotificationType.READY_FOR_PICKUP
            ).count(),
            "pickup_reminder": db.query(Notification).filter(
                Notification.notification_type == NotificationType.PICKUP_REMINDER
            ).count(),
        }
    }
    
    # Users table
    try:
        stats['users'] = {
            "total_records": db.query(User).count()
        }
    except Exception as e:
        stats['users'] = f"Error: {str(e)}"
    
    return {
        "message": "Database table statistics",
        "stats": stats
    }