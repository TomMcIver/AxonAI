"""
Background Task Scheduler for Big AI Coordinator
Runs periodic analysis and optimization tasks.

Note: Local ML training has been moved to external services.
This scheduler only handles analytics/reporting jobs now.
"""
import atexit
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER", "true").lower() == "true"


def run_big_ai_analysis():
    """Run Big AI Coordinator analysis (non-ML tasks only)"""
    print(f"[{datetime.now()}] Starting Big AI Coordinator analysis...")
    try:
        from ai_coordinator import BigAICoordinator
        coordinator = BigAICoordinator()
        
        coordinator.analyze_global_patterns()
        coordinator.generate_grade_predictions()
        coordinator.generate_teacher_insights()
        
        print(f"[{datetime.now()}] Big AI Coordinator analysis complete")
    except Exception as e:
        print(f"[{datetime.now()}] Big AI Coordinator error: {e}")


def init_scheduler(app):
    """Initialize the scheduler with Flask app context"""
    if not ENABLE_SCHEDULER:
        print("Scheduler disabled via ENABLE_SCHEDULER=false")
        return None
    
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        func=lambda: run_with_app_context(app, run_big_ai_analysis),
        trigger=IntervalTrigger(hours=6),
        id='big_ai_coordinator',
        name='Big AI Coordinator Analysis',
        replace_existing=True
    )
    
    scheduler.start()
    
    atexit.register(lambda: scheduler.shutdown())
    
    print("Background task scheduler initialized")
    return scheduler


def run_with_app_context(app, func):
    """Run a function within Flask app context"""
    with app.app_context():
        func()
