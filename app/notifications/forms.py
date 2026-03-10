# app/notifications/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, SelectField, TimeField, DateTimeField,
    BooleanField, SubmitField, TextAreaField, FieldList, FormField,
    HiddenField, SelectMultipleField, DateField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from datetime import datetime, time
import re

class NotificationPreferenceForm(FlaskForm):
    """Form for notification preferences"""
    
    # Channel preferences
    enable_push = BooleanField('Push Notifications', default=True)
    enable_email = BooleanField('Email Notifications', default=True)
    enable_sms = BooleanField('SMS Notifications', default=False)
    
    # Notification type preferences
    enable_medication_reminders = BooleanField('Medication Reminders', default=True)
    enable_refill_reminders = BooleanField('Refill Reminders', default=True)
    enable_low_stock_alerts = BooleanField('Low Stock Alerts', default=True)
    enable_missed_dose_alerts = BooleanField('Missed Dose Alerts', default=True)
    enable_interaction_alerts = BooleanField('Drug Interaction Alerts', default=True)
    enable_contraindication_alerts = BooleanField('Contraindication Alerts', default=True)
    enable_health_alerts = BooleanField('Health Alerts', default=True)
    enable_appointment_reminders = BooleanField('Appointment Reminders', default=True)
    enable_daily_checkin_reminders = BooleanField('Daily Check-in Reminders', default=True)
    enable_wellness_alerts = BooleanField('Wellness Score Updates', default=True)
    enable_ai_insights = BooleanField('AI Health Insights', default=True)
    
    # Timing preferences
    reminder_lead_minutes = IntegerField('Reminder Lead Time (minutes)', default=30, validators=[
        NumberRange(min=1, max=120, message='Lead time must be between 1-120 minutes')
    ])
    
    snooze_duration_minutes = IntegerField('Snooze Duration (minutes)', default=10, validators=[
        NumberRange(min=1, max=60, message='Snooze duration must be between 1-60 minutes')
    ])
    
    # Quiet hours
    quiet_hours_enabled = BooleanField('Enable Quiet Hours', default=True)
    quiet_start = TimeField('Quiet Hours Start', format='%H:%M', default=time(22, 0), validators=[Optional()])
    quiet_end = TimeField('Quiet Hours End', format='%H:%M', default=time(7, 0), validators=[Optional()])
    
    # Days of week for notifications
    days_of_week = SelectMultipleField('Active Days', choices=[
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday')
    ], default=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'])
    
    # Time ranges for notifications
    notification_start_time = TimeField('Daily Start Time', format='%H:%M', default=time(7, 0), validators=[Optional()])
    notification_end_time = TimeField('Daily End Time', format='%H:%M', default=time(22, 0), validators=[Optional()])
    
    # Advanced settings
    smart_reminders = BooleanField('Smart Reminders (AI-optimized timing)', default=True)
    allow_weekend_notifications = BooleanField('Weekend Notifications', default=True)
    critical_alerts_always = BooleanField('Critical Alerts Always On', default=True)
    batch_notifications = BooleanField('Batch Multiple Notifications', default=True)
    vibration_enabled = BooleanField('Enable Vibration', default=True)
    sound_enabled = BooleanField('Enable Sound', default=True)
    
    # Medication-specific preferences
    class MedicationPreferenceForm(FlaskForm):
        medication_id = HiddenField()
        medication_name = StringField('Medication', render_kw={'readonly': True})
        enable_reminders = BooleanField('Enable', default=True)
        custom_lead_time = IntegerField('Custom Lead Time (min)', validators=[Optional(), NumberRange(min=1, max=120)])
    
    medication_preferences = FieldList(FormField(MedicationPreferenceForm), min_entries=0)
    
    # Emergency override
    emergency_contact_override = BooleanField('Allow Emergency Contact Notifications', default=True)
    override_quiet_hours = BooleanField('Override Quiet Hours for Urgent Alerts', default=True)
    
    submit = SubmitField('Save Preferences')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate quiet hours
        if self.quiet_hours_enabled.data:
            if not self.quiet_start.data or not self.quiet_end.data:
                self.quiet_start.errors.append('Both start and end times are required for quiet hours')
                return False
            
            # Check if quiet hours span midnight
            if self.quiet_start.data >= self.quiet_end.data:
                # This is allowed (spans midnight), no validation needed
                pass
        
        # Validate daily time range
        if self.notification_start_time.data and self.notification_end_time.data:
            if self.notification_start_time.data >= self.notification_end_time.data:
                self.notification_start_time.errors.append('Start time must be before end time')
                return False
        
        return True

class CustomNotificationForm(FlaskForm):
    """Form for creating custom notifications"""
    
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=2, max=200, message='Title must be between 2-200 characters')
    ])
    
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Message must be between 10-500 characters')
    ])
    
    notification_type = SelectField('Notification Type', choices=[
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('emergency', 'Emergency'),
        ('success', 'Success'),
        ('update', 'Update')
    ], default='info', validators=[DataRequired()])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', validators=[DataRequired()])
    
    # Scheduling
    scheduled_time = DateTimeField('Scheduled Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    send_now = BooleanField('Send Immediately', default=True)
    
    # Recurrence
    repeat = BooleanField('Repeat', default=False)
    repeat_frequency = SelectField('Repeat Frequency', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], default='daily')
    
    repeat_days = SelectMultipleField('Repeat Days', choices=[
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday')
    ], default=['mon', 'tue', 'wed', 'thu', 'fri'])
    
    repeat_end_date = DateField('Repeat End Date', format='%Y-%m-%d', validators=[Optional()])
    repeat_count = IntegerField('Repeat Count', validators=[Optional(), NumberRange(min=1)])
    
    # Action
    is_action_required = BooleanField('Action Required', default=False)
    action_label = StringField('Action Button Label', validators=[Optional(), Length(max=50)])
    action_url = StringField('Action URL', validators=[Optional()])
    
    # Category
    category = SelectField('Category', choices=[
        ('medication', 'Medication'),
        ('health', 'Health'),
        ('appointment', 'Appointment'),
        ('system', 'System'),
        ('personal', 'Personal'),
        ('other', 'Other')
    ], default='personal')
    
    # Associated entities
    medication_id = SelectField('Associated Medication', coerce=int, validators=[Optional()])
    prescription_id = SelectField('Associated Prescription', coerce=int, validators=[Optional()])
    
    # Expiration
    expires_at = DateTimeField('Expires At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Custom data
    custom_data = TextAreaField('Custom Data (JSON)', validators=[Optional()],
                              description='Additional data in JSON format')
    
    submit = SubmitField('Create Notification')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate scheduled time is not in the past
        if self.scheduled_time.data and not self.send_now.data:
            if self.scheduled_time.data < datetime.utcnow():
                self.scheduled_time.errors.append('Scheduled time cannot be in the past')
                return False
        
        # Validate repeat options
        if self.repeat.data:
            if not self.repeat_frequency.data:
                self.repeat_frequency.errors.append('Repeat frequency is required')
                return False
            
            if self.repeat_frequency.data == 'weekly' and not self.repeat_days.data:
                self.repeat_days.errors.append('At least one day must be selected for weekly repeats')
                return False
        
        # Validate custom JSON data
        if self.custom_data.data:
            try:
                import json
                json.loads(self.custom_data.data)
            except json.JSONDecodeError:
                self.custom_data.errors.append('Invalid JSON format')
                return False
        
        return True

class NotificationFilterForm(FlaskForm):
    """Form for filtering notifications"""
    
    notification_type = SelectField('Type', choices=[
        ('all', 'All Types'),
        ('medication_reminder', 'Medication Reminders'),
        ('refill_reminder', 'Refill Reminders'),
        ('missed_dose', 'Missed Dose'),
        ('health_alert', 'Health Alerts'),
        ('interaction_warning', 'Interaction Warnings'),
        ('contraindication_warning', 'Contraindication Warnings'),
        ('appointment_reminder', 'Appointment Reminders'),
        ('system', 'System'),
        ('custom', 'Custom')
    ], default='all')
    
    priority = SelectField('Priority', choices=[
        ('all', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='all')
    
    status = SelectField('Status', choices=[
        ('all', 'All Status'),
        ('unread', 'Unread Only'),
        ('read', 'Read Only'),
        ('action_required', 'Action Required'),
        ('action_taken', 'Action Taken')
    ], default='all')
    
    date_range = SelectField('Date Range', choices=[
        ('all', 'All Time'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('week', 'Past Week'),
        ('month', 'Past Month'),
        ('custom', 'Custom Range')
    ], default='week')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    sort_by = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('priority', 'Priority (High to Low)'),
        ('type', 'Type')
    ], default='newest')
    
    items_per_page = SelectField('Items Per Page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')
    
    include_expired = BooleanField('Include Expired', default=False)
    
    submit = SubmitField('Apply Filters')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate custom date range
        if self.date_range.data == 'custom':
            if not self.start_date.data or not self.end_date.data:
                self.start_date.errors.append('Both start and end dates are required for custom range')
                return False
            
            if self.start_date.data > self.end_date.data:
                self.start_date.errors.append('Start date must be before end date')
                return False
            
            if self.end_date.data > datetime.utcnow().date():
                self.end_date.errors.append('End date cannot be in the future')
                return False
        
        return True

class NotificationTemplateForm(FlaskForm):
    """Form for creating notification templates"""
    
    template_name = StringField('Template Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    
    template_type = SelectField('Template Type', choices=[
        ('medication_reminder', 'Medication Reminder'),
        ('refill_reminder', 'Refill Reminder'),
        ('missed_dose', 'Missed Dose Alert'),
        ('health_checkin', 'Health Check-in Reminder'),
        ('appointment', 'Appointment Reminder'),
        ('welcome', 'Welcome Message'),
        ('weekly_summary', 'Weekly Summary'),
        ('monthly_report', 'Monthly Report'),
        ('custom', 'Custom Template')
    ], validators=[DataRequired()])
    
    title_template = StringField('Title Template', validators=[
        DataRequired(),
        Length(max=200)
    ], description='Use variables: {medication_name}, {dosage}, {time}, etc.')
    
    message_template = TextAreaField('Message Template', validators=[
        DataRequired(),
        Length(max=1000)
    ], description='Use variables in curly braces')
    
    # Variables available in template
    available_variables = TextAreaField('Available Variables', render_kw={'readonly': True, 'rows': 4})
    
    # Default values
    default_priority = SelectField('Default Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    
    default_lead_time = IntegerField('Default Lead Time (minutes)', default=30, validators=[
        NumberRange(min=0, max=240)
    ])
    
    is_active = BooleanField('Active', default=True)
    
    description = TextAreaField('Description', validators=[Optional()])
    
    submit = SubmitField('Save Template')

class SnoozeForm(FlaskForm):
    """Form for snoozing notifications"""
    
    notification_id = HiddenField(validators=[DataRequired()])
    
    snooze_duration = SelectField('Snooze Duration', choices=[
        ('5', '5 minutes'),
        ('10', '10 minutes'),
        ('15', '15 minutes'),
        ('30', '30 minutes'),
        ('60', '1 hour'),
        ('120', '2 hours'),
        ('240', '4 hours'),
        ('480', '8 hours'),
        ('custom', 'Custom')
    ], default='10')
    
    custom_minutes = IntegerField('Custom Minutes', validators=[
        Optional(),
        NumberRange(min=1, max=1440)  # Max 24 hours
    ])
    
    snooze_reason = SelectField('Reason for Snooze', choices=[
        ('busy', 'I\'m busy right now'),
        ('later', 'I\'ll take it later'),
        ('not_available', 'Medication not available'),
        ('not_feeling_well', 'Not feeling well'),
        ('other', 'Other reason')
    ], default='busy')
    
    other_reason = TextAreaField('Other Reason', validators=[Optional()])
    
    submit = SubmitField('Snooze')

class NotificationActionForm(FlaskForm):
    """Form for taking action on notifications"""
    
    notification_id = HiddenField(validators=[DataRequired()])
    
    action_taken = SelectField('Action Taken', choices=[
        ('dose_taken', 'Dose Taken'),
        ('refill_scheduled', 'Refill Scheduled'),
        ('doctor_notified', 'Doctor Notified'),
        ('symptoms_recorded', 'Symptoms Recorded'),
        ('appointment_scheduled', 'Appointment Scheduled'),
        ('medication_adjusted', 'Medication Adjusted'),
        ('ignored', 'Ignored'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    action_details = TextAreaField('Action Details', validators=[Optional()])
    
    follow_up_needed = BooleanField('Follow-up Needed', default=False)
    follow_up_date = DateField('Follow-up Date', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Submit Action')

class EmergencyNotificationForm(FlaskForm):
    """Form for emergency notifications"""
    
    emergency_type = SelectField('Emergency Type', choices=[
        ('severe_symptom', 'Severe Symptom'),
        ('critical_vitals', 'Critical Vital Signs'),
        ('medication_error', 'Medication Error'),
        ('allergic_reaction', 'Allergic Reaction'),
        ('overdose_suspected', 'Overdose Suspected'),
        ('other_medical', 'Other Medical Emergency')
    ], validators=[DataRequired()])
    
    severity = SelectField('Severity Level', choices=[
        ('urgent', 'Urgent - Needs attention soon'),
        ('critical', 'Critical - Needs immediate attention'),
        ('emergency', 'Emergency - Call 911/emergency services')
    ], default='urgent', validators=[DataRequired()])
    
    description = TextAreaField('Emergency Description', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    
    symptoms = TextAreaField('Symptoms Experienced', validators=[Optional()])
    
    # Who to notify
    notify_emergency_contacts = BooleanField('Notify Emergency Contacts', default=True)
    notify_healthcare_provider = BooleanField('Notify Healthcare Provider', default=False)
    call_emergency_services = BooleanField('Suggest Calling Emergency Services', default=False)
    
    # Custom message for contacts
    custom_message = TextAreaField('Custom Message for Contacts', validators=[Optional()])
    
    # Location (if available)
    current_location = StringField('Current Location', validators=[Optional()])
    share_location = BooleanField('Share Location with Contacts', default=False)
    
    submit = SubmitField('Send Emergency Alert')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validate emergency type specific requirements
        if self.emergency_type.data in ['severe_symptom', 'allergic_reaction', 'overdose_suspected']:
            if not self.symptoms.data:
                self.symptoms.errors.append('Please describe the symptoms for this type of emergency')
                return False
        
        return True

class TestNotificationForm(FlaskForm):
    """Form for testing notification settings"""
    
    test_type = SelectField('Test Notification Type', choices=[
        ('medication_reminder', 'Medication Reminder'),
        ('refill_reminder', 'Refill Reminder'),
        ('missed_dose', 'Missed Dose Alert'),
        ('health_alert', 'Health Alert'),
        ('system', 'System Notification'),
        ('custom', 'Custom Notification')
    ], default='medication_reminder')
    
    delivery_method = SelectMultipleField('Delivery Method', choices=[
        ('push', 'Push Notification'),
        ('email', 'Email'),
        ('sms', 'SMS')
    ], default=['push'])
    
    medication_id = SelectField('Test Medication', coerce=int, validators=[Optional()])
    
    # Custom test content
    custom_title = StringField('Custom Title', validators=[Optional()])
    custom_message = TextAreaField('Custom Message', validators=[Optional()])
    
    # Test timing
    send_immediately = BooleanField('Send Immediately', default=True)
    test_time = DateTimeField('Test Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    submit = SubmitField('Send Test Notification')

class NotificationStatisticsForm(FlaskForm):
    """Form for viewing notification statistics"""
    
    period = SelectField('Time Period', choices=[
        ('day', 'Last 24 Hours'),
        ('week', 'Last 7 Days'),
        ('month', 'Last 30 Days'),
        ('quarter', 'Last 90 Days'),
        ('year', 'Last 365 Days'),
        ('custom', 'Custom Range')
    ], default='week')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    group_by = SelectField('Group By', choices=[
        ('type', 'Notification Type'),
        ('priority', 'Priority Level'),
        ('status', 'Status'),
        ('day', 'Day'),
        ('hour', 'Hour of Day')
    ], default='type')
    
    chart_type = SelectField('Chart Type', choices=[
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Chart'),
        ('table', 'Data Table')
    ], default='bar')
    
    include_metrics = SelectMultipleField('Include Metrics', choices=[
        ('sent', 'Sent Notifications'),
        ('read', 'Read Notifications'),
        ('action_taken', 'Actions Taken'),
        ('snoozed', 'Snoozed Notifications'),
        ('dismissed', 'Dismissed Notifications')
    ], default=['sent', 'read', 'action_taken'])
    
    export_format = SelectField('Export Format', choices=[
        ('none', 'No Export'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('pdf', 'PDF Report')
    ], default='none')
    
    submit = SubmitField('View Statistics')