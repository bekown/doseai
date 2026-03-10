# app/utils/insight_analyzer.py

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import and_, or_
from app.models import db, User, Medication, Prescription, Dose, UserHealthProfile, DailyCheckin

class InsightAnalyzer:
    """Analyzes user data to generate health and medication insights"""
    
    @staticmethod
    def check_medication_interactions(user_id: int) -> List[Dict[str, Any]]:
        """Check for potential medication interactions"""
        interactions = []
        
        # Get user's active medications
        active_prescriptions = Prescription.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        if len(active_prescriptions) < 2:
            return interactions
        
        # Get medication IDs
        medication_ids = [p.medication_id for p in active_prescriptions]
        medications = Medication.query.filter(
            Medication.id.in_(medication_ids)
        ).all()
        
        # Simple interaction logic (you should replace with a proper drug database)
        medication_names = [med.name.lower() for med in medications]
        
        # Example interaction rules
        interaction_rules = [
            {
                'medications': ['warfarin', 'aspirin', 'ibuprofen'],
                'type': 'bleeding_risk',
                'severity': 'high',
                'message': 'Increased bleeding risk when combined'
            },
            {
                'medications': ['simvastatin', 'clarithromycin'],
                'type': 'muscle_risk',
                'severity': 'high',
                'message': 'Increased risk of muscle damage'
            },
            {
                'medications': ['lisinopril', 'spironolactone'],
                'type': 'kidney_risk',
                'severity': 'medium',
                'message': 'Increased potassium levels risk'
            }
        ]
        
        # Check for interactions
        for rule in interaction_rules:
            matching_meds = [med for med in medications 
                           if any(keyword in med.name.lower() 
                                  for keyword in rule['medications'])]
            
            if len(matching_meds) >= 2:
                interactions.append({
                    'type': rule['type'],
                    'severity': rule['severity'],
                    'medication_ids': [med.id for med in matching_meds],
                    'medication_names': [med.name for med in matching_meds],
                    'details': {
                        'message': rule['message'],
                        'risk': rule['severity']
                    }
                })
        
        return interactions
    
    @staticmethod
    def check_contraindications(user_id: int) -> List[Dict[str, Any]]:
        """Check for contraindications based on user health profile"""
        contraindications = []
        
        # Get user health profile
        health_profile = UserHealthProfile.query.filter_by(user_id=user_id).first()
        if not health_profile:
            return contraindications
        
        # Get active prescriptions
        prescriptions = Prescription.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        # Example contraindication checks
        for prescription in prescriptions:
            medication = prescription.medication
            
            # Check based on conditions
            if health_profile.has_liver_disease and 'atorvastatin' in medication.name.lower():
                contraindications.append({
                    'medication_id': medication.id,
                    'medication_name': medication.name,
                    'condition': 'liver disease',
                    'severity': 'high',
                    'details': {
                        'message': f'{medication.name} may not be suitable for patients with liver conditions',
                        'recommendation': 'Consult your doctor'
                    }
                })
            
            # Check based on allergies
            if health_profile.allergies and 'penicillin' in medication.name.lower():
                if 'penicillin' in health_profile.allergies.lower():
                    contraindications.append({
                        'medication_id': medication.id,
                        'medication_name': medication.name,
                        'condition': 'penicillin allergy',
                        'severity': 'high',
                        'details': {
                            'message': f'Allergic reaction risk with {medication.name}',
                            'recommendation': 'Consider alternative medication'
                        }
                    })
        
        return contraindications
    
    @staticmethod
    def analyze_adherence(user_id: int, days: int = 7) -> Dict[str, Any]:
        """Analyze medication adherence"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get doses in the time period
        doses = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.scheduled_time.between(start_date, end_date)
        ).all()
        
        total_doses = len(doses)
        if total_doses == 0:
            return {'adherence_rate': 100, 'missed_doses': 0, 'taken_doses': 0}
        
        taken_doses = sum(1 for dose in doses if dose.status == 'taken')
        missed_doses = sum(1 for dose in doses if dose.status == 'missed')
        
        adherence_rate = (taken_doses / total_doses) * 100 if total_doses > 0 else 0
        
        return {
            'adherence_rate': round(adherence_rate, 1),
            'missed_doses': missed_doses,
            'taken_doses': taken_doses,
            'total_doses': total_doses,
            'period_days': days
        }
    
    @staticmethod
    def identify_missed_doses(user_id: int, hours_threshold: int = 24) -> List[Dict[str, Any]]:
        """Identify recently missed doses"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)
        
        missed_doses = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Dose.status == 'missed',
            Dose.scheduled_time >= cutoff_time
        ).order_by(Dose.scheduled_time.desc()).all()
        
        result = []
        for dose in missed_doses:
            result.append({
                'dose_id': dose.id,
                'medication_name': dose.prescription.medication.name,
                'scheduled_time': dose.scheduled_time.isoformat(),
                'hours_ago': round((datetime.utcnow() - dose.scheduled_time).seconds / 3600, 1),
                'prescription_id': dose.prescription_id
            })
        
        return result
    
    @staticmethod
    def check_vital_signs_trends(user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Analyze vital signs trends from check-ins"""
        insights = []
        
        checkins = DailyCheckin.query.filter_by(
            user_id=user_id
        ).filter(
            DailyCheckin.checkin_date >= datetime.utcnow().date() - timedelta(days=days)
        ).order_by(DailyCheckin.checkin_date.asc()).all()
        
        if len(checkins) < 5:
            return insights
        
        # Analyze blood pressure trends
        bp_readings = [(c.blood_pressure_systolic, c.blood_pressure_diastolic) 
                      for c in checkins if c.blood_pressure_systolic]
        
        if len(bp_readings) >= 3:
            recent_systolic = [bp[0] for bp in bp_readings[-3:]]
            avg_recent = sum(recent_systolic) / len(recent_systolic)
            
            if avg_recent > 140:
                insights.append({
                    'type': 'high_bp_trend',
                    'severity': 'medium',
                    'title': 'Elevated Blood Pressure',
                    'message': 'Your recent blood pressure readings are consistently high',
                    'data': {
                        'average_systolic': round(avg_recent, 1),
                        'readings_count': len(bp_readings)
                    }
                })
        
        return insights
    
    @staticmethod
    def check_prescription_refills(user_id: int) -> List[Dict[str, Any]]:
        """Check for upcoming prescription refills"""
        insights = []
        today = datetime.utcnow().date()
        
        prescriptions = Prescription.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        for prescription in prescriptions:
            if prescription.refill_date and prescription.refill_date <= today + timedelta(days=3):
                days_until = (prescription.refill_date - today).days
                
                insights.append({
                    'type': 'refill_needed',
                    'severity': 'medium',
                    'title': 'Prescription Refill Needed',
                    'message': f'{prescription.medication.name} needs refill',
                    'data': {
                        'prescription_id': prescription.id,
                        'medication_name': prescription.medication.name,
                        'refill_date': prescription.refill_date.isoformat(),
                        'days_until': days_until,
                        'urgent': days_until <= 1
                    }
                })
        
        return insights