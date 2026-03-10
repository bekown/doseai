# models.py
"""Database models for the application
I will be using the following conventions:
    Table names in plural, model names in singular.
    Use db.Integer for primary keys.
    Use db.String with appropriate lengths for text fields.
    Use db.DateTime for timestamps.
    Set up relationships with db.relationship and foreign keys with db.ForeignKey."""

from datetime import datetime, time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Float, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

# Association tables
medication_conditions = db.Table('medication_conditions',
    Column('medication_id', Integer, ForeignKey('medications.id'), primary_key=True),
    Column('condition_id', Integer, ForeignKey('health_conditions.id'), primary_key=True)
)

medication_allergies = db.Table('medication_allergies',
    Column('medication_id', Integer, ForeignKey('medications.id'), primary_key=True),
    Column('allergy_id', Integer, ForeignKey('allergies.id'), primary_key=True)
)

class User(db.Model):
    """User authentication model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    profile = relationship('Profile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    medications = relationship('Medication', back_populates='user', cascade='all, delete-orphan')
    prescriptions = relationship('Prescription', back_populates='user', cascade='all, delete-orphan')
    emergency_contacts = relationship('EmergencyContact', back_populates='user', cascade='all, delete-orphan')
    notification_preferences = relationship('NotificationPreference', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()
    
    @validates('username')
    def validate_username(self, key, username):
        if len(username) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError('Username can only contain letters, numbers and underscores')
        return username.lower()

class Profile(db.Model):
    """User demographic and health profile"""
    __tablename__ = 'profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    
    # Address components (normalized)
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(50), default='US')
    
    # Health information
    gender = Column(String(20))
    date_of_birth = Column(Date)
    ethnicity = Column(String(50))
    occupation = Column(String(100))
    
    # Physical metrics
    height_cm = Column(Integer)
    weight_kg = Column(Float)
    blood_type = Column(String(5))  # A+, O-, etc.
    
    # Insurance information (encrypted in production)
    insurance_provider = Column(String(100))
    insurance_id = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='profile')
    health_conditions = relationship('HealthCondition', back_populates='user', cascade='all, delete-orphan')
    allergies = relationship('Allergy', back_populates='user', cascade='all, delete-orphan')
    
    @hybrid_property
    def age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @hybrid_property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None
    
    @validates('blood_type')
    def validate_blood_type(self, key, blood_type):
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_type and blood_type.upper() not in [bt.upper() for bt in valid_types]:
            raise ValueError('Invalid blood type')
        return blood_type.upper()

class HealthCondition(db.Model):
    """Known health conditions"""
    __tablename__ = 'health_conditions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20))  # chronic, acute
    icd10_code = Column(String(10))  # International Classification of Diseases
    diagnosis_date = Column(Date)
    severity = Column(String(20))  # mild, moderate, severe
    stage = Column(String(20))
    symptoms = Column(Text)
    treatment = Column(Text)
    prognosis = Column(Text)
    status = Column(String(20), default='active')  # active, resolved, controlled
    provider_name = Column(String(100))
    provider_contact = Column(String(100))
    
    # Relationships
    user = relationship('User', backref='conditions')
    medications = relationship('Medication', secondary=medication_conditions, back_populates='conditions')

class Allergy(db.Model):
    """Known allergies"""
    __tablename__ = 'allergies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    allergen_name = Column(String(100), nullable=False)
    type = Column(String(20))  # food, drug, environmental, insect, other
    reaction = Column(String(100))  # rash, anaphylaxis, etc.
    severity = Column(String(20))  # mild, moderate, severe
    onset_date = Column(Date)
    treatment = Column(Text)
    verification_status = Column(String(20), default='confirmed')  # confirmed, suspected
    status = Column(String(20), default='active')  # active, resolved
    
    # Relationships
    user = relationship('User', backref='allergies')
    medications = relationship('Medication', secondary=medication_allergies, back_populates='allergies')

class EmergencyContact(db.Model):
    """Emergency contact information"""
    __tablename__ = 'emergency_contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    contact_relationship = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    can_access_health_data = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    notes = Column(Text)
    
    user = relationship('User', back_populates='emergency_contacts')

class Pharmacy(db.Model):
    """Pharmacy information"""
    __tablename__ = 'pharmacies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    
    # Address
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state = Column(String(50))
    zip_code = Column(String(20))
    
    hours = Column(JSON)  # {'monday': '9am-5pm', ...}
    is_preferred = Column(Boolean, default=False)
    notes = Column(Text)

class HealthcareProvider(db.Model):
    """Healthcare provider information"""
    __tablename__ = 'healthcare_providers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100))
    type = Column(String(50))  # primary_care, specialist, therapist, etc.
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    clinic_name = Column(String(100))
    notes = Column(Text)
    is_primary = Column(Boolean, default=False)

class Medication(db.Model):
    """Medication information"""
    __tablename__ = 'medications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Basic information
    name = Column(String(100), nullable=False)
    generic_name = Column(String(100))
    brand_name = Column(String(100))
    strength = Column(String(50))  # 500mg, 20mg/5ml, etc.
    form = Column(String(50))  # tablet, capsule, liquid, injection, etc.
    ndc_code = Column(String(20))  # National Drug Code
    
    # Image and identification
    image_url = Column(String(255))
    color = Column(String(30))
    shape = Column(String(30))
    imprint = Column(String(50))
    
    # Classification
    drug_class = Column(String(100))
    schedule = Column(String(10))  # Controlled substance schedule
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='medications')
    prescriptions = relationship('Prescription', back_populates='medication', cascade='all, delete-orphan')
    inventory = relationship('MedicationInventory', back_populates='medication', cascade='all, delete-orphan')
    conditions = relationship('HealthCondition', secondary=medication_conditions, back_populates='medications')
    allergies = relationship('Allergy', secondary=medication_allergies, back_populates='medications')
    
    @property
    def active_prescription(self):
        """Get the active prescription if any"""
        for prescription in self.prescriptions:
            if prescription.status == 'active':
                return prescription
        return None
    
    @property
    def next_dose_time(self):
        """Get the next scheduled dose time"""
        if not self.active_prescription:
            return None
        
        last_dose = Dose.query.filter_by(
            prescription_id=self.active_prescription.id
        ).order_by(Dose.scheduled_time.desc()).first()
        
        if last_dose and last_dose.next_dose_time:
            return last_dose.next_dose_time
        return None

class Prescription(db.Model):
    """Prescription details"""
    __tablename__ = 'prescriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    medication_id = Column(Integer, ForeignKey('medications.id', ondelete='CASCADE'), nullable=False)
    provider_id = Column(Integer, ForeignKey('healthcare_providers.id'))
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    
    # Prescription details
    prescription_number = Column(String(50))
    dosage = Column(String(100), nullable=False)  # Take 1 tablet
    frequency = Column(Integer, nullable=False)  # times per day
    frequency_unit = Column(String(20), default='day')  # day, week, month
    route = Column(String(50))  # oral, topical, injection, etc.
    
    # Duration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(Date)
    refills_allowed = Column(Integer, default=0)
    refills_remaining = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default='active')  # active, completed, discontinued
    status_reason = Column(Text)
    
    # Additional info
    instructions = Column(Text)
    indication = Column(String(200))  # reason for taking
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='prescriptions')
    medication = relationship('Medication', back_populates='prescriptions')
    provider = relationship('HealthcareProvider')
    pharmacy = relationship('Pharmacy')
    doses = relationship('Dose', back_populates='prescription', cascade='all, delete-orphan')
    refills = relationship('MedicationRefill', back_populates='prescription', cascade='all, delete-orphan')
    
    @property
    def is_active(self):
        return self.status == 'active' and (
            not self.end_date or self.end_date >= datetime.now().date()
        )
    
    @property
    def adherence_rate(self):
        """Calculate adherence rate for this prescription"""
        total_doses = Dose.query.filter_by(prescription_id=self.id).count()
        taken_doses = Dose.query.filter_by(
            prescription_id=self.id,
            status='taken'
        ).count()
        
        if total_doses > 0:
            return round((taken_doses / total_doses) * 100, 1)
        return 0.0

class MedicationSchedule(db.Model):
    """Flexible medication schedule"""
    __tablename__ = 'medication_schedules'
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False)
    
    # Schedule configuration
    schedule_type = Column(String(20), default='daily')  # daily, weekly, specific_days
    days_of_week = Column(JSON)  # ['monday', 'wednesday', 'friday']
    times = Column(JSON, nullable=False)  # ['08:00', '20:00']
    
    # Advanced scheduling
    interval_hours = Column(Integer)  # For "every X hours" schedules
    take_with_food = Column(Boolean, default=False)
    take_before_bed = Column(Boolean, default=False)
    
    # Timezone support for travel
    timezone = Column(String(50), default='UTC')
    
    # Relationships
    prescription = relationship('Prescription', backref='schedules')

class Dose(db.Model):
    """Individual dose tracking"""
    __tablename__ = 'doses'
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('medication_schedules.id'))
    
    # Timing
    scheduled_time = Column(DateTime, nullable=False)
    actual_time = Column(DateTime)
    next_dose_time = Column(DateTime)
    
    # Status
    status = Column(String(20), default='scheduled')  # scheduled, taken, skipped, missed, snoozed
    taken_late = Column(Boolean, default=False)
    snooze_count = Column(Integer, default=0)
    
    # Notes
    notes = Column(Text)
    side_effects = Column(JSON)  # {'nausea': 'mild', 'headache': 'moderate'}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prescription = relationship('Prescription', back_populates='doses')
    schedule = relationship('MedicationSchedule')
    
    @property
    def is_overdue(self):
        if self.status == 'scheduled' and self.scheduled_time < datetime.utcnow():
            return True
        return False
    
    @property
    def minutes_late(self):
        if self.status == 'taken' and self.actual_time and self.scheduled_time:
            delay = (self.actual_time - self.scheduled_time).total_seconds() / 60
            return max(0, delay)
        return 0

class MedicationInventory(db.Model):
    """Medication inventory tracking"""
    __tablename__ = 'medication_inventory'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    medication_id = Column(Integer, ForeignKey('medications.id', ondelete='CASCADE'), nullable=False)
    
    # Inventory details
    quantity = Column(Integer, nullable=False)
    unit = Column(String(20), nullable=False)  # tablets, ml, mg, etc.
    strength_per_unit = Column(String(50))  # 500mg per tablet
    
    # Batch information
    lot_number = Column(String(50))
    expiration_date = Column(Date)
    manufacturer = Column(String(100))
    
    # Storage
    location = Column(String(100))  # bathroom cabinet, fridge, etc.
    storage_instructions = Column(Text)
    
    # Tracking
    initial_quantity = Column(Integer)
    low_stock_threshold = Column(Integer, default=7)  # days supply
    is_expiring_soon = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    medication = relationship('Medication', back_populates='inventory')
    
    @property
    def days_supply(self):
        """Calculate days of medication remaining"""
        if not self.quantity or not self.prescription_daily_doses:
            return None
        
        daily_doses = self.prescription_daily_doses
        return round(self.quantity / daily_doses, 1)
    
    @property
    def prescription_daily_doses(self):
        """Get average daily doses from active prescriptions"""
        active_prescriptions = Prescription.query.filter_by(
            medication_id=self.medication_id,
            status='active'
        ).all()
        
        total_daily_doses = 0
        for prescription in active_prescriptions:
            total_daily_doses += prescription.frequency
        
        return total_daily_doses

class MedicationRefill(db.Model):
    """Medication refill history"""
    __tablename__ = 'medication_refills'
    
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    
    refill_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    days_supply = Column(Integer)
    cost = Column(Float)
    insurance_covered = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    prescription = relationship('Prescription', back_populates='refills')
    pharmacy = relationship('Pharmacy')

class MedicalEvaluation(db.Model):
    """Medical evaluation/visit records"""
    __tablename__ = 'medical_evaluations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider_id = Column(Integer, ForeignKey('healthcare_providers.id'))
    
    evaluation_date = Column(DateTime, nullable=False)
    type = Column(String(30))  # routine, emergency, follow_up, annual_checkup
    chief_complaint = Column(String(200))
    diagnosis = Column(Text)
    summary = Column(Text)
    recommendations = Column(Text)
    follow_up_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    provider = relationship('HealthcareProvider')
    vitals = relationship('VitalSigns', back_populates='evaluation', cascade='all, delete-orphan')
    lab_tests = relationship('LabTest', back_populates='evaluation', cascade='all, delete-orphan')
    imaging_studies = relationship('ImagingStudy', back_populates='evaluation', cascade='all, delete-orphan')

class VitalSigns(db.Model):
    """Vital signs recording"""
    __tablename__ = 'vital_signs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    evaluation_id = Column(Integer, ForeignKey('medical_evaluations.id'))
    
    # Vital measurements
    systolic_bp = Column(Integer)  # mmHg
    diastolic_bp = Column(Integer)  # mmHg
    heart_rate = Column(Integer)  # bpm
    respiratory_rate = Column(Integer)  # breaths/min
    temperature = Column(Float)  # Celsius
    oxygen_saturation = Column(Integer)  # SpO2 percentage
    pain_level = Column(Integer)  # 0-10 scale
    
    # Additional measurements
    height_cm = Column(Float)
    weight_kg = Column(Float)
    blood_glucose = Column(Float)  # mg/dL
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    user = relationship('User')
    evaluation = relationship('MedicalEvaluation', back_populates='vitals')
    
    @property
    def blood_pressure(self):
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp}"
        return None
    
    @property
    def bp_category(self):
        """Categorize blood pressure according to AHA guidelines"""
        if not self.systolic_bp or not self.diastolic_bp:
            return None
        
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "normal"
        elif 120 <= self.systolic_bp <= 129 and self.diastolic_bp < 80:
            return "elevated"
        elif (130 <= self.systolic_bp <= 139) or (80 <= self.diastolic_bp <= 89):
            return "stage1"
        elif self.systolic_bp >= 140 or self.diastolic_bp >= 90:
            return "stage2"
        elif self.systolic_bp > 180 or self.diastolic_bp > 120:
            return "crisis"
        return None

class Symptom(db.Model):
    """Symptom tracking"""
    __tablename__ = 'symptoms'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    evaluation_id = Column(Integer, ForeignKey('medical_evaluations.id'))
    
    name = Column(String(100), nullable=False)
    severity = Column(String(20))  # mild, moderate, severe
    duration_minutes = Column(Integer)
    frequency = Column(String(20))  # constant, intermittent
    triggers = Column(Text)
    alleviating_factors = Column(Text)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    status = Column(String(20), default='active')  # active, resolved
    
    # Body location for symptom
    body_location = Column(String(100))
    
    notes = Column(Text)
    
    # Relationships
    user = relationship('User')
    evaluation = relationship('MedicalEvaluation')

class Mood(db.Model):
    """Mood tracking"""
    __tablename__ = 'moods'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    mood_level = Column(String(20), nullable=False)  # excellent, good, fair, poor
    energy_level = Column(Integer)  # 1-10 scale
    stress_level = Column(Integer)  # 1-10 scale
    sleep_hours = Column(Float)
    sleep_quality = Column(String(20))
    
    notes = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User')

class DailyCheckin(db.Model):
    """Daily health check-in"""
    __tablename__ = 'daily_checkins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    checkin_date = Column(Date, nullable=False)
    
    # Completion status
    vitals_completed = Column(Boolean, default=False)
    symptoms_completed = Column(Boolean, default=False)
    mood_completed = Column(Boolean, default=False)
    medications_taken = Column(JSON)  # List of medication IDs taken today
    
    # Overall assessment
    overall_wellness = Column(Integer)  # 1-10 scale
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'checkin_date'),)
    
    user = relationship('User')

class LabTest(db.Model):
    """Laboratory test results"""
    __tablename__ = 'lab_tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    evaluation_id = Column(Integer, ForeignKey('medical_evaluations.id'))
    
    test_name = Column(String(100), nullable=False)
    test_code = Column(String(20))  # LOINC code
    result_value = Column(String(50))
    result_unit = Column(String(20))
    reference_range = Column(String(50))
    result_status = Column(String(20))  # normal, high, low, abnormal
    
    test_date = Column(Date)
    result_date = Column(Date)
    lab_name = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    user = relationship('User')
    evaluation = relationship('MedicalEvaluation', back_populates='lab_tests')

class ImagingStudy(db.Model):
    """Imaging study results"""
    __tablename__ = 'imaging_studies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    evaluation_id = Column(Integer, ForeignKey('medical_evaluations.id'))
    
    study_type = Column(String(100), nullable=False)  # X-ray, MRI, CT, Ultrasound
    body_part = Column(String(100))
    findings = Column(Text)
    impression = Column(Text)
    radiologist = Column(String(100))
    
    study_date = Column(Date)
    report_date = Column(Date)
    
    # File attachments (in production, store in cloud storage)
    report_url = Column(String(255))
    image_urls = Column(JSON)  # List of image URLs
    
    notes = Column(Text)
    
    # Relationships
    user = relationship('User')
    evaluation = relationship('MedicalEvaluation', back_populates='imaging_studies')

class DrugInteraction(db.Model):
    """Drug-drug interactions"""
    __tablename__ = 'drug_interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    medication1_id = Column(Integer, ForeignKey('medications.id'), nullable=False)
    medication2_id = Column(Integer, ForeignKey('medications.id'), nullable=False)
    
    interaction_name = Column(String(200))
    severity = Column(String(20))  # major, moderate, minor
    mechanism = Column(Text)
    effect = Column(Text)
    recommendation = Column(Text)
    
    # Source of interaction data
    source = Column(String(50))  # ai_generated, database, manual
    confidence_score = Column(Float)  # 0-1
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    
    __table_args__ = (
        db.CheckConstraint('medication1_id < medication2_id', name='check_medication_order'),
        db.UniqueConstraint('medication1_id', 'medication2_id', name='unique_interaction_pair')
    )
    
    # Relationships
    user = relationship('User')
    medication1 = relationship('Medication', foreign_keys=[medication1_id])
    medication2 = relationship('Medication', foreign_keys=[medication2_id])

class Contraindication(db.Model):
    """Medication contraindications"""
    __tablename__ = 'contraindications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    medication_id = Column(Integer, ForeignKey('medications.id'), nullable=False)
    
    contraindication_type = Column(String(50))  # allergy, condition, age, pregnancy
    related_entity_id = Column(Integer)  # ID of allergy, condition, etc.
    related_entity_type = Column(String(50))
    
    severity = Column(String(20))  # absolute, relative
    description = Column(Text)
    recommendation = Column(Text)
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    
    user = relationship('User')
    medication = relationship('Medication')

class Notification(db.Model):
    """System notifications"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Notification details
    type = Column(String(50), nullable=False)  # medication_reminder, health_alert, refill, interaction
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20))  # low, medium, high, urgent
    
    # Associated entities
    medication_id = Column(Integer, ForeignKey('medications.id'))
    prescription_id = Column(Integer, ForeignKey('prescriptions.id'))
    
    # Status
    is_read = Column(Boolean, default=False)
    is_action_required = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)
    
    # Action information
    action_url = Column(String(255))
    action_label = Column(String(50))
    
    # Scheduling
    scheduled_time = Column(DateTime)
    sent_time = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Additional data
    data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    medication = relationship('Medication')
    prescription = relationship('Prescription')
    
    @property
    def is_expired(self):
        if self.expires_at:
            return self.expires_at < datetime.utcnow()
        return False

class NotificationPreference(db.Model):
    """User notification preferences"""
    __tablename__ = 'notification_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Channel preferences
    enable_push = Column(Boolean, default=True)
    enable_email = Column(Boolean, default=True)
    enable_sms = Column(Boolean, default=False)
    
    # Type preferences
    enable_medication_reminders = Column(Boolean, default=True)
    enable_refill_reminders = Column(Boolean, default=True)
    enable_health_alerts = Column(Boolean, default=True)
    enable_interaction_alerts = Column(Boolean, default=True)
    enable_appointment_reminders = Column(Boolean, default=True)
    
    # Timing preferences
    reminder_lead_minutes = Column(Integer, default=30)
    snooze_duration_minutes = Column(Integer, default=10)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=True)
    quiet_start = Column(String(5), default='22:00')  # 10 PM
    quiet_end = Column(String(5), default='07:00')   # 7 AM
    
    # Advanced settings
    smart_reminders = Column(Boolean, default=True)  # AI-optimized timing
    allow_weekend_notifications = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='notification_preferences')

class AIInsight(db.Model):
    """AI-generated health insights"""
    __tablename__ = 'ai_insights'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    insight_type = Column(String(50), nullable=False)  # adherence, symptom, medication, general
    insight_text = Column(Text, nullable=False)
    
    # Metadata
    confidence_score = Column(Float)  # 0-100
    source_data = Column(JSON)  # Data used to generate insight
    is_actionable = Column(Boolean, default=False)
    action_url = Column(String(255))
    action_label = Column(String(100))
    
    # Status
    is_dismissed = Column(Boolean, default=False)
    priority = Column(String(20))  # low, medium, high
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    user = relationship('User')

class AdherenceTrend(db.Model):
    """Medication adherence trends"""
    __tablename__ = 'adherence_trends'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    medication_id = Column(Integer, ForeignKey('medications.id'))
    
    period_type = Column(String(20), default='weekly')  # daily, weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Metrics
    doses_scheduled = Column(Integer, default=0)
    doses_taken = Column(Integer, default=0)
    doses_missed = Column(Integer, default=0)
    doses_skipped = Column(Integer, default=0)
    adherence_rate = Column(Float)  # percentage
    
    # Analysis
    trend_direction = Column(String(20))  # improving, declining, stable
    trend_strength = Column(Float)  # -1 to 1
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'medication_id', 'period_start', name='unique_adherence_period'),
    )
    
    user = relationship('User')
    medication = relationship('Medication')

class WellnessScore(db.Model):
    """Comprehensive wellness scoring"""
    __tablename__ = 'wellness_scores'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    calculation_date = Column(Date, nullable=False)
    total_score = Column(Integer, nullable=False)  # 0-100
    
    # Component scores
    adherence_score = Column(Integer)  # 0-40
    vital_signs_score = Column(Integer)  # 0-30
    symptoms_score = Column(Integer)  # 0-20
    lifestyle_score = Column(Integer)  # 0-10
    
    # Risk assessment
    risk_level = Column(String(20))  # low, medium, high
    risk_factors = Column(JSON)
    
    # Recommendations
    recommendations = Column(JSON)  # List of recommendations
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'calculation_date', name='unique_daily_score'),
    )
    
    user = relationship('User')

class AppEngagement(db.Model):
    """App usage analytics"""
    __tablename__ = 'app_engagement'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    event_type = Column(String(50), nullable=False)  # app_open, screen_view, medication_log, etc.
    screen_name = Column(String(100))
    action = Column(String(100))
    duration_seconds = Column(Integer)
    
    # Device info
    device_type = Column(String(50))
    app_version = Column(String(20))
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User')

class TravelSchedule(db.Model):
    """Travel mode adjustments"""
    __tablename__ = 'travel_schedules'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    destination = Column(String(100))
    destination_timezone = Column(String(50), nullable=False)
    
    travel_start = Column(DateTime, nullable=False)
    travel_end = Column(DateTime)
    
    # Original and adjusted schedules
    original_schedules = Column(JSON)  # Store original medication schedules
    adjusted_schedules = Column(JSON)  # Timezone-adjusted schedules
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User')