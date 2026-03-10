# app/tasks/scheduler.py

from celery import Celery
from app.utils.notification_service import NotificationService
from app.tasks.insight_tasks import check_scheduled_insights

celery = Celery(__name__)

@celery.task
# app/tasks/scheduler.py

@celery.task
def run_scheduled_checks():
    """Run all scheduled checks"""
    # Existing checks
    NotificationService.check_and_create_medication_reminders()
    NotificationService.check_and_create_refill_reminders()
    
    # New: Check insights for all active users
    from app.utils.notification_service import InsightsNotificationService
    from app.models import User
    
    active_users = User.query.filter_by(is_active=True).all()
    total_notifications = 0
    
    for user in active_users:
        result = InsightsNotificationService.check_and_create_insight_notifications(user.id)
        total_notifications += sum(result.values())
    
    return f"Created {total_notifications} insight notifications"