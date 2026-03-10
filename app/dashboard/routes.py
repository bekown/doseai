# app/dashboard/routes.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import (
    Medication, Prescription, Dose, VitalSigns, Symptom, 
    DailyCheckin, Notification, WellnessScore
)
from app.utils.helpers import Helper
from app.utils.ai_service import AIService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    user_id = current_user.id
    
    # Get medications
    medications = Medication.query.filter_by(user_id=user_id).limit(5).all()
    
    # Get adherence rate
    adherence_rate = Helper.calculate_adherence_rate(user_id, days=7)
    
    # Get upcoming doses (next 24 hours)
    upcoming_doses = Helper.get_upcoming_doses(user_id, hours=24)
    
    # Get recent vitals
    recent_vitals = VitalSigns.query.filter_by(user_id=user_id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .first()
    
    # Get active symptoms
    active_symptoms = Symptom.query.filter_by(
        user_id=user_id,
        status='active'
    ).count()
    
    # Get today's checkin status
    today = datetime.utcnow().date()
    today_checkin = DailyCheckin.query.filter_by(
        user_id=user_id,
        checkin_date=today
    ).first()
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get latest wellness score
    wellness_score = WellnessScore.query.filter_by(user_id=user_id)\
        .order_by(WellnessScore.calculation_date.desc())\
        .first()
    
    # Generate AI insights
    ai_service = AIService()
    user_data = {
        'adherence_rate': adherence_rate,
        'symptoms_count': active_symptoms,
        'medication_count': len(medications),
        'vitals_summary': f"HR: {recent_vitals.heart_rate if recent_vitals else 'N/A'}"
    }
    
    ai_insights = ai_service.generate_health_insights(user_data)
    
    return render_template('dashboard/index.html',
                         medications=medications,
                         adherence_rate=adherence_rate,
                         upcoming_doses=upcoming_doses,
                         recent_vitals=recent_vitals,
                         active_symptoms=active_symptoms,
                         today_checkin=today_checkin,
                         unread_notifications=unread_notifications,
                         wellness_score=wellness_score,
                         ai_insights=ai_insights)

@dashboard_bp.route('/overview')
@login_required
def overview():
    """Detailed overview dashboard"""
    user_id = current_user.id
    
    # Get statistics
    stats = {
        'total_medications': Medication.query.filter_by(user_id=user_id).count(),
        'active_prescriptions': Prescription.query.filter_by(
            user_id=user_id,
            status='active'
        ).count(),
        'missed_doses_today': Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.status == 'missed',
            Dose.scheduled_time >= datetime.utcnow().date()
        ).count(),
        'completed_checkins': DailyCheckin.query.filter_by(user_id=user_id).count(),
    }
    
    # Get adherence trend (last 7 days)
    adherence_trend = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        rate = Helper.calculate_adherence_rate(user_id, days=i+1)
        adherence_trend.append({
            'date': date.isoformat(),
            'rate': rate
        })
    
    return render_template('dashboard/overview.html',
                         stats=stats,
                         adherence_trend=adherence_trend)