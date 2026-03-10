# init_db.py

from flask import Flask
from models import db, User, Profile, Medication, Prescription, Dose, HealthCondition, Allergy
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db

def initialize_database():
    """Initialize database (different name to avoid conflict)"""
    app = create_app()
    
    with app.app_context():
        db.create_all()        
        
        # Optional: Add sample data
        add_sample_data()
    
    return True

def add_sample_data():
    """Add sample data for testing"""
    app = create_app()
    
    with app.app_context():
        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        
        # Create profile
        profile = Profile(
            user=user,
            first_name='John',
            last_name='Doe',
            phone='+1234567890',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip_code='12345',
            gender='male',
            date_of_birth=datetime(1980, 1, 1),
            height_cm=180,
            weight_kg=75,
            blood_type='O+'
        )
        
        # Create health conditions
        condition = HealthCondition(
            user=user,
            name='Type 2 Diabetes',
            type='chronic',
            diagnosis_date=datetime(2020, 5, 1),
            severity='moderate',
            status='active'
        )
        
        # Create allergy
        allergy = Allergy(
            user=user,
            allergen_name='Penicillin',
            type='drug',
            severity='severe',
            status='active'
        )
        
        # Create medication
        medication = Medication(
            user=user,
            name='Metformin',
            strength='500mg',
            form='tablet'
        )
        
        # Create prescription
        prescription = Prescription(
            user=user,
            medication=medication,
            dosage='Take 1 tablet',
            frequency=2,
            start_date=datetime.now(),
            status='active'
        )
        
        # Add all to session
        db.session.add(user)
        db.session.commit()
        
        print("✅ Sample data added successfully!")

if __name__ == '__main__':
    initialize_database()
    print("✅ Database created successfully!")
    
    # Uncomment to add sample data
    # add_sample_data()