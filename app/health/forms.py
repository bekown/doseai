# app/health/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, FloatField, SelectField, DateField,
    DateTimeField, TextAreaField, BooleanField, SubmitField,
    FieldList, FormField, FileField, MultipleFileField, DecimalField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from datetime import datetime
import re

class VitalSignsForm(FlaskForm):
    """Form for recording vital signs"""
    
    # Blood Pressure
    systolic_bp = IntegerField('Systolic (top number)', validators=[
        Optional(),
        NumberRange(min=50, max=250, message='Systolic must be between 50-250')
    ])
    
    diastolic_bp = IntegerField('Diastolic (bottom number)', validators=[
        Optional(),
        NumberRange(min=30, max=150, message='Diastolic must be between 30-150')
    ])
    
    # Heart and Respiratory
    heart_rate = IntegerField('Heart Rate (BPM)', validators=[
        Optional(),
        NumberRange(min=30, max=250, message='Heart rate must be between 30-250')
    ])
    
    respiratory_rate = IntegerField('Respiratory Rate', validators=[
        Optional(),
        NumberRange(min=8, max=50, message='Respiratory rate must be between 8-50')
    ])
    
    # Temperature
    temperature = FloatField('Temperature (°C)', validators=[
        Optional(),
        NumberRange(min=35, max=42, message='Temperature must be between 35-42°C')
    ])
    
    # Oxygen and Glucose
    oxygen_saturation = IntegerField('Oxygen Saturation (%)', validators=[
        Optional(),
        NumberRange(min=70, max=100, message='Oxygen saturation must be between 70-100%')
    ])
    
    blood_glucose = FloatField('Blood Glucose (mg/dL)', validators=[
        Optional(),
        NumberRange(min=20, max=600, message='Blood glucose must be between 20-600 mg/dL')
    ])
    
    # Pain and Weight
    pain_level = IntegerField('Pain Level (0-10)', validators=[
        Optional(),
        NumberRange(min=0, max=10, message='Pain level must be between 0-10')
    ])
    
    weight_kg = FloatField('Weight (kg)', validators=[
        Optional(),
        NumberRange(min=20, max=300, message='Weight must be between 20-300 kg')
    ])
    
    height_cm = FloatField('Height (cm)', validators=[
        Optional(),
        NumberRange(min=100, max=250, message='Height must be between 100-250 cm')
    ])
    
    # Timing
    recorded_at = DateTimeField('Recorded At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Save Vitals')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate blood pressure: diastolic should be less than systolic
        if self.systolic_bp.data and self.diastolic_bp.data:
            if self.diastolic_bp.data >= self.systolic_bp.data:
                self.diastolic_bp.errors.append('Diastolic must be lower than systolic')
                return False
        
        return True

class SymptomForm(FlaskForm):
    """Form for recording symptoms"""
    
    name = StringField('Symptom', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    severity = SelectField('Severity', choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='mild', validators=[DataRequired()])
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        Optional(),
        NumberRange(min=1)
    ])
    
    duration_hours = IntegerField('Duration (hours)', validators=[
        Optional(),
        NumberRange(min=1)
    ])
    
    frequency = SelectField('Frequency', choices=[
        ('constant', 'Constant'),
        ('intermittent', 'Intermittent'),
        ('occasional', 'Occasional')
    ], default='intermittent')
    
    body_location = StringField('Location', validators=[Optional(), Length(max=100)])
    
    triggers = TextAreaField('Triggers', validators=[Optional()])
    alleviating_factors = TextAreaField('What helps?', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Save Symptom')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Calculate total duration
        total_minutes = 0
        if self.duration_minutes.data:
            total_minutes += self.duration_minutes.data
        if self.duration_hours.data:
            total_minutes += self.duration_hours.data * 60
        
        if total_minutes <= 0:
            self.duration_minutes.errors.append('Please specify duration')
            return False
        
        return True

class MoodForm(FlaskForm):
    """Form for recording mood"""
    
    mood_level = SelectField('Mood', choices=[
        ('excellent', '😊 Excellent'),
        ('good', '🙂 Good'),
        ('fair', '😐 Fair'),
        ('poor', '😔 Poor'),
        ('depressed', '😞 Depressed'),
        ('anxious', '😰 Anxious'),
        ('angry', '😠 Angry')
    ], validators=[DataRequired()])
    
    energy_level = IntegerField('Energy Level (1-10)', validators=[
        Optional(),
        NumberRange(min=1, max=10)
    ])
    
    stress_level = IntegerField('Stress Level (1-10)', validators=[
        Optional(),
        NumberRange(min=1, max=10)
    ])
    
    sleep_hours = FloatField('Sleep Hours', validators=[
        Optional(),
        NumberRange(min=0, max=24)
    ])
    
    sleep_quality = SelectField('Sleep Quality', choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('restless', 'Restless')
    ])
    
    notes = TextAreaField('What affected your mood today?', validators=[Optional()])
    
    submit = SubmitField('Save Mood')

class DailyCheckinForm(FlaskForm):
    """Form for daily health check-in"""
    
    # Overall wellness
    overall_wellness = IntegerField('Overall Wellness (1-10)', validators=[
        DataRequired(),
        NumberRange(min=1, max=10)
    ])
    
    # Medications taken today
    class MedicationTakenForm(FlaskForm):
        medication_id = IntegerField(validators=[Optional()])
        taken = BooleanField('Taken')
        time = StringField('Time', validators=[Optional()])
    
    medications = FieldList(FormField(MedicationTakenForm), min_entries=1)
    
    # Daily goals
    water_intake = IntegerField('Water Glasses (8oz)', validators=[
        Optional(),
        NumberRange(min=0, max=20)
    ])
    
    exercise_minutes = IntegerField('Exercise (minutes)', validators=[
        Optional(),
        NumberRange(min=0, max=300)
    ])
    
    meals_eaten = IntegerField('Meals Eaten', validators=[
        Optional(),
        NumberRange(min=0, max=10)
    ])
    
    # Notes
    daily_notes = TextAreaField('Daily Notes', validators=[Optional()])
    
    submit = SubmitField('Complete Check-in')

class MedicalEvaluationForm(FlaskForm):
    """Form for medical evaluations/visits"""
    
    evaluation_date = DateField('Date of Visit', format='%Y-%m-%d', validators=[DataRequired()])
    
    evaluation_type = SelectField('Type of Visit', choices=[
        ('routine', 'Routine Check-up'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('specialist', 'Specialist'),
        ('urgent_care', 'Urgent Care'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_type = StringField('Other Type', validators=[Optional()])
    
    provider_name = StringField('Provider Name', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    clinic_name = StringField('Clinic/Hospital', validators=[Optional(), Length(max=100)])
    
    chief_complaint = StringField('Chief Complaint/Reason for Visit', validators=[
        DataRequired(),
        Length(max=200)
    ])
    
    diagnosis = TextAreaField('Diagnosis', validators=[Optional()])
    
    summary = TextAreaField('Visit Summary', validators=[Optional()])
    
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    
    follow_up_date = DateField('Follow-up Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Attachments
    documents = TextAreaField('Documents/Reports', validators=[Optional()])
    
    submit = SubmitField('Save Evaluation')
# Custom validator for lab values
class LabValueValidator:
    def __call__(self, form, field):
        if field.data:
            # Allow numeric values, text, or common lab formats
            value = str(field.data)
            
            # Check for common patterns
            patterns = [
                r'^\d+(\.\d+)?$',  # Simple numbers
                r'^\d+(\.\d+)?\s*[a-zA-Z/%]+$',  # Numbers with units
                r'^[<>]\s*\d+(\.\d+)?$',  # Less than/greater than
                r'^positive$', r'^negative$', r'^trace$',  # Common text results
                r'^[a-zA-Z\s]+$'  # Text results
            ]
            
            if not any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns):
                raise ValidationError(
                    'Invalid lab value format. Examples: 120, 7.5 mg/dL, <0.5, Positive'
                )

# Continue with existing forms, then add new ones...

class LabTestForm(FlaskForm):
    """Form for recording lab test results"""
    
    test_name = StringField('Test Name', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    test_category = SelectField('Test Category', choices=[
        ('', 'Select Category'),
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('hormone', 'Hormone Test'),
        ('lipid', 'Lipid Panel'),
        ('metabolic', 'Metabolic Panel'),
        ('cbc', 'Complete Blood Count'),
        ('liver', 'Liver Function'),
        ('kidney', 'Kidney Function'),
        ('thyroid', 'Thyroid Function'),
        ('vitamin', 'Vitamin Level'),
        ('glucose', 'Glucose/HbA1c'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # LOINC code (optional but recommended)
    loinc_code = StringField('LOINC Code', validators=[
        Optional(),
        Length(max=20)
    ])
    
    result_value = StringField('Result Value', validators=[
        DataRequired(),
        LabValueValidator()
    ])
    
    result_unit = StringField('Unit', validators=[
        Optional(),
        Length(max=20)
    ])
    
    reference_range = StringField('Normal Range', validators=[
        Optional(),
        Length(max=50)
    ], description='Example: 65-99 mg/dL or <5.7%')
    
    result_status = SelectField('Result Status', choices=[
        ('normal', 'Normal'),
        ('high', 'High'),
        ('low', 'Low'),
        ('abnormal', 'Abnormal'),
        ('critical', 'Critical')
    ], default='normal')
    
    # Timing
    test_date = DateField('Test Date', format='%Y-%m-%d', validators=[DataRequired()])
    collection_time = TimeField('Collection Time', validators=[Optional()])
    result_date = DateField('Result Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Lab information
    lab_name = StringField('Laboratory', validators=[
        Optional(),
        Length(max=100)
    ])
    
    ordering_provider = StringField('Ordering Provider', validators=[
        Optional(),
        Length(max=100)
    ])
    
    # Additional information
    notes = TextAreaField('Notes', validators=[Optional()])
    
    # File attachment
    report_file = FileField('Upload Report', validators=[Optional()])
    report_url = StringField('Report URL', validators=[Optional()])
    
    submit = SubmitField('Save Lab Result')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate result date is not before test date
        if self.result_date.data and self.test_date.data:
            if self.result_date.data < self.test_date.data:
                self.result_date.errors.append('Result date cannot be before test date')
                return False
        
        # Validate test date is not in the future
        if self.test_date.data > datetime.now().date():
            self.test_date.errors.append('Test date cannot be in the future')
            return False
        
        return True

class ImagingStudyForm(FlaskForm):
    """Form for recording imaging study results"""
    
    study_type = SelectField('Study Type', choices=[
        ('', 'Select Study Type'),
        ('xray', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('mammogram', 'Mammogram'),
        ('bone_scan', 'Bone Scan'),
        ('pet', 'PET Scan'),
        ('angiography', 'Angiography'),
        ('echo', 'Echocardiogram'),
        ('ekg', 'EKG/ECG'),
        ('eeg', 'EEG'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_type = StringField('Other Type', validators=[Optional(), Length(max=50)])
    
    body_part = StringField('Body Part/Area', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    # Study details
    contrast_used = BooleanField('Contrast Used')
    radiation_dose = StringField('Radiation Dose', validators=[Optional()])
    
    # Timing
    study_date = DateField('Study Date', format='%Y-%m-%d', validators=[DataRequired()])
    report_date = DateField('Report Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Professional information
    radiologist = StringField('Radiologist', validators=[
        Optional(),
        Length(max=100)
    ])
    
    facility_name = StringField('Facility', validators=[
        Optional(),
        Length(max=100)
    ])
    
    # Results
    findings = TextAreaField('Findings', validators=[DataRequired()])
    impression = TextAreaField('Impression/Conclusion', validators=[Optional()])
    
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    
    # Status tracking
    follow_up_required = BooleanField('Follow-up Required')
    follow_up_date = DateField('Follow-up Date', format='%Y-%m-%d', validators=[Optional()])
    
    # File attachments
    report_file = FileField('Upload Report (PDF)', validators=[Optional()])
    image_files = MultipleFileField('Upload Images', validators=[Optional()])
    
    report_url = StringField('Report URL', validators=[Optional()])
    image_urls = TextAreaField('Image URLs (one per line)', validators=[Optional()])
    
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    
    submit = SubmitField('Save Imaging Study')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate other type is specified if 'other' is selected
        if self.study_type.data == 'other' and not self.other_type.data:
            self.other_type.errors.append('Please specify the study type')
            return False
        
        # Validate study date is not in the future
        if self.study_date.data > datetime.now().date():
            self.study_date.errors.append('Study date cannot be in the future')
            return False
        
        # Validate report date is not before study date
        if self.report_date.data and self.study_date.data:
            if self.report_date.data < self.study_date.data:
                self.report_date.errors.append('Report date cannot be before study date')
                return False
        
        # Validate follow-up date is after study date
        if self.follow_up_date.data and self.study_date.data:
            if self.follow_up_date.data < self.study_date.data:
                self.follow_up_date.errors.append('Follow-up date must be after study date')
                return False
        
        return True

class ComprehensiveEvaluationForm(FlaskForm):
    """Form for comprehensive medical evaluation with labs and imaging"""
    
    # Basic evaluation info (from existing MedicalEvaluationForm)
    evaluation_date = DateField('Date of Visit', format='%Y-%m-%d', validators=[DataRequired()])
    
    evaluation_type = SelectField('Type of Visit', choices=[
        ('routine', 'Routine Check-up'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('specialist', 'Specialist'),
        ('urgent_care', 'Urgent Care'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_type = StringField('Other Type', validators=[Optional()])
    
    provider_name = StringField('Provider Name', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    clinic_name = StringField('Clinic/Hospital', validators=[Optional(), Length(max=100)])
    
    chief_complaint = StringField('Chief Complaint/Reason for Visit', validators=[
        DataRequired(),
        Length(max=200)
    ])
    
    diagnosis = TextAreaField('Diagnosis', validators=[Optional()])
    summary = TextAreaField('Visit Summary', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    follow_up_date = DateField('Follow-up Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Vitals section
    class VitalsSubForm(FlaskForm):
        systolic_bp = IntegerField('BP Systolic', validators=[Optional()])
        diastolic_bp = IntegerField('BP Diastolic', validators=[Optional()])
        heart_rate = IntegerField('Heart Rate', validators=[Optional()])
        temperature = FloatField('Temperature', validators=[Optional()])
        oxygen_saturation = IntegerField('O2 Sat', validators=[Optional()])
    
    vitals = FormField(VitalsSubForm)
    
    # Lab tests (dynamic list)
    class LabTestSubForm(FlaskForm):
        test_name = StringField('Test', validators=[Optional()])
        result_value = StringField('Result', validators=[Optional()])
        result_unit = StringField('Unit', validators=[Optional()])
        status = SelectField('Status', choices=[
            ('', '--'),
            ('normal', 'Normal'),
            ('abnormal', 'Abnormal')
        ], default='')
    
    lab_tests = FieldList(FormField(LabTestSubForm), min_entries=0, max_entries=10)
    
    add_lab_test = SubmitField('+ Add Lab Test')
    
    # Imaging studies (dynamic list)
    class ImagingSubForm(FlaskForm):
        study_type = StringField('Study', validators=[Optional()])
        body_part = StringField('Area', validators=[Optional()])
        findings = StringField('Findings', validators=[Optional()])
    
    imaging_studies = FieldList(FormField(ImagingSubForm), min_entries=0, max_entries=5)
    
    add_imaging = SubmitField('+ Add Imaging')
    
    # Prescriptions from this visit
    new_prescriptions = TextAreaField('New Prescriptions', validators=[Optional()])
    
    # Documents
    documents = TextAreaField('Documents/Reports', validators=[Optional()])
    
    submit = SubmitField('Save Complete Evaluation')

class LabTestSearchForm(FlaskForm):
    """Form for searching/filtering lab tests"""
    
    test_name = StringField('Test Name', validators=[Optional()])
    
    category = SelectField('Category', choices=[
        ('', 'All Categories'),
        ('blood', 'Blood Tests'),
        ('urine', 'Urine Tests'),
        ('hormone', 'Hormone Tests'),
        ('lipid', 'Lipid Panel'),
        ('metabolic', 'Metabolic Panel'),
        ('cbc', 'Complete Blood Count')
    ], default='')
    
    date_range = SelectField('Date Range', choices=[
        ('all', 'All Time'),
        ('year', 'Past Year'),
        ('6months', 'Past 6 Months'),
        ('3months', 'Past 3 Months'),
        ('month', 'Past Month'),
        ('custom', 'Custom Range')
    ], default='year')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    result_status = SelectField('Result Status', choices=[
        ('', 'All Results'),
        ('normal', 'Normal Only'),
        ('abnormal', 'Abnormal Only'),
        ('critical', 'Critical Only')
    ], default='')
    
    sort_by = SelectField('Sort By', choices=[
        ('date_desc', 'Date (Newest First)'),
        ('date_asc', 'Date (Oldest First)'),
        ('name', 'Test Name'),
        ('category', 'Category')
    ], default='date_desc')
    
    submit = SubmitField('Search Lab Tests')

class ImagingSearchForm(FlaskForm):
    """Form for searching/filtering imaging studies"""
    
    study_type = SelectField('Study Type', choices=[
        ('', 'All Types'),
        ('xray', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('mammogram', 'Mammogram')
    ], default='')
    
    body_part = StringField('Body Part', validators=[Optional()])
    
    date_range = SelectField('Date Range', choices=[
        ('all', 'All Time'),
        ('year', 'Past Year'),
        ('6months', 'Past 6 Months'),
        ('3months', 'Past 3 Months')
    ], default='year')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    has_follow_up = SelectField('Follow-up Status', choices=[
        ('', 'All'),
        ('required', 'Follow-up Required'),
        ('completed', 'Follow-up Completed'),
        ('none', 'No Follow-up')
    ], default='')
    
    sort_by = SelectField('Sort By', choices=[
        ('date_desc', 'Date (Newest First)'),
        ('date_asc', 'Date (Oldest First)'),
        ('type', 'Study Type')
    ], default='date_desc')
    
    submit = SubmitField('Search Imaging Studies')

class LabTrendForm(FlaskForm):
    """Form for viewing lab trends over time"""
    
    test_name = StringField('Test Name', validators=[DataRequired()])
    
    time_period = SelectField('Time Period', choices=[
        ('3months', '3 Months'),
        ('6months', '6 Months'),
        ('year', '1 Year'),
        ('2years', '2 Years'),
        ('all', 'All Time')
    ], default='year')
    
    chart_type = SelectField('Chart Type', choices=[
        ('line', 'Line Chart'),
        ('scatter', 'Scatter Plot'),
        ('bar', 'Bar Chart')
    ], default='line')
    
    show_reference_range = BooleanField('Show Normal Range', default=True)
    show_average = BooleanField('Show Average Line', default=False)
    show_annotations = BooleanField('Show Notes', default=True)
    
    compare_with = SelectField('Compare With', choices=[
        ('none', 'No Comparison'),
        ('previous', 'Previous Period'),
        ('target', 'Target Value'),
        ('other_test', 'Another Test')
    ], default='none')
    
    comparison_test = StringField('Comparison Test', validators=[Optional()])
    target_value = FloatField('Target Value', validators=[Optional()])
    
    export_format = SelectField('Export Format', choices=[
        ('none', 'No Export'),
        ('png', 'PNG Image'),
        ('pdf', 'PDF Report'),
        ('csv', 'CSV Data')
    ], default='none')
    
    submit = SubmitField('View Trends')


class ExportDataForm(FlaskForm):
    export_format = SelectField('Format', choices=[
        ('pdf', 'PDF Report'),
        ('csv', 'CSV Data'),
        ('json', 'JSON Data'),
        ('excel', 'Excel Spreadsheet')
    ], default='pdf')
    
    submit = SubmitField('Export Data')


class HealthConditionForm(FlaskForm):
    """Form for recording health conditions"""
    
    # Basic Information
    name = StringField('Condition Name', validators=[
        DataRequired(),
        Length(max=100, message="Condition name cannot exceed 100 characters")
    ])
    
    type = SelectField('Condition Type', choices=[
        ('', 'Select Type'),
        ('chronic', 'Chronic'),
        ('acute', 'Acute'),
        ('genetic', 'Genetic'),
        ('autoimmune', 'Autoimmune'),
        ('infectious', 'Infectious'),
        ('neurological', 'Neurological'),
        ('cardiovascular', 'Cardiovascular'),
        ('respiratory', 'Respiratory'),
        ('gastrointestinal', 'Gastrointestinal'),
        ('musculoskeletal', 'Musculoskeletal'),
        ('dermatological', 'Dermatological'),
        ('endocrine', 'Endocrine'),
        ('mental_health', 'Mental Health'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_type = StringField('Specify Other Type', validators=[
        Optional(),
        Length(max=50, message="Type specification cannot exceed 50 characters")
    ])
    
    # Medical Coding
    icd10_code = StringField('ICD-10 Code', validators=[
        Optional(),
        Length(max=10, message="ICD-10 code cannot exceed 10 characters")
    ])
    
    # Diagnosis Information
    diagnosis_date = DateField('Diagnosis Date', format='%Y-%m-%d', validators=[
        Optional()
    ])
    
    provider_name = StringField('Diagnosing Provider', validators=[
        Optional(),
        Length(max=100, message="Provider name cannot exceed 100 characters")
    ])
    
    provider_contact = StringField('Provider Contact', validators=[
        Optional(),
        Length(max=100, message="Contact information cannot exceed 100 characters")
    ])
    
    # Severity & Status
    severity = SelectField('Severity', choices=[
        ('', 'Select Severity'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    stage = StringField('Stage/Phase', validators=[
        Optional(),
        Length(max=20, message="Stage cannot exceed 20 characters")
    ])
    
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('controlled', 'Controlled'),
        ('in_remission', 'In Remission'),
        ('resolved', 'Resolved'),
        ('chronic_managed', 'Chronically Managed')
    ], default='active', validators=[DataRequired()])
    
    # Clinical Information
    symptoms = TextAreaField('Symptoms', validators=[
        Optional(),
        Length(max=1000, message="Symptoms description cannot exceed 1000 characters")
    ])
    
    treatment = TextAreaField('Treatment Plan', validators=[
        Optional(),
        Length(max=2000, message="Treatment plan cannot exceed 2000 characters")
    ])
    
    prognosis = TextAreaField('Prognosis', validators=[
        Optional(),
        Length(max=1000, message="Prognosis cannot exceed 1000 characters")
    ])
    
    # Monitoring
    flare_up_triggers = TextAreaField('Flare-up Triggers', validators=[
        Optional(),
        Length(max=500, message="Triggers description cannot exceed 500 characters")
    ])
    
    management_plan = TextAreaField('Management Plan', validators=[
        Optional(),
        Length(max=2000, message="Management plan cannot exceed 2000 characters")
    ])
    
    # Additional Information
    family_history = BooleanField('Family History')
    
    notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=2000, message="Notes cannot exceed 2000 characters")
    ])
    
    submit = SubmitField('Save Condition')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate ICD-10 code format if provided
        if self.icd10_code.data:
            # Basic ICD-10 format validation (letter followed by digits)
            pattern = r'^[A-Z][0-9]{2}(\.[0-9]{1,3})?$'
            if not re.match(pattern, self.icd10_code.data.upper()):
                self.icd10_code.errors.append('Invalid ICD-10 code format. Example: I10, E11.9')
                return False
        
        # Validate diagnosis date is not in the future
        if self.diagnosis_date.data:
            if self.diagnosis_date.data > datetime.now().date():
                self.diagnosis_date.errors.append('Diagnosis date cannot be in the future')
                return False
        
        # Validate other_type is specified if 'other' is selected
        if self.type.data == 'other' and not self.other_type.data:
            self.other_type.errors.append('Please specify the condition type')
            return False
        
        return True
    
    def validate_icd10_code(self, field):
        """Custom validator for ICD-10 code"""
        if field.data:
            # Additional validation for valid ICD-10 codes
            valid_codes = [
                'I10', 'I20', 'I25', 'E11', 'E78', 'J45', 'M54', 'G40', 'F41',
                'K21', 'N18', 'C50', 'C61', 'C34', 'I63', 'J44', 'K74', 'N40'
            ]
            
            # Check if it's a known code or follows the pattern
            code = field.data.upper()
            if code not in valid_codes:
                # Still allow if it follows the pattern
                pattern = r'^[A-Z][0-9]{2}(\.[0-9]{1,3})?$'
                if not re.match(pattern, code):
                    raise ValidationError('Invalid ICD-10 code format. Example: I10, E11.9')

class AllergyForm(FlaskForm):
    """Form for recording allergies"""
    
    # Allergen Information
    allergen_name = StringField('Allergen Name', validators=[
        DataRequired(),
        Length(max=100, message="Allergen name cannot exceed 100 characters")
    ])
    
    type = SelectField('Allergy Type', choices=[
        ('', 'Select Type'),
        ('drug', 'Drug/Medication'),
        ('food', 'Food'),
        ('environmental', 'Environmental'),
        ('insect', 'Insect'),
        ('latex', 'Latex'),
        ('animal', 'Animal'),
        ('contact', 'Contact Dermatitis'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    other_type = StringField('Specify Other Type', validators=[
        Optional(),
        Length(max=50, message="Type specification cannot exceed 50 characters")
    ])
    
    # Reaction Details
    reaction = StringField('Reaction/Symptoms', validators=[
        DataRequired(),
        Length(max=100, message="Reaction description cannot exceed 100 characters")
    ])
    
    reaction_details = TextAreaField('Detailed Reaction Description', validators=[
        Optional(),
        Length(max=500, message="Reaction details cannot exceed 500 characters")
    ])
    
    severity = SelectField('Severity', choices=[
        ('', 'Select Severity'),
        ('mild', 'Mild (localized rash, itching)'),
        ('moderate', 'Moderate (hives, swelling, breathing difficulties)'),
        ('severe', 'Severe (anaphylaxis, life-threatening)')
    ], validators=[DataRequired()])
    
    # Timing
    onset_date = DateField('Onset Date', format='%Y-%m-%d', validators=[
        Optional()
    ])
    
    last_reaction_date = DateField('Last Reaction Date', format='%Y-%m-%d', validators=[
        Optional()
    ])
    
    # Treatment & Management
    treatment = TextAreaField('Treatment/Management', validators=[
        Optional(),
        Length(max=1000, message="Treatment description cannot exceed 1000 characters")
    ])
    
    emergency_medication = StringField('Emergency Medication', validators=[
        Optional(),
        Length(max=100, message="Medication name cannot exceed 100 characters")
    ])
    
    epipen_required = BooleanField('Epinephrine Auto-Injector Required')
    medical_alert_needed = BooleanField('Medical Alert Bracelet Recommended')
    
    # Verification & Status
    verification_status = SelectField('Verification Status', choices=[
        ('confirmed', 'Confirmed (tested/observed)'),
        ('suspected', 'Suspected (self-reported)'),
        ('ruled_out', 'Ruled Out (tested negative)')
    ], default='suspected', validators=[DataRequired()])
    
    verification_method = SelectField('Verification Method', choices=[
        ('', 'Select Method'),
        ('skin_test', 'Skin Test'),
        ('blood_test', 'Blood Test'),
        ('challenge_test', 'Challenge Test'),
        ('clinical_observation', 'Clinical Observation'),
        ('patient_report', 'Patient Report')
    ], validators=[Optional()])
    
    verification_date = DateField('Verification Date', format='%Y-%m-%d', validators=[
        Optional()
    ])
    
    status = SelectField('Current Status', choices=[
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('outgrown', 'Outgrown')
    ], default='active', validators=[DataRequired()])
    
    # Triggers & Avoidance
    triggers = TextAreaField('Known Triggers', validators=[
        Optional(),
        Length(max=500, message="Triggers description cannot exceed 500 characters")
    ])
    
    avoidance_instructions = TextAreaField('Avoidance Instructions', validators=[
        Optional(),
        Length(max=1000, message="Avoidance instructions cannot exceed 1000 characters")
    ])
    
    cross_reactions = TextAreaField('Cross-Reactions', validators=[
        Optional(),
        Length(max=500, message="Cross-reactions cannot exceed 500 characters")
    ])
    
    # Additional Information
    notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=1000, message="Notes cannot exceed 1000 characters")
    ])
    
    submit = SubmitField('Save Allergy')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate dates
        if self.onset_date.data and self.last_reaction_date.data:
            if self.last_reaction_date.data < self.onset_date.data:
                self.last_reaction_date.errors.append('Last reaction date cannot be before onset date')
                return False
        
        if self.verification_date.data:
            if self.verification_date.data > datetime.now().date():
                self.verification_date.errors.append('Verification date cannot be in the future')
                return False
        
        # Validate onset date is not in the future
        if self.onset_date.data:
            if self.onset_date.data > datetime.now().date():
                self.onset_date.errors.append('Onset date cannot be in the future')
                return False
        
        # Validate other_type is specified if 'other' is selected
        if self.type.data == 'other' and not self.other_type.data:
            self.other_type.errors.append('Please specify the allergy type')
            return False
        
        # Validate verification method if status is confirmed
        if self.verification_status.data == 'confirmed' and not self.verification_method.data:
            self.verification_method.errors.append('Please specify the verification method for confirmed allergies')
            return False
        
        return True
    
    def validate_allergen_name(self, field):
        """Custom validator for allergen names"""
        # Common allergen validation
        common_allergens = [
            'penicillin', 'aspirin', 'ibuprofen', 'sulfa', 'codeine',
            'peanuts', 'tree nuts', 'shellfish', 'fish', 'eggs', 'milk',
            'soy', 'wheat', 'sesame', 'pollen', 'dust mites', 'mold',
            'pet dander', 'bee sting', 'wasp sting', 'latex'
        ]
        
        allergen = field.data.lower()
        
        # Check for common misspellings or variations
        variations = {
            'penecillin': 'penicillin',
            'penicilin': 'penicillin',
            'peanutes': 'peanuts',
            'penuts': 'peanuts',
            'shell fish': 'shellfish'
        }
        
        if allergen in variations:
            field.data = variations[allergen].title()
        
        # Suggest standardization for known allergens
        for common in common_allergens:
            if common in allergen and allergen != common:
                # Keep the original but log suggestion
                # In production, you might want to standardize
                pass

class QuickHealthConditionForm(FlaskForm):
    """Quick form for adding health conditions"""
    
    name = StringField('Condition', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    type = SelectField('Type', choices=[
        ('chronic', 'Chronic'),
        ('acute', 'Acute'),
        ('other', 'Other')
    ], default='chronic')
    
    severity = SelectField('Severity', choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='moderate')
    
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('controlled', 'Controlled')
    ], default='active')
    
    submit = SubmitField('Add Condition')

class QuickAllergyForm(FlaskForm):
    """Quick form for adding allergies"""
    
    allergen_name = StringField('Allergen', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    type = SelectField('Type', choices=[
        ('drug', 'Drug'),
        ('food', 'Food'),
        ('environmental', 'Environmental')
    ], default='food')
    
    severity = SelectField('Severity', choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='moderate')
    
    reaction = StringField('Reaction', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    submit = SubmitField('Add Allergy')

class HealthConditionSearchForm(FlaskForm):
    """Form for searching/filtering health conditions"""
    
    search_term = StringField('Search', validators=[Optional()])
    
    type = SelectField('Type', choices=[
        ('', 'All Types'),
        ('chronic', 'Chronic'),
        ('acute', 'Acute'),
        ('genetic', 'Genetic'),
        ('autoimmune', 'Autoimmune')
    ], default='')
    
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('active', 'Active'),
        ('controlled', 'Controlled'),
        ('resolved', 'Resolved')
    ], default='')
    
    severity = SelectField('Severity', choices=[
        ('', 'All Severities'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='')
    
    sort_by = SelectField('Sort By', choices=[
        ('name_asc', 'Name (A-Z)'),
        ('name_desc', 'Name (Z-A)'),
        ('date_desc', 'Most Recent'),
        ('severity_desc', 'Severity (High to Low)')
    ], default='name_asc')
    
    submit = SubmitField('Search Conditions')

class AllergySearchForm(FlaskForm):
    """Form for searching/filtering allergies"""
    
    search_term = StringField('Search', validators=[Optional()])
    
    type = SelectField('Type', choices=[
        ('', 'All Types'),
        ('drug', 'Drug'),
        ('food', 'Food'),
        ('environmental', 'Environmental'),
        ('insect', 'Insect')
    ], default='')
    
    severity = SelectField('Severity', choices=[
        ('', 'All Severities'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], default='')
    
    verification_status = SelectField('Verification', choices=[
        ('', 'All'),
        ('confirmed', 'Confirmed Only'),
        ('suspected', 'Suspected Only')
    ], default='')
    
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('active', 'Active'),
        ('resolved', 'Resolved')
    ], default='')
    
    sort_by = SelectField('Sort By', choices=[
        ('name_asc', 'Allergen (A-Z)'),
        ('name_desc', 'Allergen (Z-A)'),
        ('severity_desc', 'Severity (High to Low)'),
        ('date_desc', 'Most Recent')
    ], default='name_asc')
    
    submit = SubmitField('Search Allergies')

# Add to the __all__ list at the end of forms.py
__all__ = [
    'VitalSignsForm', 'SymptomForm', 'MoodForm', 'DailyCheckinForm',
    'MedicalEvaluationForm', 'LabTestForm', 'ImagingStudyForm',
    'ComprehensiveEvaluationForm', 'LabTestSearchForm', 'ImagingSearchForm',
    'LabTrendForm', 'HealthConditionForm', 'AllergyForm', 
    'QuickHealthConditionForm', 'QuickAllergyForm',
    'HealthConditionSearchForm', 'AllergySearchForm'
]