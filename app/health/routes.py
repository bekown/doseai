# app/health/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import csv
from io import StringIO, BytesIO
from utils.notification_service import NotificationService

from app import db
from app.models import (
    VitalSigns, Symptom, Mood, DailyCheckin, MedicalEvaluation,
    LabTest, ImagingStudy, HealthCondition, Allergy, HealthcareProvider
)
from app.utils.helpers import Helper
from app.utils.file_upload import FileUploadService
from .forms import (
    VitalSignsForm, SymptomForm, MoodForm, DailyCheckinForm,
    MedicalEvaluationForm, LabTestForm, ImagingStudyForm,
    ComprehensiveEvaluationForm, LabTestSearchForm, ImagingSearchForm,
    LabTrendForm, ExportDataForm, HealthConditionSearchForm, HealthConditionForm, AllergyForm, 
    QuickHealthConditionForm, QuickAllergyForm, AllergySearchForm
)

health_bp = Blueprint('health', __name__)

notification_service = NotificationService()

# ============================================================================
# HEALTH HUB DASHBOARD ROUTES
# ============================================================================

@health_bp.route('/')
@health_bp.route('/dashboard')
@login_required
def health_hub():
    """Health Hub Dashboard - Main health tracking interface"""
    
    # Get today's vitals
    today = datetime.utcnow().date()
    today_vitals = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        db.func.date(VitalSigns.recorded_at) == today
    ).order_by(VitalSigns.recorded_at.desc()).first()
    
    # Get active symptoms count
    active_symptoms_count = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    severe_symptoms_count = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active',
        severity='severe'
    ).count()
    
    # Get today's mood
    today_mood = Mood.query.filter(
        Mood.user_id == current_user.id,
        db.func.date(Mood.recorded_at) == today
    ).order_by(Mood.recorded_at.desc()).first()
    
    # Check daily check-in status
    daily_checkin = DailyCheckin.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()    
    
    
    # Get upcoming appointments (next 7 days)
    upcoming_appointments = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == current_user.id,
        MedicalEvaluation.follow_up_date >= today,
        MedicalEvaluation.follow_up_date <= today + timedelta(days=7)
    ).order_by(MedicalEvaluation.follow_up_date).limit(5).all()
    
    # Format appointments for display
    formatted_appointments = []
    for appointment in upcoming_appointments:
        formatted_appointments.append({
            'id': appointment.id,
            'provider_name': appointment.provider_name,
            'type': appointment.evaluation_type,
            'date': appointment.follow_up_date,
            'time': None  # You can add time field if available
        })
    
    # Get recent activities (last 7 days)
    recent_activities = []
    
    # Recent vitals
    recent_vitals_list = VitalSigns.query.filter_by(
        user_id=current_user.id
    ).order_by(VitalSigns.recorded_at.desc()).limit(5).all()
    
    for vital in recent_vitals_list:
        recent_activities.append({
            'type': 'vitals',
            'time': vital.recorded_at,
            'icon': 'favorite',
            'description': f'Recorded vital signs',
            'details': f'BP: {vital.blood_pressure if vital.blood_pressure else "N/A"} | HR: {vital.heart_rate if vital.heart_rate else "N/A"}'
        })
    
    # Recent mood entries
    recent_moods_list = Mood.query.filter_by(
        user_id=current_user.id
    ).order_by(Mood.recorded_at.desc()).limit(3).all()
    
    for mood in recent_moods_list:
        recent_activities.append({
            'type': 'mood',
            'time': mood.recorded_at,
            'icon': 'mood',
            'description': f'Logged mood as {mood.mood_level}',
            'details': f'Energy: {mood.energy_level if mood.energy_level else "N/A"}/10'
        })
    
    # Recent symptoms
    recent_symptoms_list = Symptom.query.filter_by(
        user_id=current_user.id
    ).order_by(Symptom.recorded_at.desc()).limit(3).all()
    
    for symptom in recent_symptoms_list:
        recent_activities.append({
            'type': 'symptoms',
            'time': symptom.recorded_at,
            'icon': 'warning',
            'description': f'Reported {symptom.name}',
            'details': f'Severity: {symptom.severity if symptom.severity else "N/A"}'
        })
    
    # Sort activities by time (most recent first)
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    # Calculate health score (simplified version)
    health_score = calculate_health_score(current_user.id)
    
    return render_template('health/index.html',
                         today_vitals=today_vitals,
                         active_symptoms_count=active_symptoms_count,
                         severe_symptoms_count=severe_symptoms_count,
                         today_mood=today_mood,
                         daily_checkin=daily_checkin,                         
                         upcoming_appointments=formatted_appointments,
                         recent_activities=recent_activities,
                         health_score=health_score.get('total', 75),                         
                         vitals_score=health_score.get('vitals', 90),
                         lifestyle_score=health_score.get('lifestyle', 70))

def calculate_health_score(user_id):
    """Calculate a comprehensive health score based on various factors"""
    
    # This is a simplified calculation - you can expand this based on your metrics
    
    score = {
        'total': 75,        
        'vitals': 90,
        'lifestyle': 70
    }
    
    try:        
        
        # Calculate vitals score based on recent readings
        recent_vitals = VitalSigns.query.filter_by(
            user_id=user_id
        ).order_by(VitalSigns.recorded_at.desc()).limit(10).all()
        
        if recent_vitals:
            normal_readings = 0
            for vital in recent_vitals:
                if vital.bp_category == 'normal':
                    normal_readings += 1
                if vital.heart_rate and 60 <= vital.heart_rate <= 100:
                    normal_readings += 1
                if vital.temperature and 36 <= vital.temperature <= 37.5:
                    normal_readings += 1
            
            total_metrics = len(recent_vitals) * 3  # BP, HR, Temp
            if total_metrics > 0:
                score['vitals'] = (normal_readings / total_metrics) * 100
        
        # Calculate lifestyle score (based on daily check-ins)
        recent_checkins = DailyCheckin.query.filter_by(
            user_id=user_id
        ).order_by(DailyCheckin.checkin_date.desc()).limit(7).all()
        
        if recent_checkins:
            wellness_sum = sum(c.overall_wellness for c in recent_checkins if c.overall_wellness)
            avg_wellness = wellness_sum / len(recent_checkins) if recent_checkins else 5
            score['lifestyle'] = (avg_wellness / 10) * 100
        
        # Calculate total score (weighted average)
        weights = { 'vitals': 0.7, 'lifestyle': 0.3}
        total = (score['vitals'] * weights['vitals'] + 
                score['lifestyle'] * weights['lifestyle'])
        score['total'] = round(total, 1)
        
    except Exception as e:
        print(f"Error calculating health score: {e}")
    
    return score

# ============================================================================
# HEALTH HUB API ENDPOINTS
# ============================================================================

@health_bp.route('/api/health-hub/quick-checkin', methods=['POST'])
@login_required
def quick_checkin_api():
    """API endpoint for quick daily check-in"""
    data = request.get_json()
    
    today = datetime.utcnow().date()
    
    # Check if already checked in today
    existing_checkin = DailyCheckin.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()
    
    if existing_checkin:
        return jsonify({
            'success': False,
            'message': 'Already checked in today'
        }), 400
    
    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today,
        overall_wellness=data.get('wellness_score', 5),
        notes=data.get('notes'),
        mood_completed=True if data.get('mood_level') else False
    )
    
    db.session.add(checkin)
    
    # Also log mood if provided
    if data.get('mood_level'):
        mood = Mood(
            user_id=current_user.id,
            mood_level=data.get('mood_level'),
            notes=data.get('notes'),
            recorded_at=datetime.utcnow()
        )
        db.session.add(mood)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Quick check-in completed',
        'data': {
            'checkin_id': checkin.id,
            'checkin_date': checkin.checkin_date.isoformat()
        }
    })


@health_bp.route('/api/health-hub/trends/<string:type>')
@login_required
def health_trends_api(type):
    """API endpoint for health trend data"""
    
    days = request.args.get('days', 7, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    if type == 'blood_pressure':
        # Get blood pressure data
        vitals = VitalSigns.query.filter(
            VitalSigns.user_id == current_user.id,
            VitalSigns.recorded_at >= cutoff,
            VitalSigns.systolic_bp.isnot(None),
            VitalSigns.diastolic_bp.isnot(None)
        ).order_by(VitalSigns.recorded_at).all()
        
        data = {
            'labels': [v.recorded_at.strftime('%m/%d') for v in vitals],
            'systolic': [v.systolic_bp for v in vitals],
            'diastolic': [v.diastolic_bp for v in vitals]
        }
        
    elif type == 'mood':
        # Get mood data
        moods = Mood.query.filter(
            Mood.user_id == current_user.id,
            Mood.recorded_at >= cutoff
        ).order_by(Mood.recorded_at).all()
        
        # Map mood levels to numerical values
        mood_values = {
            'excellent': 5,
            'good': 4,
            'fair': 3,
            'poor': 2,
            'anxious': 1,
            'depressed': 1,
            'angry': 1
        }
        
        data = {
            'labels': [m.recorded_at.strftime('%m/%d') for m in moods],
            'values': [mood_values.get(m.mood_level, 3) for m in moods],
            'moods': [m.mood_level for m in moods]
        }
        
    elif type == 'symptoms':
        # Get symptom frequency data
        symptoms_by_day = db.session.query(
            db.func.date(Symptom.recorded_at).label('date'),
            db.func.count(Symptom.id).label('count')
        ).filter(
            Symptom.user_id == current_user.id,
            Symptom.recorded_at >= cutoff
        ).group_by(db.func.date(Symptom.recorded_at))\
         .order_by('date').all()
        
        # Fill in missing days with zero
        all_dates = []
        all_counts = []
        current_date = cutoff.date()
        today = datetime.utcnow().date()
        
        while current_date <= today:
            count = next((s.count for s in symptoms_by_day if s.date == current_date), 0)
            all_dates.append(current_date.strftime('%m/%d'))
            all_counts.append(count)
            current_date += timedelta(days=1)
        
        data = {
            'labels': all_dates,
            'values': all_counts
        }
        
    else:
        data = {'labels': [], 'values': []}
    
    return jsonify(data)

@health_bp.route('/api/health-hub/summary')
@login_required
def health_summary_api():
    """API endpoint for health summary data"""
    
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Today's vitals
    today_vitals = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        db.func.date(VitalSigns.recorded_at) == today
    ).order_by(VitalSigns.recorded_at.desc()).first()
    
    # Active symptoms
    active_symptoms = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    # Today's mood
    today_mood = Mood.query.filter(
        Mood.user_id == current_user.id,
        db.func.date(Mood.recorded_at) == today
    ).order_by(Mood.recorded_at.desc()).first()
    
    # Daily check-in status
    daily_checkin = DailyCheckin.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()      
    
    
    # Upcoming appointments (next 3 days)
    upcoming_appointments = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == current_user.id,
        MedicalEvaluation.follow_up_date >= today,
        MedicalEvaluation.follow_up_date <= today + timedelta(days=3)
    ).count()
    
    return jsonify({
        'today_vitals': {
            'blood_pressure': today_vitals.blood_pressure if today_vitals else None,
            'heart_rate': today_vitals.heart_rate if today_vitals else None,
            'temperature': today_vitals.temperature if today_vitals else None,
            'recorded_at': today_vitals.recorded_at.isoformat() if today_vitals else None
        },
        'active_symptoms': active_symptoms,
        'today_mood': {
            'mood_level': today_mood.mood_level if today_mood else None,
            'energy_level': today_mood.energy_level if today_mood else None
        },
        'daily_checkin_completed': daily_checkin is not None,        
        'upcoming_appointments': upcoming_appointments,
        'health_score': calculate_health_score(current_user.id)
    })

@health_bp.route('/api/health-hub/quick-actions')
@login_required
def quick_actions_api():
    """API endpoint for quick action suggestions"""
    
    today = datetime.utcnow().date()
    suggestions = []
    
    # Check if daily check-in is needed
    daily_checkin = DailyCheckin.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()
    
    if not daily_checkin:
        suggestions.append({
            'action': 'daily_checkin',
            'title': 'Complete Daily Check-in',
            'description': 'Track your daily health metrics',
            'icon': 'check_circle',
            'priority': 'high',
            'url': '#daily-checkin-modal'
        })
    
    # Check if vitals haven't been recorded today
    today_vitals = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        db.func.date(VitalSigns.recorded_at) == today
    ).first()
    
    if not today_vitals:
        suggestions.append({
            'action': 'record_vitals',
            'title': 'Record Vital Signs',
            'description': 'Track your blood pressure and heart rate',
            'icon': 'favorite',
            'priority': 'medium',
            'url': url_for('health.vitals')
        })
    
    # Check for active symptoms that need attention
    severe_symptoms = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active',
        severity='severe'
    ).count()
    
    if severe_symptoms > 0:
        suggestions.append({
            'action': 'review_symptoms',
            'title': 'Review Severe Symptoms',
            'description': f'You have {severe_symptoms} severe symptom(s)',
            'icon': 'warning',
            'priority': 'high',
            'url': url_for('health.symptoms')
        })
    
    # Check for upcoming appointments tomorrow
    tomorrow = today + timedelta(days=1)
    tomorrow_appointments = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == current_user.id,
        MedicalEvaluation.follow_up_date == tomorrow
    ).count()
    
    if tomorrow_appointments > 0:
        suggestions.append({
            'action': 'prepare_appointment',
            'title': 'Prepare for Appointment',
            'description': f'You have {tomorrow_appointments} appointment(s) tomorrow',
            'icon': 'event',
            'priority': 'medium',
            'url': url_for('health.evaluations')
        })
    
    

# ============================================================================
# CONTEXT PROCESSORS FOR HEALTH HUB
# ============================================================================

@health_bp.context_processor
def inject_health_data():
    """Inject common health data into all templates"""
    if current_user.is_authenticated:
        today = datetime.utcnow().date()
        
        # Today's check-in status
        daily_checkin = DailyCheckin.query.filter_by(
            user_id=current_user.id,
            checkin_date=today
        ).first()        
        
        
        # Emergency contact
        from app.models import EmergencyContact
        emergency_contact = EmergencyContact.query.filter_by(
            user_id=current_user.id,
            is_primary=True
        ).first()
        
        return {
            'daily_checkin': daily_checkin,            
            'emergency_contact': emergency_contact,
            'today': today,
            'now': datetime.utcnow
        }
    return {}

# ============================================================================
# VITAL SIGNS ROUTES
# ============================================================================

@health_bp.route('/vitals', methods=['GET', 'POST'])
@login_required
def vitals():
    """View and record vital signs"""
    form = VitalSignsForm()
    
    if form.validate_on_submit():
        vital = VitalSigns(
            user_id=current_user.id,
            systolic_bp=form.systolic_bp.data,
            diastolic_bp=form.diastolic_bp.data,
            heart_rate=form.heart_rate.data,
            respiratory_rate=form.respiratory_rate.data,
            temperature=form.temperature.data,
            oxygen_saturation=form.oxygen_saturation.data,
            pain_level=form.pain_level.data,
            blood_glucose=form.blood_glucose.data,
            weight_kg=form.weight_kg.data,
            height_cm=form.height_cm.data,
            recorded_at=form.recorded_at.data or datetime.utcnow(),
            notes=form.notes.data
        )
        
        db.session.add(vital)
        db.session.commit()

        # Create notification
        
        notification_service.create_notification(
             user=current_user.id,
            title='Vital Signs Recorded',
            message='Your vital signs have been recorded.',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Vital signs recorded successfully!', 'success')
        return redirect(url_for('health.vitals'))
    
    # Get recent vitals
    recent_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .limit(10).all()
    
    # Get vitals summary for dashboard
    today = datetime.utcnow().date()
    today_vitals = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        db.func.date(VitalSigns.recorded_at) == today
    ).first()
    
    return render_template('health/vitals.html',
                         form=form,
                         recent_vitals=recent_vitals,
                         today_vitals=today_vitals)


@health_bp.route('/api/vitals/<int:id>', methods=['DELETE'])
@login_required
def delete_vital_api(id):
    """API endpoint to delete vital signs"""
    vital = VitalSigns.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(vital)
    db.session.commit()

    #Notification
    
    notification_service.create_notification(
             user=current_user.id,
            title='Vital Signs Deleted',
            message='Your vital signs have been deleted.',
            type = 'health_alert',
            priority = 'medium'
        )
    
    return jsonify({
        'success': True,
        'message': 'Vital signs deleted successfully'
    })

@health_bp.route('/api/vitals/chart-data')
@login_required
def vitals_chart_data():
    """API endpoint for vital signs chart data"""
    days = request.args.get('days', 30, type=int)
    vital_type = request.args.get('type', 'blood_pressure')
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        VitalSigns.recorded_at >= cutoff
    ).order_by(VitalSigns.recorded_at)
    
    if vital_type == 'blood_pressure':
        vitals = query.filter(
            VitalSigns.systolic_bp.isnot(None),
            VitalSigns.diastolic_bp.isnot(None)
        ).all()
        
        data = {
            'labels': [v.recorded_at.strftime('%Y-%m-%d %H:%M') for v in vitals],
            'systolic': [v.systolic_bp for v in vitals],
            'diastolic': [v.diastolic_bp for v in vitals]
        }
    
    elif vital_type == 'heart_rate':
        vitals = query.filter(VitalSigns.heart_rate.isnot(None)).all()
        data = {
            'labels': [v.recorded_at.strftime('%Y-%m-%d %H:%M') for v in vitals],
            'values': [v.heart_rate for v in vitals]
        }
    
    elif vital_type == 'temperature':
        vitals = query.filter(VitalSigns.temperature.isnot(None)).all()
        data = {
            'labels': [v.recorded_at.strftime('%Y-%m-%d %H:%M') for v in vitals],
            'values': [v.temperature for v in vitals]
        }
    
    else:
        data = {'labels': [], 'values': []}
    
    return jsonify(data)

# ============================================================================
# SYMPTOMS ROUTES
# ============================================================================

@health_bp.route('/symptoms', methods=['GET', 'POST'])
@login_required
def symptoms():
    """View and record symptoms"""
    form = SymptomForm()
    
    if form.validate_on_submit():
        # Calculate total duration in minutes
        duration_minutes = form.duration_minutes.data or 0
        if form.duration_hours.data:
            duration_minutes += form.duration_hours.data * 60
        
        symptom = Symptom(
            user_id=current_user.id,
            name=form.name.data,
            severity=form.severity.data,
            duration_minutes=duration_minutes,
            frequency=form.frequency.data,
            body_location=form.body_location.data,
            triggers=form.triggers.data,
            alleviating_factors=form.alleviating_factors.data,
            notes=form.notes.data
        )
        
        db.session.add(symptom)
        db.session.commit()

        #Notification
        
        notification_service.create_notification(
             user=current_user.id,
            title='Symptoms Recorded',
            message='Your symptoms have been recorded.',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Symptom recorded successfully!', 'success')
        return redirect(url_for('health.symptoms'))
    
    # Get symptoms
    active_symptoms = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Symptom.recorded_at.desc()).all()
    
    recent_symptoms = Symptom.query.filter_by(user_id=current_user.id)\
        .order_by(Symptom.recorded_at.desc())\
        .limit(20).all()
    
    # Symptom statistics
    symptom_stats = {
        'total': Symptom.query.filter_by(user_id=current_user.id).count(),
        'active': len(active_symptoms),
        'severe': sum(1 for s in active_symptoms if s.severity == 'severe'),
        'by_severity': {
            'mild': sum(1 for s in active_symptoms if s.severity == 'mild'),
            'moderate': sum(1 for s in active_symptoms if s.severity == 'moderate'),
            'severe': sum(1 for s in active_symptoms if s.severity == 'severe')
        }
    }
    
    return render_template('health/symptoms.html',
                         form=form,
                         active_symptoms=active_symptoms,
                         recent_symptoms=recent_symptoms,
                         symptom_stats=symptom_stats)



@health_bp.route('/api/symptoms/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_symptom_api(id):
    """API endpoint to resolve symptom"""
    symptom = Symptom.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    symptom.status = 'resolved'
    symptom.resolved_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Symptom resolved successfully'
    })


@health_bp.route('/api/symptoms/trend')
@login_required
def symptoms_trend():
    """API endpoint for symptom trends"""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Group symptoms by day
    symptoms_by_day = db.session.query(
        db.func.date(Symptom.recorded_at).label('date'),
        db.func.count(Symptom.id).label('count')
    ).filter(
        Symptom.user_id == current_user.id,
        Symptom.recorded_at >= cutoff
    ).group_by(db.func.date(Symptom.recorded_at))\
     .order_by('date').all()
    
    data = {
        'dates': [row.date.strftime('%Y-%m-%d') for row in symptoms_by_day],
        'counts': [row.count for row in symptoms_by_day]
    }
    
    return jsonify(data)

# ============================================================================
# MOOD TRACKING ROUTES
# ============================================================================

@health_bp.route('/mood', methods=['GET', 'POST'])
@login_required
def mood():
    """Track mood"""
    form = MoodForm()
    
    if form.validate_on_submit():
        mood_entry = Mood(
            user_id=current_user.id,
            mood_level=form.mood_level.data,
            energy_level=form.energy_level.data,
            stress_level=form.stress_level.data,
            sleep_hours=form.sleep_hours.data,
            sleep_quality=form.sleep_quality.data,
            notes=form.notes.data
        )
        
        db.session.add(mood_entry)
        db.session.commit()
        
        #Notification
        
        notification_service.create_notification(
             user=current_user.id,
            title='Mood Recorded',
            message='Your mood has been recorded.',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Mood recorded successfully!', 'success')
        return redirect(url_for('health.mood'))
    
    # Get recent mood entries
    recent_moods = Mood.query.filter_by(user_id=current_user.id)\
        .order_by(Mood.recorded_at.desc())\
        .limit(20).all()
    
    # Get today's mood if exists
    today = datetime.utcnow().date()
    today_mood = Mood.query.filter(
        Mood.user_id == current_user.id,
        db.func.date(Mood.recorded_at) == today
    ).first()
    
    return render_template('health/mood.html',
                         form=form,
                         recent_moods=recent_moods,
                         today_mood=today_mood)

@health_bp.route('/api/mood/calendar')
@login_required
def mood_calendar():
    """API endpoint for mood calendar data"""
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    moods = Mood.query.filter(
        Mood.user_id == current_user.id,
        Mood.recorded_at >= start_date,
        Mood.recorded_at < end_date
    ).all()
    
    # Map mood levels to colors/values
    mood_map = {
        'excellent': 5,
        'good': 4,
        'fair': 3,
        'poor': 2,
        'depressed': 1,
        'anxious': 2,
        'angry': 1
    }
    
    calendar_data = {}
    for mood in moods:
        date_str = mood.recorded_at.date().isoformat()
        calendar_data[date_str] = {
            'value': mood_map.get(mood.mood_level, 3),
            'mood': mood.mood_level,
            'notes': mood.notes[:50] if mood.notes else ''
        }
    
    return jsonify(calendar_data)

# ============================================================================
# DAILY CHECK-IN ROUTES
# ============================================================================

@health_bp.route('/api/daily-checkin', methods=['POST'])
@login_required
def daily_checkin_api():
    """API endpoint for daily check-in"""
    data = request.get_json()
    
    today = datetime.utcnow().date()
    
    # Check if already checked in today
    existing_checkin = DailyCheckin.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()
    
    if existing_checkin:
        return jsonify({
            'success': False,
            'message': 'Already checked in today'
        }), 400
    
    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today,
        overall_wellness=data.get('overall_wellness'),
        medications_taken=json.dumps(data.get('medications_taken', [])),
        water_intake=data.get('water_intake'),
        exercise_minutes=data.get('exercise_minutes'),
        meals_eaten=data.get('meals_eaten'),
        notes=data.get('notes')
    )
    
    db.session.add(checkin)
    db.session.commit()
    #Notification
   
    notification_service.create_notification(
             user=current_user.id,
            title='Daily Check-in Completed',
            message='Your daily check-in has been completed.',
            type = 'health_alert',
            priority = 'medium'
        )
    
    return jsonify({
        'success': True,
        'message': 'Daily check-in completed',
        'data': {
            'id': checkin.id,
            'checkin_date': checkin.checkin_date.isoformat(),
            'overall_wellness': checkin.overall_wellness
        }
    })


@health_bp.route('/checkin/history')
@login_required
def checkin_history():
    """View check-in history"""
    checkins = DailyCheckin.query.filter_by(user_id=current_user.id)\
        .order_by(DailyCheckin.checkin_date.desc())\
        .all()
    
    # Calculate streak
    streak = 0
    today = datetime.utcnow().date()
    current_date = today
    
    while True:
        checkin_exists = DailyCheckin.query.filter_by(
            user_id=current_user.id,
            checkin_date=current_date
        ).first()
        
        if not checkin_exists:
            break
        
        streak += 1
        current_date -= timedelta(days=1)
    
    return render_template('health/checkin_history.html',
                         checkins=checkins,
                         streak=streak)

# ============================================================================
# MEDICAL EVALUATIONS ROUTES
# ============================================================================

@health_bp.route('/evaluations', methods=['GET', 'POST'])
@login_required
def evaluations():
    """View and manage medical evaluations"""
    form = MedicalEvaluationForm()
    comprehensive_form = ComprehensiveEvaluationForm()
    
    if form.validate_on_submit():
        evaluation = MedicalEvaluation(
            user_id=current_user.id,
            evaluation_date=form.evaluation_date.data,
            evaluation_type=form.evaluation_type.data if form.evaluation_type.data != 'other' else form.other_type.data,
            provider_name=form.provider_name.data,
            clinic_name=form.clinic_name.data,
            chief_complaint=form.chief_complaint.data,
            diagnosis=form.diagnosis.data,
            summary=form.summary.data,
            recommendations=form.recommendations.data,
            follow_up_date=form.follow_up_date.data
        )
        
        db.session.add(evaluation)
        db.session.commit()
        #Notification
        
        notification_service.create_notification(
             user=current_user.id,
            title='Medical Evaluation Completed',
            message='Your medical evaluation has been completed.',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Medical evaluation saved!', 'success')
        return redirect(url_for('health.evaluations'))
    
    # Get evaluations
    evaluations = MedicalEvaluation.query.filter_by(user_id=current_user.id)\
        .order_by(MedicalEvaluation.evaluation_date.desc())\
        .all()
    
    upcoming_evaluations = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == current_user.id,
        MedicalEvaluation.follow_up_date >= datetime.utcnow().date()
    ).order_by(MedicalEvaluation.follow_up_date).all()
    
    return render_template('health/evaluations.html',
                         form=form,
                         comprehensive_form=comprehensive_form,
                         evaluations=evaluations,
                         upcoming_evaluations=upcoming_evaluations)



# ============================================================================
# LAB TESTS ROUTES
# ============================================================================

@health_bp.route('/lab-tests', methods=['GET', 'POST'])
@login_required
def lab_tests():
    """View and manage lab tests"""
    form = LabTestForm()
    search_form = LabTestSearchForm()
    
    # Handle search/filter
    query = LabTest.query.filter_by(user_id=current_user.id)
    
    if request.method == 'GET' and 'test_name' in request.args:
        if request.args.get('test_name'):
            query = query.filter(LabTest.test_name.ilike(f"%{request.args['test_name']}%"))
        
        if request.args.get('category'):
            query = query.filter_by(test_category=request.args['category'])
        
        if request.args.get('result_status'):
            query = query.filter_by(result_status=request.args['result_status'])
    
    # Apply date filter
    date_filter = request.args.get('date_range', 'year')
    if date_filter != 'all':
        if date_filter == 'year':
            cutoff = datetime.utcnow() - timedelta(days=365)
        elif date_filter == '6months':
            cutoff = datetime.utcnow() - timedelta(days=180)
        elif date_filter == '3months':
            cutoff = datetime.utcnow() - timedelta(days=90)
        elif date_filter == 'month':
            cutoff = datetime.utcnow() - timedelta(days=30)
        else:
            cutoff = datetime.utcnow()
        
        query = query.filter(LabTest.test_date >= cutoff)
    
    # Sort results
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(LabTest.test_date.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(LabTest.test_date.asc())
    elif sort_by == 'name':
        query = query.order_by(LabTest.test_name)
    elif sort_by == 'category':
        query = query.order_by(LabTest.test_category)
    
    lab_tests = query.all()
    
    # Handle form submission for new lab test
    if form.validate_on_submit():
        lab_test = LabTest(
            user_id=current_user.id,
            test_name=form.test_name.data,
            test_category=form.test_category.data,
            loinc_code=form.loinc_code.data,
            result_value=form.result_value.data,
            result_unit=form.result_unit.data,
            reference_range=form.reference_range.data,
            result_status=form.result_status.data,
            test_date=form.test_date.data,
            result_date=form.result_date.data,
            lab_name=form.lab_name.data,
            ordering_provider=form.ordering_provider.data,
            notes=form.notes.data
        )
        
        # Handle file upload
        if form.report_file.data:
            success, result = FileUploadService.save_uploaded_file(
                form.report_file.data,
                subfolder='lab_reports',
                file_type='documents',
                user_id=current_user.id
            )
            if success:
                lab_test.report_url = FileUploadService.get_file_url(result)
        
        db.session.add(lab_test)
        db.session.commit()
        # Notification
        
        notification_service.create_notification(
             user=current_user.id,
            title='New Lab Test',
            message='A new lab test has been added.',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Lab test saved successfully!', 'success')
        return redirect(url_for('health.lab_tests'))
    
    return render_template('health/lab_tests.html',
                         form=form,
                         search_form=search_form,
                         lab_tests=lab_tests)


@health_bp.route('/api/lab-tests/<int:id>', methods=['DELETE'])
@login_required
def delete_lab_test_api(id):
    """API endpoint to delete lab test"""
    lab_test = LabTest.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(lab_test)
    db.session.commit()
    #Notificatoion
    
    notification_service.create_notification(
             user=current_user.id,
            title='Lab Test Deleted',
            message='A lab test has been deleted.',
            type = 'health_alert',
            priority = 'medium'
    )
    
    return jsonify({
        'success': True,
        'message': 'Lab test deleted successfully'
    })



@health_bp.route('/lab-trends', methods=['GET', 'POST'])
@login_required
def lab_trends():
    """View lab test trends over time"""
    form = LabTrendForm()
    
    # Get unique test names for autocomplete
    test_names = db.session.query(LabTest.test_name)\
        .filter_by(user_id=current_user.id)\
        .distinct()\
        .order_by(LabTest.test_name)\
        .all()
    
    test_names = [name[0] for name in test_names]
    
    if form.validate_on_submit():
        # Process trend view request
        test_name = form.test_name.data
        time_period = form.time_period.data
        
        # Calculate date cutoff
        if time_period == '3months':
            cutoff = datetime.utcnow() - timedelta(days=90)
        elif time_period == '6months':
            cutoff = datetime.utcnow() - timedelta(days=180)
        elif time_period == 'year':
            cutoff = datetime.utcnow() - timedelta(days=365)
        elif time_period == '2years':
            cutoff = datetime.utcnow() - timedelta(days=730)
        else:
            cutoff = None
        
        # Query lab tests
        query = LabTest.query.filter_by(
            user_id=current_user.id,
            test_name=test_name
        )
        
        if cutoff:
            query = query.filter(LabTest.test_date >= cutoff)
        
        lab_tests = query.order_by(LabTest.test_date).all()
        
        # Prepare data for chart
        chart_data = {
            'dates': [test.test_date.strftime('%Y-%m-%d') for test in lab_tests],
            'values': [test.result_value for test in lab_tests],
            'units': lab_tests[0].result_unit if lab_tests else '',
            'reference_range': lab_tests[0].reference_range if lab_tests else ''
        }
        
        return render_template('health/lab_trends.html',
                             form=form,
                             test_names=test_names,
                             chart_data=chart_data,
                             show_chart=True)
    
    return render_template('health/lab_trends.html',
                         form=form,
                         test_names=test_names,
                         show_chart=False)

@health_bp.route('/api/lab-tests/export')
@login_required
def export_lab_tests():
    """Export lab tests as CSV"""
    # Get lab tests
    lab_tests = LabTest.query.filter_by(user_id=current_user.id)\
        .order_by(LabTest.test_date.desc())\
        .all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Test Name', 'Category', 'Test Date', 'Result Date',
        'Result Value', 'Unit', 'Reference Range', 'Status',
        'Laboratory', 'Notes'
    ])
    
    # Write data
    for test in lab_tests:
        writer.writerow([
            test.test_name,
            test.test_category,
            test.test_date.strftime('%Y-%m-%d') if test.test_date else '',
            test.result_date.strftime('%Y-%m-%d') if test.result_date else '',
            test.result_value,
            test.result_unit or '',
            test.reference_range or '',
            test.result_status,
            test.lab_name or '',
            test.notes or ''
        ])
    
    output.seek(0)
    
    # Create response
    response = send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'lab_tests_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    )
    # Ntofication
    
    notification_service.create_notification(
             user=current_user.id,
            title='Lab Tests Exported',
            message='Lab tests have been exported.',
            type = 'health_alert',
            priority = 'medium'
    )
    
    return response

# ============================================================================
# IMAGING STUDIES ROUTES
# ============================================================================

@health_bp.route('/imaging', methods=['GET', 'POST'])
@login_required
def imaging_studies():
    """View and manage imaging studies"""
    form = ImagingStudyForm()
    search_form = ImagingSearchForm()
    
    # Handle search/filter
    query = ImagingStudy.query.filter_by(user_id=current_user.id)
    
    if request.method == 'GET' and 'study_type' in request.args:
        if request.args.get('study_type'):
            query = query.filter_by(study_type=request.args['study_type'])
        
        if request.args.get('body_part'):
            query = query.filter(ImagingStudy.body_part.ilike(f"%{request.args['body_part']}%"))
        
        if request.args.get('has_follow_up') == 'required':
            query = query.filter_by(follow_up_required=True)
        elif request.args.get('has_follow_up') == 'completed':
            query = query.filter(ImagingStudy.follow_up_date != None)
        elif request.args.get('has_follow_up') == 'none':
            query = query.filter_by(follow_up_required=False)
    
    # Apply date filter
    date_filter = request.args.get('date_range', 'year')
    if date_filter == 'year':
        cutoff = datetime.utcnow() - timedelta(days=365)
        query = query.filter(ImagingStudy.study_date >= cutoff)
    elif date_filter == '6months':
        cutoff = datetime.utcnow() - timedelta(days=180)
        query = query.filter(ImagingStudy.study_date >= cutoff)
    elif date_filter == '3months':
        cutoff = datetime.utcnow() - timedelta(days=90)
        query = query.filter(ImagingStudy.study_date >= cutoff)
    
    # Sort results
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(ImagingStudy.study_date.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(ImagingStudy.study_date.asc())
    elif sort_by == 'type':
        query = query.order_by(ImagingStudy.study_type)
    
    imaging_studies = query.all()
    
    # Handle form submission for new imaging study
    if form.validate_on_submit():
        imaging_study = ImagingStudy(
            user_id=current_user.id,
            study_type=form.study_type.data if form.study_type.data != 'other' else form.other_type.data,
            body_part=form.body_part.data,
            contrast_used=form.contrast_used.data,
            radiation_dose=form.radiation_dose.data,
            study_date=form.study_date.data,
            report_date=form.report_date.data,
            radiologist=form.radiologist.data,
            facility_name=form.facility_name.data,
            findings=form.findings.data,
            impression=form.impression.data,
            recommendations=form.recommendations.data,
            follow_up_required=form.follow_up_required.data,
            follow_up_date=form.follow_up_date.data if form.follow_up_required.data else None,
            notes=form.notes.data
        )
        
        # Handle file uploads
        if form.report_file.data:
            success, result = FileUploadService.save_uploaded_file(
                form.report_file.data,
                subfolder='imaging_reports',
                file_type='documents',
                user_id=current_user.id
            )
            if success:
                imaging_study.report_url = FileUploadService.get_file_url(result)
        
        # Handle image uploads
        image_urls = []
        if form.image_files.data:
            for image_file in form.image_files.data:
                if image_file and image_file.filename:
                    success, result = FileUploadService.save_uploaded_file(
                        image_file,
                        subfolder='imaging_images',
                        file_type='images',
                        user_id=current_user.id
                    )
                    if success:
                        image_urls.append(FileUploadService.get_file_url(result))
        
        # Add text URLs
        if form.image_urls.data:
            urls = [url.strip() for url in form.image_urls.data.split('\n') if url.strip()]
            image_urls.extend(urls)
        
        if image_urls:
            imaging_study.image_urls = image_urls
        
        db.session.add(imaging_study)
        db.session.commit()
        
        #Notification
        notification_service.create_notification(
            user_id=current_user.id,
            title='New Imaging Study',
            message = 'New Imaging Study',
            type = 'health_alert',
            priority = 'medium'
        )
        
        
        flash('Imaging study saved successfully!', 'success')
        return redirect(url_for('health.imaging_studies'))
    
    return render_template('health/imaging_studies.html',
                         form=form,
                         search_form=search_form,
                         imaging_studies=imaging_studies)

@health_bp.route('api/imaging/<int:id>')
@login_required
def imaging_detail(id):
    """View detailed imaging study"""
    imaging_study = ImagingStudy.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify(imaging_study.to_dict())

@health_bp.route('/api/imaging/<int:id>', methods=['DELETE'])
@login_required
def delete_imaging_api(id):
    """API endpoint to delete imaging study"""
    imaging_study = ImagingStudy.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(imaging_study)
    db.session.commit()
    #Notification
    notification_service.create_notification(
        user_id=current_user.id,
        title='Imaging Study Deleted',
        message = 'Imaging Study Deleted',
        type = 'health_alert',
        priority = 'medium'
    )
    
    return jsonify({
        'success': True,
        'message': 'Imaging study deleted successfully'
    })


# ============================================================================
# HEALTH CONDITIONS & ALLERGIES ROUTES
# ============================================================================

@health_bp.route('/conditions')
@login_required
def conditions():
    """View health conditions"""
    conditions = HealthCondition.query.filter_by(user_id=current_user.id)\
        .order_by(HealthCondition.diagnosis_date.desc())\
        .all()
    
    active_conditions = [c for c in conditions if c.status == 'active']
    resolved_conditions = [c for c in conditions if c.status == 'resolved']
    
    return render_template('health/conditions.html',
                         active_conditions=active_conditions,
                         resolved_conditions=resolved_conditions)

@health_bp.route('/conditions/new', methods=['GET', 'POST'])
@login_required
def new_condition():
    """Create new health condition"""
    form = HealthConditionForm()
    
    if form.validate_on_submit():
        condition = HealthConditionForm(
            name=form.name.data,
            diagnosis_date=form.diagnosis_date.data,
            type=form.type.data if form.type.data != 'other' else form.other_type.data,
            icd10_code=form.icd10_code.data,
            severity=form.severity.data,
            status=form.status.data,
            notes=form.notes.data,
            treatments=form.treatments.data,
            symptoms=form.symptoms.data,
            provider_name=form.provider_name.data,
            user_id=current_user.id      

        )
        
        db.session.add(condition)
        db.session.commit()
        #Notification
        notification_service.create_notification(
            user_id=current_user.id,
            title='New Health Condition',
            message = 'New Health Condition',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Health condition saved successfully!', 'success')
        return redirect(url_for('health.conditions'))
    
    return render_template('health/new_condition.html', form=form)
@health_bp.route('api/conditions/<int:id>', methods=['GET'] )
@login_required
def condition_detail(id):
    """View detailed health condition"""
    condition = HealthCondition.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify(condition.to_dict())
@health_bp.route('/api/conditions/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_condition_api(id):
    """API endpoint to resolve health condition"""
    condition = HealthCondition.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    condition.status = 'resolved'
    condition.resolved_at = datetime.utcnow()
    db.session.commit()
    
    #Notification
    notification_service.create_notification(
        user_id=current_user.id,
        title='Health condition resolved',
        message = 'Health condition resolved',
        type = 'health_alert',
        priority = 'medium'
    )
    return jsonify({
        'success': True,
        'message': 'Health condition resolved successfully'
    })
@health_bp.route('/api/conditions/<int:id>', methods=['DELETE'])
@login_required
def delete_condition_api(id):
    """API endpoint to delete health condition"""
    condition = HealthCondition.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(condition)
    db.session.commit()
    #Notification
    notification_service.create_notification(
        user_id=current_user.id,
        title='Health condition deleted',
        message = 'Health condition deleted',
        type = 'health_alert',
        priority = 'medium'
    )
    
    return jsonify({
        'success': True,
        'message': 'Health condition deleted successfully'
    })
@health_bp.route('/allergies')
@login_required
def allergies():
    """View allergies"""
    allergies = Allergy.query.filter_by(user_id=current_user.id)\
        .order_by(Allergy.severity.desc())\
        .all()
    
    active_allergies = [a for a in allergies if a.status == 'active']
    resolved_allergies = [a for a in allergies if a.status == 'resolved']
    
    return render_template('health/allergies.html',
                         active_allergies=active_allergies,
                         resolved_allergies=resolved_allergies)
@health_bp.route('/allergies/new', methods=['GET', 'POST'])
@login_required
def new_allergy():
    """Create new allergy"""
    form = AllergyForm()
    
    if form.validate_on_submit():
        allergy = Allergy(
            name=form.name.data,
            severity=form.severity.data,
            status=form.status.data,
            notes=form.notes.data,
            treatments=form.treatments.data,
            reaction=form.reaction.data,
            is_confirmed=form.is_confirmed.data,
            user_id=current_user.id
        )
        
        db.session.add(allergy)
        db.session.commit()
        #Notification
        
        notification_service.create_notification(
            user_id=current_user.id,
            title='New Allergy',
            message = 'New Allergy recorded',
            type = 'health_alert',
            priority = 'medium'
        )
        
        flash('Allergy saved successfully!', 'success')
        return redirect(url_for('health.allergies'))
    
    return render_template('health/new_allergy.html', form=form)
@health_bp.route('api/allergies/<int:id>', methods=['GET'] )
@login_required
def allergy_detail(id):
    """View detailed allergy"""
    allergy = Allergy.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify(allergy.to_dict())
@health_bp.route('/api/allergies/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_allergy_api(id):
    """API endpoint to resolve allergy"""
    allergy = Allergy.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    allergy.status = 'resolved'
    allergy.resolved_at = datetime.utcnow()
    db.session.commit()
    
    #Notification    
    notification_service.create_notification(
        user_id=current_user.id,
        title='Allergy resolved',
        message = 'Allergy resolved',
        type = 'health_alert',
        priority = 'medium'
    )
    
    return jsonify({
        'success': True,
        'message': 'Allergy resolved successfully'
    })
@health_bp.route('/api/allergies/<int:id>', methods=['DELETE'])
@login_required
def delete_allergy_api(id):
    """API endpoint to delete allergy"""
    allergy = Allergy.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(allergy)
    db.session.commit()

    #Notification
    notification_service.create_notification(
        user_id=current_user.id,
        title='Allergy deleted',
        message = 'Allergy deleted',
        type = 'health_alert',
        priority = 'medium'
    )
    
    return jsonify({
        'success': True,
        'message': 'Allergy deleted successfully'
    })

# ============================================================================
# PROVIDERS ROUTES
# ============================================================================

@health_bp.route('/providers')
@login_required
def providers():
    """View healthcare providers"""
    providers = HealthcareProvider.query.filter_by(user_id=current_user.id)\
        .order_by(HealthcareProvider.is_primary.desc(),
                 HealthcareProvider.name)\
        .all()
    
    primary_provider = next((p for p in providers if p.is_primary), None)
    other_providers = [p for p in providers if not p.is_primary]
    
    return render_template('health/providers.html',
                         primary_provider=primary_provider,
                         other_providers=other_providers)

# ============================================================================
# HEALTH DASHBOARD & SUMMARY ROUTES
# ============================================================================

@health_bp.route('/summary')
@login_required
def health_summary():
    """Health summary dashboard"""
    # Get recent data
    recent_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .first()
    
    active_symptoms = Symptom.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    recent_lab_tests = LabTest.query.filter_by(user_id=current_user.id)\
        .order_by(LabTest.test_date.desc())\
        .limit(5).all()
    
    upcoming_evaluations = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == current_user.id,
        MedicalEvaluation.follow_up_date >= datetime.utcnow().date()
    ).order_by(MedicalEvaluation.follow_up_date)\
     .limit(3).all()
    
    # Calculate adherence for the week
    week_ago = datetime.utcnow() - timedelta(days=7)
    from app.models import Dose, Prescription
    recent_doses = Dose.query.join(Prescription)\
        .filter(
            Prescription.user_id == current_user.id,
            Dose.scheduled_time >= week_ago
        ).all()
    
    if recent_doses:
        adherence_rate = round(sum(1 for d in recent_doses if d.status == 'taken') / len(recent_doses) * 100, 1)
    else:
        adherence_rate = 100.0
    
    return render_template('health/summary.html',
                         recent_vitals=recent_vitals,
                         active_symptoms=active_symptoms,
                         recent_lab_tests=recent_lab_tests,
                         upcoming_evaluations=upcoming_evaluations,
                         adherence_rate=adherence_rate)

@health_bp.route('/report')
@login_required
def health_report():
    """Generate health report"""
    # Get data for the report
    vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .limit(20).all()
    
    conditions = HealthCondition.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    allergies = Allergy.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    recent_lab_tests = LabTest.query.filter_by(user_id=current_user.id)\
        .order_by(LabTest.test_date.desc())\
        .limit(10).all()
    
    from app.models import Medication, Prescription
    medications = Medication.query.join(Prescription)\
        .filter(
            Prescription.user_id == current_user.id,
            Prescription.status == 'active'
        ).all()
    
    return render_template('health/report.html',
                         vitals=vitals,
                         conditions=conditions,
                         allergies=allergies,
                         medications=medications,
                         lab_tests=recent_lab_tests)








