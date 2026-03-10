# app/medications/services.py

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models import db, Medication, Prescription, Dose, MedicationSchedule, MedicationInventory
from app.utils.cache_service import CacheService

class MedicationService:
    """Service for medication-related operations"""
    
    @staticmethod
    def create_medication(user_id: int, **kwargs) -> Medication:
        """Create a new medication"""
        medication = Medication(user_id=user_id, **kwargs)
        db.session.add(medication)
        db.session.commit()
        
        # Clear cache
        CacheService.clear_user_cache(user_id)
        
        return medication
    
    @staticmethod
    def create_prescription(medication_id: int, **kwargs) -> Prescription:
        """Create a new prescription"""
        prescription = Prescription(medication_id=medication_id, **kwargs)
        db.session.add(prescription)
        db.session.commit()
        
        return prescription
    
    @staticmethod
    def generate_schedule(prescription_id: int):
        """Generate dose schedule for a prescription"""
        prescription = Prescription.query.get_or_404(prescription_id)
        
        # Create schedule template
        schedule = MedicationSchedule(
            prescription_id=prescription_id,
            times=['08:00', '20:00'] if prescription.frequency == 2 else ['08:00'],
            schedule_type='daily'
        )
        db.session.add(schedule)
        
        # Generate initial doses
        start_date = prescription.start_date
        end_date = prescription.end_date or start_date + timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            for time_str in schedule.times:
                scheduled_time = datetime.combine(current_date.date(), 
                                                datetime.strptime(time_str, '%H:%M').time())
                
                dose = Dose(
                    prescription_id=prescription_id,
                    schedule_id=schedule.id,
                    scheduled_time=scheduled_time,
                    status='scheduled'
                )
                db.session.add(dose)
            
            current_date += timedelta(days=1)
        
        db.session.commit()
    
    @staticmethod
    def calculate_next_dose(dose: Dose) -> datetime:
        """Calculate next dose time based on prescription frequency"""
        prescription = dose.prescription
        
        if prescription.frequency == 1:
            return dose.scheduled_time + timedelta(days=1)
        elif prescription.frequency == 2:
            return dose.scheduled_time + timedelta(hours=12)
        elif prescription.frequency == 3:
            return dose.scheduled_time + timedelta(hours=8)
        elif prescription.frequency == 4:
            return dose.scheduled_time + timedelta(hours=6)
        elif prescription.frequency == 5:
            return dose.scheduled_time + timedelta(hours=4)
        elif prescription.frequency == 6:
            return dose.scheduled_time + timedelta(hours=2)
        else:
            return dose.scheduled_time + timedelta(days=1)
    
    @staticmethod
    def update_inventory(user_id: int, medication_id: int, quantity: int, **kwargs):
        """Update medication inventory"""
        inventory = MedicationInventory.query.filter_by(
            user_id=user_id,
            medication_id=medication_id
        ).first()
        
        if inventory:
            inventory.quantity = quantity
            inventory.updated_at = datetime.utcnow()
        else:
            inventory = MedicationInventory(
                user_id=user_id,
                medication_id=medication_id,
                quantity=quantity,
                **kwargs
            )
            db.session.add(inventory)
        
        db.session.commit()
        
        # Check for low stock
        if inventory.days_supply and inventory.days_supply <= 7:
            from app.utils.notification_service import NotificationService
            NotificationService.create_notification(
                user_id=user_id,
                title='⚠️ Low Medication Stock',
                message=f'{inventory.medication.name} is running low ({inventory.days_supply} days left)',
                notification_type='low_stock',
                medication_id=medication_id,
                priority='medium'
            )
    
    @staticmethod
    def get_medication_timeline(user_id: int, medication_id: int, days: int = 30):
        """Get medication timeline with doses"""
        from app.models import Dose, Prescription
        
        doses = Dose.query.join(Prescription).filter(
            Prescription.user_id == user_id,
            Prescription.medication_id == medication_id,
            Dose.scheduled_time >= datetime.utcnow() - timedelta(days=days)
        ).order_by(Dose.scheduled_time.desc()).all()
        
        timeline = []
        for dose in doses:
            timeline.append({
                'date': dose.scheduled_time.date().isoformat(),
                'time': dose.scheduled_time.time().strftime('%H:%M'),
                'status': dose.status,
                'taken_late': dose.taken_late,
                'snooze_count': dose.snooze_count
            })
        
        return timeline