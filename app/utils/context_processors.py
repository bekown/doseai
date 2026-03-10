# app/utils/context_processors.py

from flask import session
from flask_login import current_user
from datetime import datetime, timedelta
from app.models import db, Notification, Dose, Prescription, Medication, DailyCheckin
from sqlalchemy.orm import joinedload

def inject_global_data():
    """Main context processor that injects data into all templates"""
    data = {
        'now': datetime.utcnow(),
        'config': get_app_config(),
    }
    
    if current_user.is_authenticated:
        data.update({
            'unread_notifications': get_unread_notification_count(current_user.id),
            'global_countdown': get_next_dose_data(current_user.id),
            'missed_dose_guidance': get_missed_dose_guidance(current_user.id),
            'daily_data_vitals': get_daily_checkin_status(current_user.id)
        })
        
        # Set session data if not already set
        if 'user_name' not in session:
            set_user_session_data()
    else:
        data.update({
            'unread_notifications': 0,
            'global_countdown': None,
            'missed_dose_guidance': None,
            'daily_data_vitals': None
        })
    
    return data
def get_api_endpoints():
    """Get API endpoint URLs for JavaScript"""
    from flask import url_for
    
    # Use a try-except block to handle cases where routes aren't registered yet
    try:
        return {
            'take_dose': url_for('medications.take_dose', _external=False),
            'snooze_dose': url_for('medications.snooze_dose', _external=False),
            'skip_dose': url_for('medications.skip_dose', _external=False),
            'daily_checkin': url_for('health.daily_checkin', _external=False),
            'notifications_list': url_for('notifications.api_list', _external=False),
            'mark_as_read': url_for('notifications.mark_as_read', notification_id=0, _external=False).replace('/0', ''),
            'delete_notification': url_for('notifications.delete_notification', notification_id=0, _external=False).replace('/0', '')
        }
    except:
        # Return placeholder endpoints that will be updated by JavaScript
        return {
            'take_dose': '/medications/take_dose',
            'snooze_dose': '/medications/snooze_dose',
            'skip_dose': '/medications/skip_dose',
            'daily_checkin': '/health/daily_checkin',
            'notifications_list': '/notifications/api/list',
            'mark_as_read': '/notifications/{id}/read',
            'delete_notification': '/notifications/{id}/delete'
        }
def get_app_config():
    """Get app configuration for templates"""
    from flask import current_app
    return {
        'DEBUG': current_app.config.get('DEBUG', False),
        'STATIC_FILE_VERSION': current_app.config.get('STATIC_FILE_VERSION', '1.0.0'),
        'APP_NAME': current_app.config.get('APP_NAME', 'DoseAI'),
        'CONTACT_EMAIL': current_app.config.get('CONTACT_EMAIL', 'support@doseai.com'),
    }

def get_unread_notification_count(user_id):
    """Get count of unread notifications"""
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()

def get_next_dose_data(user_id):
    """Get the next scheduled dose for a user"""
    try:
        next_dose = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.status == 'scheduled',
            Dose.scheduled_time > datetime.utcnow()
        ).options(
            joinedload(Dose.prescription).joinedload(Prescription.medication)
        ).order_by(
            Dose.scheduled_time.asc()
        ).first()
        
        if next_dose:
            medication = next_dose.prescription.medication
            
            return {
                'medication_id': medication.id,
                'medication_name': medication.name,
                'next_dose_time': next_dose.scheduled_time.isoformat(),
                'scheduled_time': next_dose.scheduled_time.isoformat(),
                'prescription_id': next_dose.prescription_id,
                'dosage': next_dose.prescription.dosage,
                'minutes_until': int((next_dose.scheduled_time - datetime.utcnow()).total_seconds() / 60)
            }
        
        # Check for overdue doses
        overdue_dose = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.status == 'scheduled',
            Dose.scheduled_time <= datetime.utcnow()
        ).options(
            joinedload(Dose.prescription).joinedload(Prescription.medication)
        ).order_by(
            Dose.scheduled_time.asc()
        ).first()
        
        if overdue_dose:
            medication = overdue_dose.prescription.medication
            minutes_overdue = int((datetime.utcnow() - overdue_dose.scheduled_time).total_seconds() / 60)
            
            return {
                'medication_id': medication.id,
                'medication_name': medication.name,
                'next_dose_time': overdue_dose.scheduled_time.isoformat(),
                'scheduled_time': overdue_dose.scheduled_time.isoformat(),
                'prescription_id': overdue_dose.prescription_id,
                'dosage': overdue_dose.prescription.dosage,
                'minutes_overdue': minutes_overdue,
                'is_overdue': True
            }
    
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error getting next dose data: {e}")
    
    return None

def get_missed_dose_guidance(user_id):
    """Get guidance for missed doses"""
    try:
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        missed_doses = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.status == 'missed',
            Dose.scheduled_time >= twenty_four_hours_ago
        ).all()
        
        if missed_doses:
            guidance = "<h6>Missed Dose Guidance:</h6><ul>"
            for dose in missed_doses[:3]:
                medication = dose.prescription.medication
                guidance += f"<li><strong>{medication.name}:</strong> "
                guidance += "Take as soon as you remember. If it's almost time for your next dose, skip the missed dose.</li>"
            guidance += "</ul>"
            return guidance
    
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error getting missed dose guidance: {e}")
    
    return None

def get_daily_checkin_status(user_id):
    """Get daily check-in status for user"""
    try:
        today = datetime.utcnow().date()
        
        checkin = DailyCheckin.query.filter_by(
            user_id=user_id,
            checkin_date=today
        ).first()
        
        if checkin:
            return {
                'submitted_today': True,
                'vitals_submitted': checkin.vitals_completed,
                'symptoms_submitted': checkin.symptoms_completed,
                'mood_submitted': checkin.mood_completed,
                'medications_taken': checkin.medications_taken or [],
                'overall_wellness': checkin.overall_wellness,
                'notes': checkin.notes
            }
        else:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            existing_reminder = Notification.query.filter_by(
                user_id=user_id,
                type='daily_checkin',
                is_read=False
            ).filter(
                Notification.created_at >= one_hour_ago
            ).first()
            
            return {
                'submitted_today': False,
                'vitals_submitted': False,
                'symptoms_submitted': False,
                'mood_submitted': False,
                'has_reminder': existing_reminder is not None,
                'medications_taken': [],
                'overall_wellness': None,
                'notes': None
            }
    
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error getting daily checkin status: {e}")
    
    return {
        'submitted_today': False,
        'vitals_submitted': False,
        'symptoms_submitted': False,
        'mood_submitted': False,
        'has_reminder': False,
        'medications_taken': [],
        'overall_wellness': None,
        'notes': None
    }

def set_user_session_data():
    """Set user data in session"""
    from flask import session
    
    if current_user.is_authenticated:
        if current_user.profile:
            session['user_name'] = f"{current_user.profile.first_name} {current_user.profile.last_name}"
        else:
            session['user_name'] = current_user.username
        
        session['user_email'] = current_user.email
        session['user_id'] = current_user.id