# app/utils/notification_service.py

from datetime import datetime, timedelta

from flask import current_app
from app.models import db, User, Notification, Medication, Prescription, Dose
from .cache_service import cache

from typing import Dict, Any, List, Optional

from .insight_analyzer import InsightAnalyzer 

class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'info',
        priority: str = 'medium',
        **kwargs
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            medication_id=kwargs.get('medication_id'),
            prescription_id=kwargs.get('prescription_id'),
            is_action_required=kwargs.get('is_action_required', False),
            action_url=kwargs.get('action_url'),
            data=kwargs.get('data', {}),
            expires_at=kwargs.get('expires_at')
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Clear notification cache
        cache.delete(f'notifications_{user_id}')
        
        return notification
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        cache_key = f'notifications_{user_id}_{unread_only}_{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        # Cache for 5 minutes
        cache.set(cache_key, notifications, timeout=300)
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            
            # Clear cache
            cache.delete(f'notifications_{user_id}')
            return True
        
        return False
    
    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            
            # Clear cache
            cache.delete(f'notifications_{user_id}')
            return True
        
        return False
    
    @staticmethod
    def check_and_create_medication_reminders():
        """Check for upcoming medication doses and create reminders"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        reminder_lead = current_app.config.get('DEFAULT_REMINDER_LEAD_MINUTES', 30)
        
        # Find doses scheduled in the next reminder_lead minutes
        upcoming_doses = Dose.query.join(Prescription).filter(
            Dose.status == 'scheduled',
            Dose.scheduled_time.between(now, now + timedelta(minutes=reminder_lead))
        ).all()
        
        notifications_created = 0
        
        for dose in upcoming_doses:
            # Check if notification already exists
            existing = Notification.query.filter_by(
                user_id=dose.prescription.user_id,
                prescription_id=dose.prescription.id,
                type='medication_reminder',
                is_read=False
            ).filter(
                Notification.created_at >= now - timedelta(minutes=reminder_lead)
            ).first()
            
            if not existing:
                medication = dose.prescription.medication
                time_until = (dose.scheduled_time - now).seconds // 60
                
                NotificationService.create_notification(
                    user_id=dose.prescription.user_id,
                    title='💊 Medication Reminder',
                    message=f"Time to take {medication.name} in {time_until} minutes",
                    notification_type='medication_reminder',
                    priority='high',
                    medication_id=medication.id,
                    prescription_id=dose.prescription.id,
                    is_action_required=True,
                    action_url=f'/medications/{medication.id}/take',
                    data={
                        'dose_id': dose.id,
                        'scheduled_time': dose.scheduled_time.isoformat(),
                        'minutes_until': time_until
                    },
                    expires_at=dose.scheduled_time + timedelta(hours=1)
                )
                
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def check_and_create_refill_reminders():
        """Check for medications needing refills"""
        # Find medications with low inventory or expiring prescriptions
        from sqlalchemy import and_
        
        today = datetime.utcnow().date()
        
        # Check prescriptions ending soon
        ending_prescriptions = Prescription.query.filter(
            Prescription.status == 'active',
            Prescription.end_date != None,
            Prescription.end_date <= today + timedelta(days=3)
        ).all()
        
        notifications_created = 0
        
        for prescription in ending_prescriptions:
            days_left = (prescription.end_date - today).days
            
            existing = Notification.query.filter_by(
                user_id=prescription.user_id,
                prescription_id=prescription.id,
                type='refill_reminder',
                is_read=False
            ).filter(
                Notification.created_at >= today - timedelta(days=1)
            ).first()
            
            if not existing:
                urgency = 'today' if days_left <= 1 else f'in {days_left} days'
                
                NotificationService.create_notification(
                    user_id=prescription.user_id,
                    title='🔄 Prescription Ending',
                    message=f"{prescription.medication.name} prescription ends {urgency}",
                    notification_type='refill_reminder',
                    priority='medium',
                    medication_id=prescription.medication_id,
                    prescription_id=prescription.id,
                    is_action_required=True,
                    action_url=f'/medications/{prescription.medication_id}/refill',
                    data={
                        'end_date': prescription.end_date.isoformat(),
                        'days_remaining': days_left
                    }
                )
                
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def create_daily_checkin_reminder(user_id: int):
        """Create daily health check-in reminder"""
        today = datetime.utcnow().date()
        
        # Check if user already checked in today
        from app.models import DailyCheckin
        existing_checkin = DailyCheckin.query.filter_by(
            user_id=user_id,
            checkin_date=today
        ).first()
        
        if not existing_checkin:
            # Check if reminder already sent today
            existing_notification = Notification.query.filter_by(
                user_id=user_id,
                type='daily_checkin',
                is_read=False
            ).filter(
                db.func.date(Notification.created_at) == today
            ).first()
            
            if not existing_notification:
                NotificationService.create_notification(
                    user_id=user_id,
                    title='📊 Daily Health Check',
                    message='Complete your daily health check-in',
                    notification_type='daily_checkin',
                    priority='medium',
                    is_action_required=True,
                    action_url='/health/checkin',
                    data={'reminder_type': 'daily_checkin'}
                )
                return True
        
        return False


#

class InsightsNotificationService:
    """Service for handling insights-related notifications"""
    
    @staticmethod
    def check_and_create_insight_notifications(user_id: int) -> Dict[str, int]:
        """Run all insight checks and create notifications"""
        notifications_created = {
            'interactions': 0,
            'contraindications': 0,
            'adherence': 0,
            'vital_signs': 0,
            'refills': 0
        }
        
        analyzer = InsightAnalyzer()
        
        # 1. Check medication interactions
        interactions = analyzer.check_medication_interactions(user_id)
        for interaction in interactions:
            if InsightsNotificationService.create_interaction_notification(
                user_id=user_id,
                medication_ids=interaction['medication_ids'],
                interaction_type=interaction['type'],
                severity=interaction['severity'],
                details=interaction['details']
            ):
                notifications_created['interactions'] += 1
        
        # 2. Check contraindications
        contraindications = analyzer.check_contraindications(user_id)
        for contra in contraindications:
            if InsightsNotificationService.create_contraindication_notification(
                user_id=user_id,
                medication_id=contra['medication_id'],
                condition=contra['condition'],
                severity=contra['severity'],
                contraindication_details=contra['details']
            ):
                notifications_created['contraindications'] += 1
        
        # 3. Check adherence (only notify if low)
        adherence = analyzer.analyze_adherence(user_id)
        if adherence['adherence_rate'] < 70:  # Below 70% adherence
            if InsightsNotificationService.create_adherence_notification(
                user_id=user_id,
                adherence_rate=adherence['adherence_rate'],
                missed_doses=adherence['missed_doses']
            ):
                notifications_created['adherence'] += 1
        
        # 4. Check vital signs trends
        vital_signs_insights = analyzer.check_vital_signs_trends(user_id)
        for insight in vital_signs_insights:
            if InsightsNotificationService.create_insight_notification(
                user_id=user_id,
                insight_type=insight['type'],
                title=insight['title'],
                message=insight['message'],
                priority=insight['severity'],
                data=insight['data']
            ):
                notifications_created['vital_signs'] += 1
        
        # 5. Check prescription refills
        refill_insights = analyzer.check_prescription_refills(user_id)
        for insight in refill_insights:
            if InsightsNotificationService.create_insight_notification(
                user_id=user_id,
                insight_type='refill_needed',
                title=insight['title'],
                message=insight['message'],
                priority='medium',
                action_url=f'/prescriptions/{insight["data"]["prescription_id"]}/refill',
                data=insight['data']
            ):
                notifications_created['refills'] += 1
        
        return notifications_created
    
    @staticmethod
    def create_adherence_notification(user_id: int, adherence_rate: float, missed_doses: int) -> bool:
        """Create notification for low adherence"""
        
        existing = Notification.query.filter_by(
            user_id=user_id,
            type='low_adherence',
            is_read=False
        ).filter(
            Notification.created_at >= datetime.utcnow() - timedelta(days=1)
        ).first()
        
        if existing:
            return False
        
        title = '📉 Low Medication Adherence'
        message = f'Your adherence is {adherence_rate}% with {missed_doses} missed dose(s)'
        
        NotificationService.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type='low_adherence',
            priority='medium',
            is_action_required=True,
            action_url='/medications/history',
            data={
                'adherence_rate': adherence_rate,
                'missed_doses': missed_doses,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        return True
    
    # Keep the other methods from the previous version...
    @staticmethod
    def create_interaction_notification(user_id: int, medication_ids: List[int], 
                                       interaction_type: str, severity: str, 
                                       details: Dict[str, Any]) -> bool:
        # ... (same as before)
    
    @staticmethod
    def create_contraindication_notification(user_id: int, medication_id: int, 
                                            condition: str, severity: str, 
                                            contraindication_details: Dict[str, Any]) -> bool:
        # ... (same as before)
    
    @staticmethod
    def create_insight_notification(user_id: int, insight_type: str, title: str, 
                                   message: str, priority: str = 'medium', **kwargs) -> bool:
        # ... (same as before)