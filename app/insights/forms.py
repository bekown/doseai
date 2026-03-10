# app/insights/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    DateField, SelectField, IntegerField, FloatField,
    TextAreaField, BooleanField, SubmitField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import datetime, timedelta

class InsightFilterForm(FlaskForm):
    """Form for filtering insights and analytics"""
    
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 90 days'),
        ('180', 'Last 6 months'),
        ('365', 'Last year'),
        ('custom', 'Custom Range')
    ], default='30')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    medication_filter = SelectField('Medication', choices=[
        ('all', 'All Medications'),
        ('specific', 'Specific Medication')
    ], default='all')
    
    medication_id = SelectField('Select Medication', coerce=int, validators=[Optional()])
    
    # Chart options
    chart_type = SelectField('Chart Type', choices=[
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('scatter', 'Scatter Plot')
    ], default='line')
    
    show_trends = BooleanField('Show Trends', default=True)
    show_comparisons = BooleanField('Show Comparisons', default=False)
    
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
            
            if self.end_date.data > datetime.now().date():
                self.end_date.errors.append('End date cannot be in the future')
                return False
        
        return True

class ExportDataForm(FlaskForm):
    """Form for exporting health data"""
    
    export_format = SelectField('Format', choices=[
        ('pdf', 'PDF Report'),
        ('csv', 'CSV Data'),
        ('json', 'JSON Data'),
        ('excel', 'Excel Spreadsheet')
    ], default='pdf')
    
    data_types = SelectField('Data to Include', choices=[
        ('all', 'All Data'),
        ('medications', 'Medications Only'),
        ('vitals', 'Vital Signs Only'),
        ('symptoms', 'Symptoms Only'),
        ('evaluations', 'Medical Evaluations Only')
    ], default='all')
    
    date_range = SelectField('Date Range', choices=[
        ('all', 'All Time'),
        ('year', 'Last Year'),
        ('month', 'Last Month'),
        ('custom', 'Custom Range')
    ], default='all')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    include_charts = BooleanField('Include Charts', default=True)
    include_summary = BooleanField('Include Summary', default=True)
    
    submit = SubmitField('Export Data')

class GoalSettingForm(FlaskForm):
    """Form for setting health goals"""
    
    goal_type = SelectField('Goal Type', choices=[
        ('adherence', 'Medication Adherence'),
        ('vitals', 'Vital Signs'),
        ('symptoms', 'Symptom Management'),
        ('lifestyle', 'Lifestyle'),
        ('weight', 'Weight Management')
    ], validators=[DataRequired()])
    
    target_value = FloatField('Target Value', validators=[DataRequired()])
    
    target_unit = StringField('Unit', validators=[Optional()])
    
    timeframe = SelectField('Timeframe', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], default='weekly')
    
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    description = TextAreaField('Goal Description', validators=[Optional()])
    
    reminder_enabled = BooleanField('Enable Reminders', default=True)
    
    submit = SubmitField('Set Goal')