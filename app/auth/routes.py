# app/auth/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, Profile
from app.utils.validators import Validator
from .forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm,EmergencyContactForm
from datetime import datetime
from app.extensions import db
from utils.notification_service import NotificationService

auth_bp = Blueprint('auth', __name__)

notificationservice = NotificationService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account is deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Logged in successfully!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Validate password
        is_valid, message = Validator.validate_password(form.password.data)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if user exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_active=True
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create empty profile
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from .forms import ProfileForm
    
    form = ProfileForm(obj=current_user.profile)
    
    if form.validate_on_submit():
        form.populate_obj(current_user.profile)
        current_user.profile.updated_at = datetime.utcnow()
        db.session.commit()
        # Notification
        notificationservice.create_notification (
            user_id=current_user.id,
            title="Profile updated",
            message="Your profile has been updated successfully.",
            type="health_alerts"
        )
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    from .forms import ChangePasswordForm
    
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Validate new password
        is_valid, message = Validator.validate_password(form.new_password.data)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        # Notification
        notificationservice.create_notification (
            user_id=current_user.id,
            title="Password changed",
            message="Your password has been changed successfully.",
            type="health_alerts"
        )
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form)
