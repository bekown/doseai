# app/insights/routes.py

from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from app import db
from app.models import (
    Medication, Prescription, Dose, VitalSigns, Symptom,
    DailyCheckin, WellnessScore, AIInsight, AdherenceTrend,
    DrugInteraction, Contraindication, MedicationInventory,
    HealthCondition, Allergy, Goal, GoalCategory, GoalSetting
)
from app.utils.ai_service import AIService
from app.utils.helpers import Helper
from .forms import InsightFilterForm, ExportDataForm, GoalSettingForm

from app.utils.notification_service import InsightsNotificationService
from app.utils.insight_analyzer import InsightAnalyzer

insights_bp = Blueprint('insights', __name__)
insights_api_bp = Blueprint('/api/insights', __name__)
ai_service = AIService()

# ============================================================================
# MAIN INSIGHTS DASHBOARD
# ============================================================================

@insights_bp.route('/')
@login_required
def index():
    """Main insights dashboard"""
    user_id = current_user.id
    
    # Calculate adherence rate
    adherence_rate = Helper.calculate_adherence_rate(user_id, days=30)
    
    # Get latest wellness score
    wellness_score = WellnessScore.query.filter_by(user_id=user_id)\
        .order_by(WellnessScore.calculation_date.desc())\
        .first()
    
    # Get recent AI insights
    ai_insights = AIInsight.query.filter_by(user_id=user_id)\
        .filter(
            (AIInsight.expires_at.is_(None)) |
            (AIInsight.expires_at > datetime.utcnow())
        )\
        .order_by(AIInsight.created_at.desc())\
        .limit(5).all()
    
    # Get adherence trends
    adherence_trends = AdherenceTrend.query.filter_by(user_id=user_id)\
        .order_by(AdherenceTrend.period_start.desc())\
        .limit(4).all()
    
    # Get medication performance
    from sqlalchemy import func
    medication_performance = db.session.query(
        Medication.name,
        Prescription.frequency,
        func.count(Dose.id).label('total_doses'),
        func.sum(func.case([(Dose.status == 'taken', 1)], else_=0)).label('taken_doses')
    ).join(Prescription, Prescription.medication_id == Medication.id)\
     .join(Dose, Dose.prescription_id == Prescription.id)\
     .filter(
        Prescription.user_id == user_id,
        Prescription.status == 'active'
     ).group_by(Medication.name, Prescription.frequency).all()
    
    # Calculate adherence rates for each medication
    med_performance_data = []
    for med in medication_performance:
        if med.total_doses > 0:
            rate = round((med.taken_doses / med.total_doses) * 100, 1)
        else:
            rate = 0.0
        
        med_performance_data.append({
            'name': med.name,
            'frequency': med.frequency,
            'adherence_rate': rate,
            'total_doses': med.total_doses,
            'taken_doses': med.taken_doses
        })
    
    # Sort by adherence rate
    med_performance_data.sort(key=lambda x: x['adherence_rate'])
    
    # Get symptom trends (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    symptoms_by_day = db.session.query(
        func.date(Symptom.recorded_at).label('date'),
        func.count(Symptom.id).label('count'),
        func.avg(func.case([(Symptom.severity == 'severe', 3),
                           (Symptom.severity == 'moderate', 2),
                           (Symptom.severity == 'mild', 1)], else_=0)).label('avg_severity')
    ).filter(
        Symptom.user_id == user_id,
        Symptom.recorded_at >= week_ago
    ).group_by(func.date(Symptom.recorded_at))\
     .order_by('date').all()
    
    # Get risk factors
    risk_factors = []
    
    # Check for severe drug interactions
    severe_interactions = DrugInteraction.query.filter_by(
        user_id=user_id,
        severity='severe'
    ).count()
    
    if severe_interactions > 0:
        risk_factors.append({
            'type': 'interaction',
            'severity': 'high',
            'message': f'{severe_interactions} severe drug interactions detected',
            'icon': '⚠️'
        })
    
    # Check for contraindications
    contraindications = Contraindication.query.filter_by(
        user_id=user_id,
        severity='absolute'
    ).count()
    
    if contraindications > 0:
        risk_factors.append({
            'type': 'contraindication',
            'severity': 'high',
            'message': f'{contraindications} absolute contraindications found',
            'icon': '🚫'
        })
    
    # Check for abnormal vitals
    latest_vitals = VitalSigns.query.filter_by(user_id=user_id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .first()
    
    if latest_vitals:
        if latest_vitals.systolic_bp and latest_vitals.systolic_bp > 140:
            risk_factors.append({
                'type': 'bp',
                'severity': 'medium',
                'message': f'Elevated blood pressure: {latest_vitals.systolic_bp}/{latest_vitals.diastolic_bp}',
                'icon': '📈'
            })
        
        if latest_vitals.heart_rate and (latest_vitals.heart_rate > 100 or latest_vitals.heart_rate < 60):
            risk_factors.append({
                'type': 'hr',
                'severity': 'low',
                'message': f'Abnormal heart rate: {latest_vitals.heart_rate} BPM',
                'icon': '❤️'
            })
    
    # Generate comprehensive AI report
    context_data = {
        'adherence_rate': adherence_rate,
        'wellness_score': wellness_score.total_score if wellness_score else 'N/A',
        'risk_factors_count': len(risk_factors),
        'active_medications': len(med_performance_data),
        'symptom_trend': 'improving' if len(symptoms_by_day) > 1 and 
                         symptoms_by_day[-1].count < symptoms_by_day[0].count else 'stable'
    }
    
    ai_report = ai_service.generate_health_insights(context_data)
    
    # Get action items
    action_items = []
    
    # Check for low adherence medications
    low_adherence_meds = [m for m in med_performance_data if m['adherence_rate'] < 70]
    if low_adherence_meds:
        action_items.append({
            'icon': '💊',
            'title': 'Improve Medication Adherence',
            'description': f'{low_adherence_meds[0]["name"]} has {low_adherence_meds[0]["adherence_rate"]}% adherence',
            'priority': 'high',
            'url': '/medications'
        })
    
    # Check for upcoming follow-ups
    from app.models import MedicalEvaluation
    upcoming_followups = MedicalEvaluation.query.filter(
        MedicalEvaluation.user_id == user_id,
        MedicalEvaluation.follow_up_date >= datetime.utcnow().date(),
        MedicalEvaluation.follow_up_date <= datetime.utcnow().date() + timedelta(days=7)
    ).count()
    
    if upcoming_followups > 0:
        action_items.append({
            'icon': '📅',
            'title': 'Upcoming Follow-up',
            'description': f'{upcoming_followups} medical follow-up(s) in the next 7 days',
            'priority': 'medium',
            'url': '/health/evaluations'
        })
    
    # Check for severe symptoms
    severe_symptoms = Symptom.query.filter_by(
        user_id=user_id,
        severity='severe',
        status='active'
    ).count()
    
    if severe_symptoms > 0:
        action_items.append({
            'icon': '🤒',
            'title': 'Active Severe Symptoms',
            'description': f'{severe_symptoms} severe symptom(s) reported',
            'priority': 'high',
            'url': '/health/symptoms'
        })
    
    return render_template('insights/index.html',
                         adherence_rate=adherence_rate,
                         wellness_score=wellness_score,
                         ai_insights=ai_insights,
                         adherence_trends=adherence_trends,
                         medication_performance=med_performance_data,
                         symptoms_by_day=symptoms_by_day,
                         risk_factors=risk_factors,
                         ai_report=ai_report,
                         action_items=action_items)

# ============================================================================
# ADHERENCE ANALYTICS
# ============================================================================

@insights_bp.route('/adherence')
@login_required
def adherence_analytics():
    """Detailed adherence analytics"""
    form = InsightFilterForm()
    
    # Default date range: last 30 days
    days = int(request.args.get('days', 30))
    
    # Calculate adherence rate
    adherence_rate = Helper.calculate_adherence_rate(current_user.id, days)
    
    # Get daily adherence for chart
    daily_adherence = []
    for i in range(days - 1, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        
        doses = db.session.query(Dose).join(Prescription)\
            .filter(
                Prescription.user_id == current_user.id,
                db.func.date(Dose.scheduled_time) == date
            ).all()
        
        if doses:
            taken_doses = sum(1 for d in doses if d.status == 'taken')
            daily_rate = round((taken_doses / len(doses)) * 100, 1) if doses else 0
        else:
            daily_rate = None
        
        daily_adherence.append({
            'date': date.strftime('%Y-%m-%d'),
            'rate': daily_rate,
            'has_data': len(doses) > 0
        })
    
    # Get medication-specific adherence
    medication_adherence = db.session.query(
        Medication.id,
        Medication.name,
        func.count(Dose.id).label('total'),
        func.sum(func.case([(Dose.status == 'taken', 1)], else_=0)).label('taken')
    ).join(Prescription, Prescription.medication_id == Medication.id)\
     .join(Dose, Dose.prescription_id == Prescription.id)\
     .filter(
        Prescription.user_id == current_user.id,
        Dose.scheduled_time >= datetime.utcnow() - timedelta(days=days)
     ).group_by(Medication.id, Medication.name).all()
    
    med_adherence_data = []
    for med in medication_adherence:
        if med.total > 0:
            rate = round((med.taken / med.total) * 100, 1)
        else:
            rate = 0.0
        
        med_adherence_data.append({
            'id': med.id,
            'name': med.name,
            'adherence_rate': rate,
            'total_doses': med.total,
            'taken_doses': med.taken,
            'missed_doses': med.total - med.taken
        })
    
    # Sort by adherence rate (lowest first)
    med_adherence_data.sort(key=lambda x: x['adherence_rate'])
    
    # Get adherence by time of day
    adherence_by_hour = db.session.query(
        db.func.strftime('%H', Dose.scheduled_time).label('hour'),
        func.count(Dose.id).label('total'),
        func.sum(func.case([(Dose.status == 'taken', 1)], else_=0)).label('taken')
    ).join(Prescription)\
     .filter(
        Prescription.user_id == current_user.id,
        Dose.scheduled_time >= datetime.utcnow() - timedelta(days=days)
     ).group_by('hour')\
     .order_by('hour').all()
    
    hour_data = []
    for hour in range(24):
        hour_str = f'{hour:02d}'
        hour_record = next((h for h in adherence_by_hour if h.hour == hour_str), None)
        
        if hour_record and hour_record.total > 0:
            rate = round((hour_record.taken / hour_record.total) * 100, 1)
        else:
            rate = None
        
        hour_data.append({
            'hour': hour_str,
            'adherence_rate': rate,
            'total': hour_record.total if hour_record else 0,
            'taken': hour_record.taken if hour_record else 0
        })
    
    # Get best/worst days for adherence
    adherence_by_day = db.session.query(
        db.func.strftime('%w', Dose.scheduled_time).label('day_of_week'),
        db.func.count(Dose.id).label('total'),
        db.func.sum(db.case([(Dose.status == 'taken', 1)], else_=0)).label('taken')
    ).join(Prescription)\
     .filter(
        Prescription.user_id == current_user.id,
        Dose.scheduled_time >= datetime.utcnow() - timedelta(days=min(days, 90))  # Last 90 days max
     ).group_by('day_of_week')\
     .order_by('day_of_week').all()
    
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    day_data = []
    for i, day_name in enumerate(day_names):
        day_record = next((d for d in adherence_by_day if int(d.day_of_week) == i), None)
        
        if day_record and day_record.total > 0:
            rate = round((day_record.taken / day_record.total) * 100, 1)
        else:
            rate = None
        
        day_data.append({
            'day': day_name,
            'adherence_rate': rate,
            'total': day_record.total if day_record else 0,
            'taken': day_record.taken if day_record else 0
        })
    
    # Find best and worst days
    valid_days = [d for d in day_data if d['adherence_rate'] is not None]
    if valid_days:
        best_day = max(valid_days, key=lambda x: x['adherence_rate'])
        worst_day = min(valid_days, key=lambda x: x['adherence_rate'])
    else:
        best_day = worst_day = None
    
    return render_template('insights/adherence.html',
                         form=form,
                         days=days,
                         adherence_rate=adherence_rate,
                         daily_adherence=daily_adherence,
                         medication_adherence=med_adherence_data,
                         hour_data=hour_data,
                         day_data=day_data,
                         best_day=best_day,
                         worst_day=worst_day)

# ============================================================================
# HEALTH TRENDS
# ============================================================================

@insights_bp.route('/health-trends')
@login_required
def health_trends():
    """Health trends and patterns"""
    form = InsightFilterForm()
    
    days = int(request.args.get('days', 30))
    
    # Get vital trends
    vitals = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        VitalSigns.recorded_at >= datetime.utcnow() - timedelta(days=days)
    ).order_by(VitalSigns.recorded_at).all()
    
    # Prepare data for charts
    bp_dates = []
    bp_systolic = []
    bp_diastolic = []
    
    hr_dates = []
    hr_values = []
    
    temp_dates = []
    temp_values = []
    
    for vital in vitals:
        if vital.systolic_bp and vital.diastolic_bp:
            bp_dates.append(vital.recorded_at)
            bp_systolic.append(vital.systolic_bp)
            bp_diastolic.append(vital.diastolic_bp)
        
        if vital.heart_rate:
            hr_dates.append(vital.recorded_at)
            hr_values.append(vital.heart_rate)
        
        if vital.temperature:
            temp_dates.append(vital.recorded_at)
            temp_values.append(vital.temperature)
    
    # Get symptom trends
    symptoms = Symptom.query.filter(
        Symptom.user_id == current_user.id,
        Symptom.recorded_at >= datetime.utcnow() - timedelta(days=days)
    ).order_by(Symptom.recorded_at).all()
    
    # Group symptoms by day
    symptoms_by_day = {}
    for symptom in symptoms:
        date_str = symptom.recorded_at.date().isoformat()
        if date_str not in symptoms_by_day:
            symptoms_by_day[date_str] = {
                'count': 0,
                'severity_sum': 0,
                'symptoms': []
            }
        
        symptoms_by_day[date_str]['count'] += 1
        severity_value = {'mild': 1, 'moderate': 2, 'severe': 3}.get(symptom.severity, 0)
        symptoms_by_day[date_str]['severity_sum'] += severity_value
        symptoms_by_day[date_str]['symptoms'].append(symptom.name)
    
    # Convert to lists for chart
    symptom_dates = list(symptoms_by_day.keys())
    symptom_counts = [data['count'] for data in symptoms_by_day.values()]
    symptom_severity_avg = [
        round(data['severity_sum'] / data['count'], 2) if data['count'] > 0 else 0
        for data in symptoms_by_day.values()
    ]
    
    # Get mood trends
    moods = db.session.query(
        db.func.date(Mood.recorded_at).label('date'),
        db.func.avg(db.case([
            (Mood.mood_level == 'excellent', 5),
            (Mood.mood_level == 'good', 4),
            (Mood.mood_level == 'fair', 3),
            (Mood.mood_level == 'poor', 2),
            (Mood.mood_level == 'depressed', 1),
            (Mood.mood_level == 'anxious', 2),
            (Mood.mood_level == 'angry', 1)
        ], else_=3)).label('avg_mood'),
        db.func.avg(Mood.energy_level).label('avg_energy'),
        db.func.avg(Mood.stress_level).label('avg_stress')
    ).filter(
        Mood.user_id == current_user.id,
        Mood.recorded_at >= datetime.utcnow() - timedelta(days=days)
    ).group_by(db.func.date(Mood.recorded_at))\
     .order_by('date').all()
    
    mood_dates = [mood.date.strftime('%Y-%m-%d') for mood in moods]
    mood_values = [round(float(mood.avg_mood or 3), 2) for mood in moods]
    energy_values = [round(float(mood.avg_energy or 5), 2) for mood in moods]
    stress_values = [round(float(mood.avg_stress or 5), 2) for mood in moods]
    
    # Calculate correlations
    correlations = []
    
    if len(bp_systolic) > 5 and len(symptom_counts) > 5:
        # Simple correlation between BP and symptoms (example)
        min_len = min(len(bp_systolic), len(symptom_counts))
        if min_len > 5:
            bp_corr = np.corrcoef(bp_systolic[:min_len], symptom_counts[:min_len])[0, 1]
            if abs(bp_corr) > 0.5:
                correlations.append({
                    'type': 'BP and Symptoms',
                    'correlation': round(bp_corr, 2),
                    'interpretation': 'High blood pressure correlates with increased symptoms' if bp_corr > 0 else 'High blood pressure correlates with decreased symptoms'
                })
    
    return render_template('insights/health_trends.html',
                         form=form,
                         days=days,
                         bp_dates=bp_dates,
                         bp_systolic=bp_systolic,
                         bp_diastolic=bp_diastolic,
                         hr_dates=hr_dates,
                         hr_values=hr_values,
                         temp_dates=temp_dates,
                         temp_values=temp_values,
                         symptom_dates=symptom_dates,
                         symptom_counts=symptom_counts,
                         symptom_severity_avg=symptom_severity_avg,
                         mood_dates=mood_dates,
                         mood_values=mood_values,
                         energy_values=energy_values,
                         stress_values=stress_values,
                         correlations=correlations)

# ============================================================================
# MEDICATION ANALYTICS
# ============================================================================

@insights_bp.route('/medication-analytics')
@login_required
def medication_analytics():
    """Medication-specific analytics"""
    
    # Get all medications with prescriptions
    medications = Medication.query.join(Prescription)\
        .filter(
            Prescription.user_id == current_user.id,
            Prescription.status == 'active'
        ).all()
    
    medication_data = []
    
    for med in medications:
        # Get prescriptions for this medication
        prescriptions = Prescription.query.filter_by(
            medication_id=med.id,
            user_id=current_user.id,
            status='active'
        ).all()
        
        # Calculate adherence for this medication
        total_doses = 0
        taken_doses = 0
        
        for prescription in prescriptions:
            doses = Dose.query.filter_by(prescription_id=prescription.id).all()
            total_doses += len(doses)
            taken_doses += sum(1 for d in doses if d.status == 'taken')
        
        if total_doses > 0:
            adherence_rate = round((taken_doses / total_doses) * 100, 1)
        else:
            adherence_rate = 0.0
        
        # Get side effect reports
        side_effects = []
        for prescription in prescriptions:
            doses_with_effects = Dose.query.filter(
                Dose.prescription_id == prescription.id,
                Dose.side_effects.isnot(None)
            ).all()
            
            for dose in doses_with_effects:
                if dose.side_effects:
                    try:
                        effects = json.loads(dose.side_effects)
                        if isinstance(effects, dict):
                            side_effects.extend(effects.keys())
                    except:
                        pass
        
        # Count side effect frequency
        from collections import Counter
        side_effect_counts = Counter(side_effects)
        top_side_effects = side_effect_counts.most_common(3)
        
        # Get time taken patterns
        dose_times = db.session.query(
            db.func.strftime('%H:%M', Dose.actual_time).label('time'),
            db.func.count(Dose.id).label('count')
        ).join(Prescription)\
         .filter(
            Prescription.medication_id == med.id,
            Prescription.user_id == current_user.id,
            Dose.actual_time.isnot(None),
            Dose.status == 'taken'
         ).group_by('time')\
         .order_by(db.desc('count')).limit(3).all()
        
        medication_data.append({
            'id': med.id,
            'name': med.name,
            'strength': med.strength,
            'form': med.form,
            'adherence_rate': adherence_rate,
            'total_doses': total_doses,
            'taken_doses': taken_doses,
            'side_effects': top_side_effects,
            'common_times': dose_times,
            'prescriptions': prescriptions
        })
    
    # Sort by adherence rate
    medication_data.sort(key=lambda x: x['adherence_rate'])
    
    # Get drug interactions
    interactions = DrugInteraction.query.filter_by(user_id=current_user.id)\
        .order_by(DrugInteraction.severity.desc())\
        .all()
    
    # Get contraindications
    contraindications = Contraindication.query.filter_by(user_id=current_user.id)\
        .order_by(Contraindication.severity.desc())\
        .all()
    
    return render_template('insights/medication_analytics.html',
                         medications=medication_data,
                         interactions=interactions,
                         contraindications=contraindications)

# ============================================================================
# AI INSIGHTS & PREDICTIONS
# ============================================================================

@insights_bp.route('/ai-insights')
@login_required
def ai_insights():
    """AI-generated insights and predictions"""
    
    # Get stored AI insights
    insights = AIInsight.query.filter_by(user_id=current_user.id)\
        .filter(
            (AIInsight.expires_at.is_(None)) |
            (AIInsight.expires_at > datetime.utcnow())
        )\
        .order_by(AIInsight.priority.desc(), AIInsight.created_at.desc())\
        .all()
    
    # Generate new insights if needed
    if len(insights) < 3:
        # Gather data for AI analysis
        adherence_rate = Helper.calculate_adherence_rate(current_user.id, 30)
        
        latest_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
            .order_by(VitalSigns.recorded_at.desc())\
            .first()
        
        active_symptoms = Symptom.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).count()
        
        from app.models import Prescription
        active_medications = Prescription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).count()
        
        context_data = {
            'adherence_rate': adherence_rate,
            'vitals_summary': f"BP: {latest_vitals.systolic_bp if latest_vitals else 'N/A'}/{latest_vitals.diastolic_bp if latest_vitals else 'N/A'}, HR: {latest_vitals.heart_rate if latest_vitals else 'N/A'}",
            'symptoms_count': active_symptoms,
            'medication_count': active_medications,
            'user_data': 'analysis_requested'
        }
        
        # Generate new insights
        new_insights = ai_service.generate_health_insights(context_data)
        
        # Store new insights
        for insight in new_insights:
            ai_insight = AIInsight(
                user_id=current_user.id,
                insight_type=insight.get('insight_type', 'general'),
                insight_text=insight.get('insight_text', ''),
                confidence_score=insight.get('confidence_score', 75),
                is_actionable=insight.get('is_actionable', False),
                action_url=insight.get('action_url'),
                priority=insight.get('priority', 'medium')
            )
            
            db.session.add(ai_insight)
        
        db.session.commit()
        
        # Refresh insights list
        insights = AIInsight.query.filter_by(user_id=current_user.id)\
            .filter(
                (AIInsight.expires_at.is_(None)) |
                (AIInsight.expires_at > datetime.utcnow())
            )\
            .order_by(AIInsight.priority.desc(), AIInsight.created_at.desc())\
            .all()
    
    # Get prediction data
    predictions = []
    
    # Predict future adherence based on trends
    adherence_trends = AdherenceTrend.query.filter_by(user_id=current_user.id)\
        .order_by(AdherenceTrend.period_start.desc())\
        .limit(4).all()
    
    if len(adherence_trends) >= 2:
        recent_trend = adherence_trends[0].adherence_rate - adherence_trends[1].adherence_rate
        
        if recent_trend > 5:
            predictions.append({
                'type': 'adherence',
                'direction': 'improving',
                'confidence': 'high',
                'message': 'Your medication adherence is improving significantly'
            })
        elif recent_trend < -5:
            predictions.append({
                'type': 'adherence',
                'direction': 'declining',
                'confidence': 'medium',
                'message': 'Your medication adherence shows a declining trend'
            })
    
    # Predict potential issues
    from app.models import Dose
    missed_doses_recent = Dose.query.join(Prescription)\
        .filter(
            Prescription.user_id == current_user.id,
            Dose.status == 'missed',
            Dose.scheduled_time >= datetime.utcnow() - timedelta(days=7)
        ).count()
    
    if missed_doses_recent > 3:
        predictions.append({
            'type': 'risk',
            'direction': 'increasing',
            'confidence': 'high',
            'message': f'High rate of missed doses ({missed_doses_recent} in 7 days)'
        })
    
    return render_template('insights/ai_insights.html',
                         insights=insights,
                         predictions=predictions)

@insights_bp.route('/refresh-ai-insights', methods=['POST'])
@login_required
def refresh_ai_insights():
    """Manually refresh AI insights"""
    try:
        # Delete old insights
        AIInsight.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        flash('AI insights refreshed!', 'success')
    except Exception as e:
        flash(f'Error refreshing insights: {str(e)}', 'error')
    
    return redirect(url_for('insights.ai_insights'))

# ============================================================================
# EXPORT & REPORTING
# ============================================================================

@insights_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_data():
    """Export health data"""
    form = ExportDataForm()
    
    if form.validate_on_submit():
        export_format = form.export_format.data
        data_types = form.data_types.data
        date_range = form.date_range.data
        
        # Calculate date range
        if date_range == 'year':
            start_date = datetime.utcnow() - timedelta(days=365)
        elif date_range == 'month':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif date_range == 'custom' and form.start_date.data and form.end_date.data:
            start_date = form.start_date.data
            end_date = form.end_date.data
        else:
            start_date = None
            end_date = None
        
        # Generate report based on format
        if export_format == 'pdf':
            # For PDF, we'd typically use a library like ReportLab or WeasyPrint
            # For now, redirect to a printable version
            return redirect(url_for('insights.printable_report',
                                  data_types=data_types,
                                  start_date=start_date.isoformat() if start_date else '',
                                  end_date=end_date.isoformat() if end_date else ''))
        
        elif export_format == 'csv':
            # Generate CSV
            return generate_csv_export(data_types, start_date, end_date)
        
        elif export_format == 'json':
            # Generate JSON
            return generate_json_export(data_types, start_date, end_date)
    
    return render_template('insights/export.html', form=form)

def generate_csv_export(data_types, start_date, end_date):
    """Generate CSV export"""
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.writer(output)
    
    if data_types in ['all', 'medications']:
        writer.writerow(['=== MEDICATION DATA ==='])
        writer.writerow(['Medication', 'Strength', 'Form', 'Prescription Start', 'Status'])
        
        query = Medication.query.join(Prescription)\
            .filter(Prescription.user_id == current_user.id)
        
        if start_date:
            query = query.filter(Prescription.start_date >= start_date)
        if end_date:
            query = query.filter(Prescription.start_date <= end_date)
        
        medications = query.all()
        
        for med in medications:
            prescription = med.active_prescription
            if prescription:
                writer.writerow([
                    med.name,
                    med.strength,
                    med.form,
                    prescription.start_date.strftime('%Y-%m-%d') if prescription.start_date else '',
                    prescription.status
                ])
    
    # Add other data types similarly...
    
    output.seek(0)
    
    from flask import send_file
    from io import BytesIO
    
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'health_export_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    )

def generate_json_export(data_types, start_date, end_date):
    """Generate JSON export"""
    data = {}
    
    if data_types in ['all', 'vitals']:
        query = VitalSigns.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(VitalSigns.recorded_at >= start_date)
        if end_date:
            query = query.filter(VitalSigns.recorded_at <= end_date)
        
        vitals = query.all()
        data['vital_signs'] = [{
            'recorded_at': v.recorded_at.isoformat() if v.recorded_at else None,
            'systolic_bp': v.systolic_bp,
            'diastolic_bp': v.diastolic_bp,
            'heart_rate': v.heart_rate,
            'temperature': v.temperature
        } for v in vitals]
    
    # Add other data types similarly...
    
    from flask import jsonify, send_file
    from io import BytesIO
    import json
    
    json_data = json.dumps(data, indent=2, default=str)
    
    return send_file(
        BytesIO(json_data.encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'health_export_{datetime.utcnow().strftime("%Y%m%d")}.json'
    )

@insights_bp.route('/printable-report')
@login_required
def printable_report():
    """Printable health report"""
    # Get data for the report
    vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .limit(20).all()
    
    from app.models import Medication, Prescription
    medications = Medication.query.join(Prescription)\
        .filter(
            Prescription.user_id == current_user.id,
            Prescription.status == 'active'
        ).all()
    
    conditions = HealthCondition.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    allergies = Allergy.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    lab_tests = LabTest.query.filter_by(user_id=current_user.id)\
        .order_by(LabTest.test_date.desc())\
        .limit(10).all()
    
    # Calculate adherence
    adherence_rate = Helper.calculate_adherence_rate(current_user.id, 30)
    
    # Get wellness score
    wellness_score = WellnessScore.query.filter_by(user_id=current_user.id)\
        .order_by(WellnessScore.calculation_date.desc())\
        .first()
    
    return render_template('insights/printable_report.html',
                         vitals=vitals,
                         medications=medications,
                         conditions=conditions,
                         allergies=allergies,
                         lab_tests=lab_tests,
                         adherence_rate=adherence_rate,
                         wellness_score=wellness_score,
                         generated_date=datetime.utcnow())

# ============================================================================
# GOAL SETTING & PROGRESS
# ============================================================================

@insights_bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    """Goal setting and progress tracking"""
    form = GoalSettingForm()
    
    # This would typically connect to a Goals model
    # For now, show example goals
    
    example_goals = [
        {
            'type': 'adherence',
            'target': 95,
            'current': 88,
            'timeframe': 'monthly',
            'progress': 88/95*100,
            'status': 'in_progress'
        },
        {
            'type': 'vitals',
            'target': 'BP < 130/80',
            'current': '135/85',
            'timeframe': 'weekly',
            'progress': 75,
            'status': 'needs_improvement'
        },
        {
            'type': 'symptoms',
            'target': 'Reduce severe symptoms',
            'current': '2 severe symptoms',
            'timeframe': 'monthly',
            'progress': 60,
            'status': 'in_progress'
        }
    ]
    
    return render_template('insights/goals.html',
                         form=form,
                         goals=example_goals)

# ============================================================================
# API ENDPOINTS FOR CHARTS
# ============================================================================

@insights_bp.route('/api/adherence-trend')
@login_required
def api_adherence_trend():
    """API endpoint for adherence trend chart"""
    weeks = int(request.args.get('weeks', 8))
    
    # Calculate weekly adherence
    weekly_data = []
    for i in range(weeks):
        week_end = datetime.utcnow() - timedelta(weeks=i)
        week_start = week_end - timedelta(weeks=1)
        
        doses = Dose.query.join(Prescription)\
            .filter(
                Prescription.user_id == current_user.id,
                Dose.scheduled_time >= week_start,
                Dose.scheduled_time < week_end
            ).all()
        
        if doses:
            taken_doses = sum(1 for d in doses if d.status == 'taken')
            adherence_rate = round((taken_doses / len(doses)) * 100, 1)
        else:
            adherence_rate = None
        
        weekly_data.append({
            'week': week_start.strftime('%Y-%m-%d'),
            'adherence_rate': adherence_rate
        })
    
    # Reverse to show chronological order
    weekly_data.reverse()
    
    return jsonify(weekly_data)

@insights_bp.route('/api/wellness-timeline')
@login_required
def api_wellness_timeline():
    """API endpoint for wellness score timeline"""
    scores = WellnessScore.query.filter_by(user_id=current_user.id)\
        .order_by(WellnessScore.calculation_date)\
        .limit(30).all()
    
    data = {
        'dates': [score.calculation_date.strftime('%Y-%m-%d') for score in scores],
        'scores': [score.total_score for score in scores],
        'risk_levels': [score.risk_level for score in scores]
    }
    
    return jsonify(data)

# ============================================================================
# DASHBOARD WIDGETS (for AJAX loading)
# ============================================================================

@insights_bp.route('/widgets/adherence-summary')
@login_required
def widget_adherence_summary():
    """Widget: Adherence summary"""
    adherence_rate = Helper.calculate_adherence_rate(current_user.id, 7)
    
    # Compare with previous week
    previous_rate = Helper.calculate_adherence_rate(current_user.id, 14)  # 2 weeks ago
    
    if previous_rate > 0:
        trend = adherence_rate - previous_rate
        trend_direction = 'up' if trend > 0 else 'down' if trend < 0 else 'same'
        trend_percent = abs(round(trend, 1))
    else:
        trend_direction = 'same'
        trend_percent = 0
    
    return jsonify({
        'current_rate': round(adherence_rate, 1),
        'trend_direction': trend_direction,
        'trend_percent': trend_percent,
        'period': '7 days'
    })

@insights_bp.route('/widgets/health-alerts')
@login_required
def widget_health_alerts():
    """Widget: Health alerts"""
    alerts = []
    
    # Check for severe symptoms
    severe_symptoms = Symptom.query.filter_by(
        user_id=current_user.id,
        severity='severe',
        status='active'
    ).count()
    
    if severe_symptoms > 0:
        alerts.append({
            'type': 'symptom',
            'severity': 'high',
            'message': f'{severe_symptoms} severe symptom(s) active',
            'action': '/health/symptoms'
        })
    
    # Check for abnormal vitals
    latest_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.recorded_at.desc())\
        .first()
    
    if latest_vitals:
        if latest_vitals.systolic_bp and latest_vitals.systolic_bp > 140:
            alerts.append({
                'type': 'vitals',
                'severity': 'medium',
                'message': 'Elevated blood pressure',
                'action': '/health/vitals'
            })
        
        if latest_vitals.heart_rate and latest_vitals.heart_rate > 100:
            alerts.append({
                'type': 'vitals',
                'severity': 'low',
                'message': 'Elevated heart rate',
                'action': '/health/vitals'
            })
    
    # Check for drug interactions
    severe_interactions = DrugInteraction.query.filter_by(
        user_id=current_user.id,
        severity='severe'
    ).count()
    
    if severe_interactions > 0:
        alerts.append({
            'type': 'medication',
            'severity': 'high',
            'message': f'{severe_interactions} severe drug interaction(s)',
            'action': '/insights/medication-analytics'
        })
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts)
    })


insights_bp.route('/analyze', methods=['GET'])
@login_required
def analyze_insights():
    """Analyze user data and return insights"""
    analyzer = InsightAnalyzer()
    
    insights = {
        'interactions': analyzer.check_medication_interactions(current_user.id),
        'contraindications': analyzer.check_contraindications(current_user.id),
        'adherence': analyzer.analyze_adherence(current_user.id),
        'missed_doses': analyzer.identify_missed_doses(current_user.id),
        'vital_signs_trends': analyzer.check_vital_signs_trends(current_user.id),
        'refill_needs': analyzer.check_prescription_refills(current_user.id)
    }
    
    return jsonify({
        'success': True,
        'insights': insights,
        'generated_at': datetime.utcnow().isoformat()
    })

@insights_bp.route('/notify-me', methods=['POST'])
@login_required
def trigger_insight_notifications():
    """Manually trigger insight notifications"""
    result = InsightsNotificationService.check_and_create_insight_notifications(current_user.id)
    
    return jsonify({
        'success': True,
        'notifications_created': result,
        'message': f'Created {sum(result.values())} insight notification(s)'
    })

@insights_bp.route('/check-interactions', methods=['GET'])
@login_required
def check_interactions():
    """Specifically check for medication interactions"""
    analyzer = InsightAnalyzer()
    interactions = analyzer.check_medication_interactions(current_user.id)
    
    # Create notifications for critical interactions
    critical_count = 0
    for interaction in interactions:
        if interaction['severity'] in ['high', 'severe']:
            InsightsNotificationService.create_interaction_notification(
                user_id=current_user.id,
                medication_ids=interaction['medication_ids'],
                interaction_type=interaction['type'],
                severity=interaction['severity'],
                details=interaction['details']
            )
            critical_count += 1
    
    return jsonify({
        'interactions': interactions,
        'critical_alerts': critical_count,
        'has_critical_alerts': critical_count > 0
    })
@insights_bp.route('/analyze', methods=['GET'])
@login_required
def analyze_insights():
    """Analyze user data and return insights"""
    analyzer = InsightAnalyzer()
    
    insights = {
        'interactions': analyzer.check_medication_interactions(current_user.id),
        'contraindications': analyzer.check_contraindications(current_user.id),
        'adherence': analyzer.analyze_adherence(current_user.id),
        'missed_doses': analyzer.identify_missed_doses(current_user.id),
        'vital_signs_trends': analyzer.check_vital_signs_trends(current_user.id),
        'refill_needs': analyzer.check_prescription_refills(current_user.id)
    }
    
    return jsonify({
        'success': True,
        'insights': insights,
        'generated_at': datetime.utcnow().isoformat()
    })

@insights_bp.route('/notify-me', methods=['POST'])
@login_required
def trigger_insight_notifications():
    """Manually trigger insight notifications"""
    result = InsightsNotificationService.check_and_create_insight_notifications(current_user.id)
    
    return jsonify({
        'success': True,
        'notifications_created': result,
        'message': f'Created {sum(result.values())} insight notification(s)'
    })

@insights_bp.route('/check-interactions', methods=['GET'])
@login_required
def check_interactions():
    """Specifically check for medication interactions"""
    analyzer = InsightAnalyzer()
    interactions = analyzer.check_medication_interactions(current_user.id)
    
    # Create notifications for critical interactions
    critical_count = 0
    for interaction in interactions:
        if interaction['severity'] in ['high', 'severe']:
            InsightsNotificationService.create_interaction_notification(
                user_id=current_user.id,
                medication_ids=interaction['medication_ids'],
                interaction_type=interaction['type'],
                severity=interaction['severity'],
                details=interaction['details']
            )
            critical_count += 1
    
    return jsonify({
        'interactions': interactions,
        'critical_alerts': critical_count,
        'has_critical_alerts': critical_count > 0
    })