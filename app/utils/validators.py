# app/utils/validators.py

import re
from datetime import datetime
from flask import current_app

class Validator:
    """Centralized validation service"""
    
    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < current_app.config.get('PASSWORD_MIN_LENGTH', 8):
            return False, "Password must be at least 8 characters"
        
        if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
            if not re.search(r'[A-Z]', password):
                return False, "Password must contain at least one uppercase letter"
        
        if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
            if not re.search(r'[a-z]', password):
                return False, "Password must contain at least one lowercase letter"
        
        if current_app.config.get('PASSWORD_REQUIRE_DIGITS', True):
            if not re.search(r'\d', password):
                return False, "Password must contain at least one digit"
        
        if current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True):
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_phone(phone):
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))
    
    @staticmethod
    def validate_date_of_birth(dob):
        """Validate date of birth (must be at least 13 years old)"""
        try:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            return age >= 13
        except:
            return False
    
    @staticmethod
    def validate_medication_dosage(dosage):
        """Validate medication dosage format"""
        patterns = [
            r'^\d+(\.\d+)?\s*(mg|mcg|g|ml|mL|IU|units?)$',
            r'^\d+\s*x\s*\d+(\.\d+)?\s*(mg|mcg|g|ml)$',
            r'^\d+(\.\d+)?%$',
            r'^\d+\s*tablet(s)?$',
            r'^\d+\s*capsule(s)?$'
        ]
        return any(re.match(pattern, dosage, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def validate_vital_signs(vitals):
        """Validate vital sign ranges"""
        validated = {}
        
        if vitals.get('heart_rate'):
            hr = int(vitals['heart_rate'])
            if 30 <= hr <= 250:
                validated['heart_rate'] = hr
        
        if vitals.get('systolic_bp') and vitals.get('diastolic_bp'):
            sys = int(vitals['systolic_bp'])
            dia = int(vitals['diastolic_bp'])
            if 50 <= sys <= 250 and 30 <= dia <= 150:
                validated['systolic_bp'] = sys
                validated['diastolic_bp'] = dia
        
        if vitals.get('temperature'):
            temp = float(vitals['temperature'])
            if 30 <= temp <= 45:  # Celsius
                validated['temperature'] = temp
        
        return validated