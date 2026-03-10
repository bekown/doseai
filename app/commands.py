# app/commands.py

import click
from flask.cli import with_appcontext
from app.models import db, User, Profile
from app.extensions import bcrypt
from datetime import datetime
from app import initialize_database 

@click.command('init-db')
@with_appcontext
def init_db():
    """Initialize the database. by calling function in init_db.py"""
    initialize_database()    
    click.echo('✅ Database initialized.')

@click.command('seed-db')
@with_appcontext
def seed_db():
    """Seed the database with sample data."""
    # Create a test user
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    
    # Create profile
    profile = Profile(
        user=user,
        first_name='Test',
        last_name='User',
        phone='+1234567890'
    )
    
    db.session.add(user)
    db.session.commit()
    
    click.echo('✅ Database seeded with sample data.')

@click.command('create-admin')
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.password_option()
@with_appcontext
def create_admin(username, email, password):
    """Create an admin user."""
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        click.echo('❌ User with this email already exists.')
        return
    
    user = User(
        username=username,
        email=email,
        is_active=True
    )
    user.set_password(password)
    
    # Create profile
    profile = Profile(user=user)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'✅ Admin user {username} created successfully.')