# app/tasks/insight_tasks.py

from datetime import datetime, timedelta
from app.utils.insights_notification_service import InsightsNotificationService
from app.models import User, Medication, Prescription, Dose

def check_scheduled_insights():
    """Scheduled task to check for insights"""
    
    # Get all active users
    active_users = User.query.filter_by(is_active=True).all()
    
    for user in active_users:
        # Check for interactions
        check_user_interactions(user.id)
        
        # Check for contraindications
        check_user_contraindications(user.id)
        
        # Check for other insights
        check_user_health_insights(user.id)

def check_user_interactions(user_id):
    """Check medication interactions for a user"""
    from app.utils.insight_analyzer import InsightAnalyzer
    
    analyzer = InsightAnalyzer()
    interactions = analyzer.check_medication_interactions(user_id)
    
    for interaction in interactions:
        if interaction['severity'] in ['high', 'severe']:
            InsightsNotificationService.create_interaction_notification(
                user_id=user_id,
                medication_ids=interaction['medication_ids'],
                interaction_type=interaction['type'],
                severity=interaction['severity'],
                details=interaction['details']
            )