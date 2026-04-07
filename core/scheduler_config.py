"""
Background Task Scheduler for Big AI Coordinator
Runs periodic analysis and optimization tasks
"""
import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.ai_coordinator import BigAICoordinator

def run_big_ai_analysis():
    """Run Big AI Coordinator analysis"""
    print(f"[{datetime.now()}] Starting Big AI Coordinator analysis...")
    try:
        coordinator = BigAICoordinator()
        
        # Run all analysis tasks
        coordinator.analyze_global_patterns()
        coordinator.generate_grade_predictions()
        coordinator.generate_teacher_insights()
        
        print(f"[{datetime.now()}] Big AI Coordinator analysis complete")
    except Exception as e:
        print(f"[{datetime.now()}] Big AI Coordinator error: {e}")

def init_scheduler(app):
    """Initialize the scheduler with Flask app context"""
    scheduler = BackgroundScheduler()
    
    # Schedule Big AI Coordinator to run every 6 hours
    scheduler.add_job(
        func=lambda: run_with_app_context(app, run_big_ai_analysis),
        trigger=IntervalTrigger(hours=6),
        id='big_ai_coordinator',
        name='Big AI Coordinator Analysis',
        replace_existing=True
    )
    
    # Also run analysis once on startup (after 1 minute delay)
    scheduler.add_job(
        func=lambda: run_with_app_context(app, run_big_ai_analysis),
        trigger='date',
        run_date=datetime.now().replace(second=datetime.now().second + 60),
        id='big_ai_startup',
        name='Big AI Initial Analysis'
    )
    
    # Start the scheduler
    scheduler.start()
    
    # Shut down scheduler when app exits
    atexit.register(lambda: scheduler.shutdown())
    
    print("Background task scheduler initialized")
    return scheduler

def run_with_app_context(app, func):
    """Run a function within Flask app context"""
    with app.app_context():
        func()