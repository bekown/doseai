# app/utils/helpers.py

from datetime import datetime, timedelta
from flask import current_app
from .cache_service import cache

class Helper:
    """Helper functions for common operations"""
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_user_medications(user_id):
        """Get user medications with caching"""
        from app.models import Medication, Prescription
        return Medication.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def calculate_adherence_rate(user_id, days=30):
        """Calculate adherence rate for the last N days"""
        from app.models import Dose, Prescription
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.scheduled_time >= cutoff_date
        ).with_entities(
            func.count(Dose.id).label('total'),
            func.sum(func.case([(Dose.status == 'taken', 1)], else_=0)).label('taken')
        ).first()
        
        if result and result.total and result.total > 0:
            return round((result.taken / result.total) * 100, 1)
        return 0.0
    
    @staticmethod
    def get_upcoming_doses(user_id, hours=24):
        """Get doses scheduled in the next N hours"""
        from app.models import Dose, Prescription, Medication
        from sqlalchemy import and_
        
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)
        
        return Dose.query.join(Prescription).join(Medication).filter(
            Prescription.user_id == user_id,
            Dose.status == 'scheduled',
            and_(Dose.scheduled_time >= now, Dose.scheduled_time <= end_time)
        ).order_by(Dose.scheduled_time).all()
    
    @staticmethod
    def format_datetime(dt, format='%Y-%m-%d %H:%M'):
        """Format datetime consistently"""
        if dt:
            return dt.strftime(format)
        return None
    
    @staticmethod
    def get_relative_time(dt):
        """Get relative time string (e.g., '2 hours ago')"""
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"