# app/medications/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, FloatField, SelectField, DateField,
    DateTimeField, TimeField, TextAreaField, BooleanField, SubmitField,
    FieldList, FormField, MultipleFileField, DecimalField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from wtforms.widgets import TextInput
from datetime import datetime, time
import re

# Custom validators
class TimeFormat:
    def __init__(self, message=None):
        if not message:
            message = 'Time must be in HH:MM format'
        self.message = message
    
    def __call__(self, form, field):
        if field.data:
            try:
                datetime.strptime(field.data, '%H:%M')
            except ValueError:
                raise ValidationError(self.message)

class DosageValidator:
    def __call__(self, form, field):
        if field.data:
            # Validate common dosage formats
            patterns = [
                r'^\d+(\.\d+)?\s*(mg|mcg|g|ml|mL|IU|units?)$',
                r'^\d+\s*x\s*\d+(\.\d+)?\s*(mg|mcg|g|ml)$',
                r'^\d+(\.\d+)?%$',
                r'^\d+\s*tablet(s)?$',
                r'^\d+\s*capsule(s)?$',
                r'^\d+\s*puff(s)?$',
                r'^\d+\s*drop(s)?$'
            ]
            if not any(re.match(pattern, field.data, re.IGNORECASE) for pattern in patterns):
                raise ValidationError(
                    'Invalid dosage format. Examples: 500mg, 2 tablets, 1x50mg'
                )

class MedicationForm(FlaskForm):
    """Form for adding/editing medications"""
    
    # Basic information
    name = StringField('Medication Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    
    generic_name = StringField('Generic Name', validators=[
        Optional(),
        Length(max=100)
    ])
    
    brand_name = StringField('Brand Name', validators=[
        Optional(),
        Length(max=100)
    ])
    
    strength = StringField('Strength', validators=[
        DataRequired(),
        Length(max=50)
    ])
    
    form = SelectField('Form', choices=[
        ('', 'Select Form'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('liquid', 'Liquid/Solution'),
        ('injection', 'Injection'),
        ('inhaler', 'Inhaler'),
        ('cream', 'Cream/Ointment'),
        ('patch', 'Patch'),
        ('suppository', 'Suppository'),
        ('drops', 'Eye/Ear Drops'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_form = StringField('Other Form', validators=[Optional(), Length(max=50)])
    
    # Classification
    drug_class = StringField('Drug Class', validators=[
        Optional(),
        Length(max=100)
    ])
    
    schedule = SelectField('Schedule', choices=[
        ('', 'Not Controlled'),
        ('I', 'Schedule I'),
        ('II', 'Schedule II'),
        ('III', 'Schedule III'),
        ('IV', 'Schedule IV'),
        ('V', 'Schedule V')
    ], validators=[Optional()])
    
    # Identification
    ndc_code = StringField('NDC Code', validators=[
        Optional(),
        Length(max=20)
    ])
    
    color = StringField('Color', validators=[
        Optional(),
        Length(max=30)
    ])
    
    shape = StringField('Shape', validators=[
        Optional(),
        Length(max=30)
    ])
    
    imprint = StringField('Imprint', validators=[
        Optional(),
        Length(max=50)
    ])
    
    # Image
    image_url = StringField('Image URL', validators=[Optional()])
    
    # Additional info
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Save Medication')
    
    def validate(self, extra_validators=None):
        # Call parent validation
        if not super().validate(extra_validators):
            return False
        
        # Custom validation for 'other' form
        if self.form.data == 'other' and not self.other_form.data:
            self.other_form.errors.append('Please specify the form')
            return False
        
        return True

class PrescriptionForm(FlaskForm):
    """Form for adding/editing prescriptions"""
    
    # Medication selection (for existing medications)
    medication_id = SelectField('Medication', coerce=int, validators=[DataRequired()])
    
    # Provider information
    provider_name = StringField('Prescribing Provider', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    provider_contact = StringField('Provider Contact', validators=[
        Optional(),
        Length(max=100)
    ])
    
    # Pharmacy information
    pharmacy_name = StringField('Pharmacy', validators=[
        Optional(),
        Length(max=100)
    ])
    
    pharmacy_phone = StringField('Pharmacy Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    
    # Prescription details
    prescription_number = StringField('Rx Number', validators=[
        Optional(),
        Length(max=50)
    ])
    
    dosage = StringField('Dosage', validators=[
        DataRequired(),
        Length(max=100),
        DosageValidator()
    ])
    
    frequency = IntegerField('Times per Day', validators=[
        DataRequired(),
        NumberRange(min=1, max=24, message='Frequency must be between 1 and 24 times per day')
    ])
    
    route = SelectField('Route', choices=[
        ('', 'Select Route'),
        ('oral', 'Oral'),
        ('topical', 'Topical'),
        ('injection', 'Injection'),
        ('inhalation', 'Inhalation'),
        ('sublingual', 'Sublingual'),
        ('rectal', 'Rectal'),
        ('vaginal', 'Vaginal'),
        ('ophthalmic', 'Ophthalmic'),
        ('otic', 'Otic')
    ], validators=[DataRequired()])
    
    # Duration
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[Optional()])
    
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    indefinite = BooleanField('Indefinite/No End Date')
    
    # Refills
    refills_allowed = IntegerField('Refills Allowed', default=0, validators=[
        NumberRange(min=0, max=12)
    ])
    
    # Additional info
    instructions = TextAreaField('Instructions', validators=[
        Optional(),
        Length(max=500)
    ])
    
    indication = StringField('Reason/Indication', validators=[
        Optional(),
        Length(max=200)
    ])
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Save Prescription')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate end date if not indefinite
        if not self.indefinite.data and not self.end_date.data:
            self.end_date.errors.append('End date is required unless indefinite')
            return False
        
        # Validate end date is after start date
        if self.end_date.data and self.start_date.data:
            if self.end_date.data < self.start_date.data:
                self.end_date.errors.append('End date must be after start date')
                return False
        
        return True

class MedicationScheduleForm(FlaskForm):
    """Form for medication scheduling"""
    
    schedule_type = SelectField('Schedule Type', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('specific_days', 'Specific Days'),
        ('interval', 'Every X Hours')
    ], default='daily', validators=[DataRequired()])
    
    # For daily schedules
    times = StringField('Times (comma-separated)', validators=[
        DataRequired()
    ], description='Example: 08:00,20:00 or 09:00')
    
    # For weekly/specific days
    days_of_week = SelectField('Days of Week', choices=[
        ('all', 'Every Day'),
        ('weekdays', 'Weekdays Only'),
        ('weekends', 'Weekends Only'),
        ('specific', 'Specific Days')
    ], default='all')
    
    monday = BooleanField('Mon')
    tuesday = BooleanField('Tue')
    wednesday = BooleanField('Wed')
    thursday = BooleanField('Thu')
    friday = BooleanField('Fri')
    saturday = BooleanField('Sat')
    sunday = BooleanField('Sun')
    
    # For interval schedules
    interval_hours = IntegerField('Every X Hours', validators=[
        Optional(),
        NumberRange(min=1, max=24)
    ])
    
    # Advanced options
    take_with_food = BooleanField('Take with Food')
    take_before_bed = BooleanField('Take Before Bed')
    timezone = StringField('Timezone', default='UTC')
    
    submit = SubmitField('Save Schedule')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate time format
        if self.times.data:
            time_list = [t.strip() for t in self.times.data.split(',')]
            for t in time_list:
                try:
                    datetime.strptime(t, '%H:%M')
                except ValueError:
                    self.times.errors.append(f'Invalid time format: {t}. Use HH:MM format.')
                    return False
        
        # Validate at least one day is selected for specific days
        if self.days_of_week.data == 'specific':
            days_selected = any([
                self.monday.data, self.tuesday.data, self.wednesday.data,
                self.thursday.data, self.friday.data, self.saturday.data,
                self.sunday.data
            ])
            if not days_selected:
                self.monday.errors.append('Select at least one day')
                return False
        
        return True

class DoseForm(FlaskForm):
    """Form for logging individual doses"""
    
    prescription_id = SelectField('Medication', coerce=int, validators=[DataRequired()])
    
    # Timing
    scheduled_time = DateTimeField('Scheduled Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    actual_time = DateTimeField('Actual Time Taken', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Status
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('taken', 'Taken'),
        ('skipped', 'Skipped'),
        ('missed', 'Missed')
    ], default='taken', validators=[DataRequired()])
    
    # Side effects
    side_effects = TextAreaField('Side Effects', validators=[Optional(), Length(max=500)])
    
    nausea = SelectField('Nausea', choices=[
        ('none', 'None'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='none')
    
    headache = SelectField('Headache', choices=[
        ('none', 'None'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='none')
    
    dizziness = SelectField('Dizziness', choices=[
        ('none', 'None'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='none')
    
    fatigue = SelectField('Fatigue', choices=[
        ('none', 'None'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='none')
    
    # Notes
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Log Dose')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate actual time is not in the future
        if self.actual_time.data and self.actual_time.data > datetime.utcnow():
            self.actual_time.errors.append('Actual time cannot be in the future')
            return False
        
        return True

class MedicationInventoryForm(FlaskForm):
    """Form for managing medication inventory"""
    
    medication_id = SelectField('Medication', coerce=int, validators=[DataRequired()])
    
    quantity = IntegerField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=1, message='Quantity must be at least 1')
    ])
    
    unit = SelectField('Unit', choices=[
        ('tablets', 'Tablets'),
        ('capsules', 'Capsules'),
        ('ml', 'mL'),
        ('mg', 'mg'),
        ('g', 'grams'),
        ('puffs', 'Puffs'),
        ('drops', 'Drops'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_unit = StringField('Other Unit', validators=[Optional()])
    
    strength_per_unit = StringField('Strength per Unit', validators=[
        Optional(),
        Length(max=50)
    ])
    
    # Batch information
    lot_number = StringField('Lot Number', validators=[Optional(), Length(max=50)])
    expiration_date = DateField('Expiration Date', format='%Y-%m-%d', validators=[Optional()])
    manufacturer = StringField('Manufacturer', validators=[Optional(), Length(max=100)])
    
    # Storage
    location = StringField('Storage Location', validators=[Optional(), Length(max=100)])
    storage_instructions = TextAreaField('Storage Instructions', validators=[Optional()])
    
    # Thresholds
    low_stock_threshold = IntegerField('Low Stock Alert (days supply)', default=7, validators=[
        NumberRange(min=1, max=90)
    ])
    
    submit = SubmitField('Save Inventory')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate expiration date is not in the past
        if self.expiration_date.data and self.expiration_date.data < datetime.now().date():
            self.expiration_date.errors.append('Expiration date cannot be in the past')
            return False
        
        return True

class RefillForm(FlaskForm):
    """Form for logging medication refills"""
    
    prescription_id = SelectField('Prescription', coerce=int, validators=[DataRequired()])
    pharmacy_id = SelectField('Pharmacy', coerce=int, validators=[Optional()])
    
    refill_date = DateField('Refill Date', format='%Y-%m-%d', validators=[DataRequired()])
    quantity = IntegerField('Quantity Dispensed', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    
    days_supply = IntegerField('Days Supply', validators=[
        Optional(),
        NumberRange(min=1)
    ])
    
    cost = DecimalField('Cost', validators=[Optional()])
    insurance_covered = BooleanField('Insurance Covered', default=True)
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Log Refill')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate refill date is not in the future
        if self.refill_date.data > datetime.now().date():
            self.refill_date.errors.append('Refill date cannot be in the future')
            return False
        
        return True

class QuickDoseForm(FlaskForm):
    """Simplified form for quick dose logging"""
    
    medication_id = SelectField('Medication', coerce=int, validators=[DataRequired()])
    taken_now = BooleanField('Taken Now', default=True)
    custom_time = DateTimeField('Custom Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Quick side effect checkboxes
    side_effects = TextAreaField('Any side effects?', validators=[Optional()])
    
    submit = SubmitField('Log Dose')

class SearchMedicationForm(FlaskForm):
    """Form for searching medications"""
    
    query = StringField('Search', validators=[DataRequired()])
    search_type = SelectField('Search By', choices=[
        ('name', 'Name'),
        ('generic', 'Generic Name'),
        ('class', 'Drug Class'),
        ('all', 'All Fields')
    ], default='name')
    
    submit = SubmitField('Search')

class BulkDoseForm(FlaskForm):
    """Form for logging multiple doses at once"""
    
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Dynamic field for each medication
    class MedicationDoseForm(FlaskForm):
        medication_id = IntegerField(widget=TextInput(), validators=[Optional()])
        taken = BooleanField('Taken')
        time = TimeField('Time', validators=[Optional()])
        notes = StringField('Notes', validators=[Optional()])
    
    medications = FieldList(FormField(MedicationDoseForm), min_entries=1)
    
    submit = SubmitField('Save All Doses')