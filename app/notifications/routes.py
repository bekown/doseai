# app/notifications/routes.py

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from app.models import db, User, Notification, NotificationPreference, Medication, Prescription, DailyCheckin
from app.notifications.forms import (
    NotificationPreferenceForm, CustomNotificationForm, NotificationFilterForm,
    NotificationTemplateForm, SnoozeForm, NotificationActionForm,
    EmergencyNotificationForm, TestNotificationForm, NotificationStatisticsForm
)
from app.utils.notification_service import NotificationService
import json

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# ==================== Main Notification Views ====================

@bp.route('/')
@login_required
def index():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    form = NotificationFilterForm()
    
    # Build query based on form filters
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filters from query parameters (for pagination)
    notification_type = request.args.get('notification_type', 'all')
    priority = request.args.get('priority', 'all')
    status = request.args.get('status', 'all')
    date_range = request.args.get('date_range', 'week')
    sort_by = request.args.get('sort_by', 'newest')
    include_expired = request.args.get('include_expired', 'false') == 'true'
    
    # Apply filters
    if notification_type != 'all':
        query = query.filter_by(type=notification_type)
    
    if priority != 'all':
        query = query.filter_by(priority=priority)
    
    if status == 'unread':
        query = query.filter_by(is_read=False)
    elif status == 'read':
        query = query.filter_by(is_read=True)
    elif status == 'action_required':
        query = query.filter_by(is_action_required=True, action_taken=False)
    elif status == 'action_taken':
        query = query.filter_by(action_taken=True)
    
    # Date range filter
    today = datetime.utcnow().date()
    if date_range == 'today':
        query = query.filter(func.date(Notification.created_at) == today)
    elif date_range == 'yesterday':
        query = query.filter(func.date(Notification.created_at) == today - timedelta(days=1))
    elif date_range == 'week':
        query = query.filter(Notification.created_at >= datetime.utcnow() - timedelta(days=7))
    elif date_range == 'month':
        query = query.filter(Notification.created_at >= datetime.utcnow() - timedelta(days=30))
    
    # Expired filter
    if not include_expired:
        query = query.filter(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
    
    # Sorting
    if sort_by == 'newest':
        query = query.order_by(Notification.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Notification.created_at.asc())
    elif sort_by == 'priority':
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        query = query.order_by(
            func.coalesce(
                func.nullif(func.lower(Notification.priority), None),
                'medium'
            )
        )
    
    # Get paginated results
    notifications = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Update form data
    form.notification_type.data = notification_type
    form.priority.data = priority
    form.status.data = status
    form.date_range.data = date_range
    form.sort_by.data = sort_by
    form.include_expired.data = include_expired
    
    return render_template('notifications/index.html',
                         notifications=notifications,
                         form=form,
                         active_page='notifications')

@bp.route('/unread')
@login_required
def unread():
    """View unread notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('notifications/unread.html',
                         notifications=unread_notifications,
                         active_page='notifications')

@bp.route('/action-required')
@login_required
def action_required():
    """View notifications requiring action"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    action_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_action_required=True,
        action_taken=False
    ).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('notifications/action_required.html',
                         notifications=action_notifications,
                         active_page='notifications')

@bp.route('/api/list')
@login_required
def api_list():
    """API endpoint for notifications (for mobile apps)"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
    
    notifications = NotificationService.get_user_notifications(
        current_user.id, unread_only=unread_only, limit=limit
    )
    
    # Format for API response
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'is_action_required': notification.is_action_required,
            'action_taken': notification.action_taken,
            'action_url': notification.action_url,
            'action_label': notification.action_label,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
            'data': notification.data,
            'medication': {
                'id': notification.medication.id,
                'name': notification.medication.name
            } if notification.medication else None
        })
    
    return jsonify({
        'success': True,
        'notifications': notifications_data,
        'count': len(notifications_data),
        'unread_count': len([n for n in notifications if not n.is_read])
    })

# ==================== Notification Actions ====================

@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a notification as read"""
    success = NotificationService.mark_as_read(notification_id, current_user.id)
    
    if request.is_json:
        return jsonify({'success': success})
    
    if success:
        flash('Notification marked as read', 'success')
    else:
        flash('Notification not found', 'error')
    
    return redirect(request.referrer or url_for('notifications.index'))

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    
    # Clear cache
    from app.utils.cache_service import cache
    cache.delete(f'notifications_{current_user.id}')
    
    if request.is_json:
        return jsonify({'success': True})
    
    flash('All notifications marked as read', 'success')
    return redirect(request.referrer or url_for('notifications.index'))

@bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    success = NotificationService.delete_notification(notification_id, current_user.id)
    
    if request.is_json:
        return jsonify({'success': success})
    
    if success:
        flash('Notification deleted', 'success')
    else:
        flash('Notification not found', 'error')
    
    return redirect(request.referrer or url_for('notifications.index'))

@bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    """Clear all read notifications"""
    try:
        # Delete all read notifications for the user
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=True
        ).delete()
        
        db.session.commit()
        
        # Clear cache
        from app.utils.cache_service import cache
        cache.delete(f'notifications_{current_user.id}')
        
        flash('All read notifications cleared', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error clearing notifications: {e}')
        flash('Error clearing notifications', 'error')
    
    return redirect(url_for('notifications.index'))

# ==================== Snooze Functionality ====================

@bp.route('/<int:notification_id>/snooze', methods=['GET', 'POST'])
@login_required
def snooze_notification(notification_id):
    """Snooze a notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    form = SnoozeForm()
    form.notification_id.data = notification_id
    
    if form.validate_on_submit():
        # Calculate snooze duration
        if form.snooze_duration.data == 'custom':
            minutes = form.custom_minutes.data
        else:
            minutes = int(form.snooze_duration.data)
        
        # Update notification
        notification.is_read = False
        notification.read_at = None
        notification.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        
        # Record snooze reason in data
        if not notification.data:
            notification.data = {}
        
        snooze_data = {
            'snoozed_at': datetime.utcnow().isoformat(),
            'snooze_duration_minutes': minutes,
            'snooze_reason': form.snooze_reason.data,
            'other_reason': form.other_reason.data if form.snooze_reason.data == 'other' else None
        }
        
        if 'snoozes' not in notification.data:
            notification.data['snoozes'] = []
        
        notification.data['snoozes'].append(snooze_data)
        
        db.session.commit()
        
        # Clear cache
        from app.utils.cache_service import cache
        cache.delete(f'notifications_{current_user.id}')
        
        flash(f'Notification snoozed for {minutes} minutes', 'success')
        return redirect(url_for('notifications.index'))
    
    return render_template('notifications/snooze.html',
                         form=form,
                         notification=notification)

# ==================== Action Handling ====================

@bp.route('/<int:notification_id>/action', methods=['GET', 'POST'])
@login_required
def take_action(notification_id):
    """Take action on a notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id,
        is_action_required=True
    ).first_or_404()
    
    form = NotificationActionForm()
    form.notification_id.data = notification_id
    
    if form.validate_on_submit():
        # Update notification
        notification.action_taken = True
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        # Store action details
        if not notification.data:
            notification.data = {}
        
        notification.data['action_details'] = {
            'action_taken': form.action_taken.data,
            'details': form.action_details.data,
            'timestamp': datetime.utcnow().isoformat(),
            'follow_up_needed': form.follow_up_needed.data,
            'follow_up_date': form.follow_up_date.data.isoformat() if form.follow_up_date.data else None
        }
        
        db.session.commit()
        
        # Clear cache
        from app.utils.cache_service import cache
        cache.delete(f'notifications_{current_user.id}')
        
        flash('Action recorded successfully', 'success')
        
        # Redirect based on action type
        if notification.type == 'medication_reminder' and form.action_taken.data == 'dose_taken':
            return redirect(url_for('medications.log_dose', medication_id=notification.medication_id))
        elif notification.type == 'refill_reminder' and form.action_taken.data == 'refill_scheduled':
            return redirect(url_for('medications.refill', medication_id=notification.medication_id))
        else:
            return redirect(url_for('notifications.index'))
    
    return render_template('notifications/action.html',
                         form=form,
                         notification=notification)

# ==================== Notification Preferences ====================

@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Manage notification preferences"""
    # Get or create user preferences
    preferences = NotificationPreference.query.filter_by(
        user_id=current_user.id
    ).first()
    
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    form = NotificationPreferenceForm(obj=preferences)
    
    # Get user's medications for medication-specific preferences
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    
    # Initialize medication preferences if empty
    if not form.medication_preferences.entries:
        for medication in medications:
            form.medication_preferences.append_entry({
                'medication_id': medication.id,
                'medication_name': medication.name,
                'enable_reminders': True,
                'custom_lead_time': None
            })
    
    if form.validate_on_submit():
        try:
            # Update basic preferences
            form.populate_obj(preferences)
            
            # Handle medication-specific preferences
            # (In a real app, you'd save these to a separate table)
            
            db.session.commit()
            flash('Notification preferences updated', 'success')
            return redirect(url_for('notifications.preferences'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating preferences: {e}')
            flash('Error updating preferences', 'error')
    
    return render_template('notifications/preferences.html',
                         form=form,
                         medications=medications,
                         preferences=preferences,
                         active_page='notifications')

@bp.route('/preferences/reset', methods=['POST'])
@login_required
def reset_preferences():
    """Reset notification preferences to defaults"""
    try:
        preferences = NotificationPreference.query.filter_by(
            user_id=current_user.id
        ).first()
        
        if preferences:
            # Delete existing preferences
            db.session.delete(preferences)
        
        # Create new default preferences
        default_preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(default_preferences)
        db.session.commit()
        
        flash('Notification preferences reset to defaults', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error resetting preferences: {e}')
        flash('Error resetting preferences', 'error')
    
    return redirect(url_for('notifications.preferences'))

# ==================== Custom Notifications ====================

@bp.route('/custom/new', methods=['GET', 'POST'])
@login_required
def create_custom():
    """Create a custom notification"""
    form = CustomNotificationForm()
    
    # Populate medication and prescription choices
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    form.medication_id.choices = [(0, 'None')] + [(m.id, m.name) for m in medications]
    
    prescriptions = Prescription.query.filter_by(user_id=current_user.id).all()
    form.prescription_id.choices = [(0, 'None')] + [(p.id, f"{p.medication.name} - {p.dosage}") for p in prescriptions]
    
    if form.validate_on_submit():
        try:
            # Prepare data for notification
            data = {}
            if form.custom_data.data:
                data = json.loads(form.custom_data.data)
            
            # Handle scheduling
            scheduled_time = None
            if not form.send_now.data and form.scheduled_time.data:
                scheduled_time = form.scheduled_time.data
            
            # Create notification
            notification = NotificationService.create_notification(
                user_id=current_user.id,
                title=form.title.data,
                message=form.message.data,
                notification_type=form.notification_type.data,
                priority=form.priority.data,
                medication_id=form.medication_id.data if form.medication_id.data != 0 else None,
                prescription_id=form.prescription_id.data if form.prescription_id.data != 0 else None,
                is_action_required=form.is_action_required.data,
                action_url=form.action_url.data,
                action_label=form.action_label.data,
                scheduled_time=scheduled_time,
                expires_at=form.expires_at.data,
                data=data
            )
            
            # Handle recurrence (simplified - in production, use a task queue)
            if form.repeat.data:
                # Store recurrence info in data
                notification.data['recurrence'] = {
                    'frequency': form.repeat_frequency.data,
                    'days': form.repeat_days.data,
                    'end_date': form.repeat_end_date.data.isoformat() if form.repeat_end_date.data else None,
                    'count': form.repeat_count.data
                }
                db.session.commit()
            
            flash('Custom notification created', 'success')
            return redirect(url_for('notifications.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating custom notification: {e}')
            flash('Error creating notification', 'error')
    
    return render_template('notifications/custom.html',
                         form=form,
                         active_page='notifications')

# ==================== Emergency Notifications ====================

@bp.route('/emergency', methods=['GET', 'POST'])
@login_required
def emergency():
    """Send emergency notification"""
    form = EmergencyNotificationForm()
    
    if form.validate_on_submit():
        try:
            # Create emergency notification for the user
            notification = NotificationService.create_notification(
                user_id=current_user.id,
                title=f'🚨 EMERGENCY: {form.emergency_type.data.replace("_", " ").title()}',
                message=form.description.data,
                notification_type='emergency',
                priority='urgent',
                is_action_required=True,
                action_url=url_for('notifications.emergency_details', emergency_id='temp'),
                data={
                    'emergency_type': form.emergency_type.data,
                    'severity': form.severity.data,
                    'symptoms': form.symptoms.data,
                    'timestamp': datetime.utcnow().isoformat(),
                    'location': form.current_location.data if form.share_location.data else None,
                    'notifications': {
                        'emergency_contacts': form.notify_emergency_contacts.data,
                        'healthcare_provider': form.notify_healthcare_provider.data,
                        'emergency_services': form.call_emergency_services.data
                    }
                }
            )
            
            # In production, you would:
            # 1. Send notifications to emergency contacts
            # 2. Contact healthcare provider if requested
            # 3. Log the emergency for follow-up
            # 4. Potentially call emergency services API
            
            flash('Emergency alert sent', 'success')
            return redirect(url_for('notifications.index'))
            
        except Exception as e:
            current_app.logger.error(f'Error sending emergency alert: {e}')
            flash('Error sending emergency alert', 'error')
    
    return render_template('notifications/emergency.html',
                         form=form,
                         active_page='notifications')

@bp.route('/emergency/<emergency_id>')
@login_required
def emergency_details(emergency_id):
    """View emergency details"""
    # This would typically fetch emergency details from database
    return render_template('notifications/emergency_details.html',
                         emergency_id=emergency_id)

# ==================== Testing & Debugging ====================

@bp.route('/test', methods=['GET', 'POST'])
@login_required
def test_notifications():
    """Test notification settings"""
    form = TestNotificationForm()
    
    # Populate medication choices
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    form.medication_id.choices = [(0, 'None')] + [(m.id, m.name) for m in medications]
    
    if form.validate_on_submit():
        try:
            # Determine notification content based on test type
            if form.test_type.data == 'medication_reminder' and form.medication_id.data != 0:
                medication = Medication.query.get(form.medication_id.data)
                title = '💊 Test Medication Reminder'
                message = f"This is a test reminder for {medication.name}"
                notification_type = 'medication_reminder'
                priority = 'medium'
            elif form.test_type.data == 'custom' and form.custom_title.data and form.custom_message.data:
                title = form.custom_title.data
                message = form.custom_message.data
                notification_type = 'custom'
                priority = 'medium'
            else:
                # Default test notification
                title = '🔔 Test Notification'
                message = 'This is a test notification to verify your settings are working correctly.'
                notification_type = 'system'
                priority = 'low'
            
            # Create test notification
            notification = NotificationService.create_notification(
                user_id=current_user.id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                data={
                    'test_notification': True,
                    'test_type': form.test_type.data,
                    'delivery_methods': form.delivery_method.data,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # In production, you would send actual push/email/SMS notifications
            # based on the selected delivery methods
            
            flash('Test notification sent! Check your notifications list.', 'success')
            return redirect(url_for('notifications.index'))
            
        except Exception as e:
            current_app.logger.error(f'Error sending test notification: {e}')
            flash('Error sending test notification', 'error')
    
    return render_template('notifications/test.html',
                         form=form,
                         active_page='notifications')

# ==================== Statistics & Analytics ====================

@bp.route('/statistics', methods=['GET', 'POST'])
@login_required
def statistics():
    """View notification statistics"""
    form = NotificationStatisticsForm()
    
    # Default values
    today = datetime.utcnow()
    default_end = today
    default_start = today - timedelta(days=7)
    
    form.start_date.data = default_start.date()
    form.end_date.data = default_end.date()
    
    if form.validate_on_submit():
        # Use form data
        if form.period.data == 'custom':
            start_date = form.start_date.data
            end_date = form.end_date.data
        else:
            period_days = {
                'day': 1,
                'week': 7,
                'month': 30,
                'quarter': 90,
                'year': 365
            }
            end_date = today.date()
            start_date = (today - timedelta(days=period_days[form.period.data])).date()
    else:
        # Use defaults
        start_date = default_start.date()
        end_date = default_end.date()
    
    # Query notifications for the period
    notifications = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.created_at >= datetime.combine(start_date, datetime.min.time()),
        Notification.created_at <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    # Calculate statistics
    stats = {
        'total': len(notifications),
        'read': len([n for n in notifications if n.is_read]),
        'unread': len([n for n in notifications if not n.is_read]),
        'action_required': len([n for n in notifications if n.is_action_required]),
        'action_taken': len([n for n in notifications if n.action_taken]),
        'by_type': {},
        'by_priority': {},
        'by_day': {},
        'by_hour': {}
    }
    
    for notification in notifications:
        # Group by type
        if notification.type not in stats['by_type']:
            stats['by_type'][notification.type] = 0
        stats['by_type'][notification.type] += 1
        
        # Group by priority
        if notification.priority not in stats['by_priority']:
            stats['by_priority'][notification.priority] = 0
        stats['by_priority'][notification.priority] += 1
        
        # Group by day
        day = notification.created_at.strftime('%Y-%m-%d')
        if day not in stats['by_day']:
            stats['by_day'][day] = 0
        stats['by_day'][day] += 1
        
        # Group by hour
        hour = notification.created_at.strftime('%H:00')
        if hour not in stats['by_hour']:
            stats['by_hour'][hour] = 0
        stats['by_hour'][hour] += 1
    
    # Calculate percentages
    if stats['total'] > 0:
        stats['read_percentage'] = (stats['read'] / stats['total']) * 100
        stats['action_rate'] = (stats['action_taken'] / max(1, stats['action_required'])) * 100
    else:
        stats['read_percentage'] = 0
        stats['action_rate'] = 0
    
    # Prepare data for charts
    chart_data = {
        'type_labels': list(stats['by_type'].keys()),
        'type_data': list(stats['by_type'].values()),
        'priority_labels': list(stats['by_priority'].keys()),
        'priority_data': list(stats['by_priority'].values()),
        'day_labels': list(stats['by_day'].keys()),
        'day_data': list(stats['by_day'].values()),
        'hour_labels': list(stats['by_hour'].keys()),
        'hour_data': list(stats['by_hour'].values())
    }
    
    return render_template('notifications/statistics.html',
                         form=form,
                         stats=stats,
                         chart_data=chart_data,
                         start_date=start_date,
                         end_date=end_date,
                         active_page='notifications')

# ==================== Templates Management ====================

@bp.route('/templates')
@login_required
def templates():
    """View notification templates"""
    # In production, you would have a Template model
    # For now, we'll show a static list
    templates = [
        {'id': 1, 'name': 'Standard Medication Reminder', 'type': 'medication_reminder', 'is_active': True},
        {'id': 2, 'name': 'Refill Reminder', 'type': 'refill_reminder', 'is_active': True},
        {'id': 3, 'name': 'Missed Dose Alert', 'type': 'missed_dose', 'is_active': True},
        {'id': 4, 'name': 'Daily Check-in', 'type': 'daily_checkin', 'is_active': True},
    ]
    
    return render_template('notifications/templates.html',
                         templates=templates,
                         active_page='notifications')

@bp.route('/templates/new', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create a notification template"""
    form = NotificationTemplateForm()
    
    # Set available variables based on template type
    if form.template_type.data == 'medication_reminder':
        form.available_variables.data = '{medication_name}, {dosage}, {time}, {frequency}, {next_dose}, {adherence_rate}'
    elif form.template_type.data == 'refill_reminder':
        form.available_variables.data = '{medication_name}, {remaining_days}, {pharmacy_name}, {refill_date}'
    else:
        form.available_variables.data = '{user_name}, {date}, {time}'
    
    if form.validate_on_submit():
        # In production, save to Template model
        flash('Template created successfully', 'success')
        return redirect(url_for('notifications.templates'))
    
    return render_template('notifications/template_form.html',
                         form=form,
                         title='Create Template',
                         active_page='notifications')

# ==================== Background Tasks ====================

@bp.route('/check-reminders')
@login_required
def check_reminders():
    """Manual trigger for checking reminders (admin/debug)"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('notifications.index'))
    
    try:
        medication_reminders = NotificationService.check_and_create_medication_reminders()
        refill_reminders = NotificationService.check_and_create_refill_reminders()
        
        flash(f'Created {medication_reminders} medication reminders and {refill_reminders} refill reminders', 'success')
    except Exception as e:
        current_app.logger.error(f'Error checking reminders: {e}')
        flash('Error checking reminders', 'error')
    
    return redirect(url_for('notifications.index'))

@bp.route('/daily-checkin-reminder')
@login_required
def daily_checkin_reminder():
    """Create daily check-in reminder"""
    success = NotificationService.create_daily_checkin_reminder(current_user.id)
    
    if success:
        flash('Daily check-in reminder created', 'success')
    else:
        flash('Daily check-in already completed or reminder already sent', 'info')
    
    return redirect(url_for('notifications.index'))

# ==================== Bulk Operations ====================

@bp.route('/bulk/delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple notifications"""
    notification_ids = request.form.getlist('notification_ids')
    
    if not notification_ids:
        flash('No notifications selected', 'error')
        return redirect(request.referrer or url_for('notifications.index'))
    
    try:
        deleted_count = 0
        for notification_id in notification_ids:
            success = NotificationService.delete_notification(
                int(notification_id), current_user.id
            )
            if success:
                deleted_count += 1
        
        flash(f'{deleted_count} notifications deleted', 'success')
    except Exception as e:
        current_app.logger.error(f'Error in bulk delete: {e}')
        flash('Error deleting notifications', 'error')
    
    return redirect(url_for('notifications.index'))

@bp.route('/bulk/mark-read', methods=['POST'])
@login_required
def bulk_mark_read():
    """Mark multiple notifications as read"""
    notification_ids = request.form.getlist('notification_ids')
    
    if not notification_ids:
        flash('No notifications selected', 'error')
        return redirect(request.referrer or url_for('notifications.index'))
    
    try:
        read_count = 0
        for notification_id in notification_ids:
            notification = Notification.query.filter_by(
                id=int(notification_id),
                user_id=current_user.id
            ).first()
            
            if notification and not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                read_count += 1
        
        if read_count > 0:
            db.session.commit()
            # Clear cache
            from app.utils.cache_service import cache
            cache.delete(f'notifications_{current_user.id}')
        
        flash(f'{read_count} notifications marked as read', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in bulk mark read: {e}')
        flash('Error marking notifications as read', 'error')
    
    return redirect(url_for('notifications.index'))

# ==================== Export Functionality ====================

@bp.route('/export')
@login_required
def export_notifications():
    """Export notifications to CSV/JSON"""
    format_type = request.args.get('format', 'json')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Notification.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Notification.created_at <= datetime.fromisoformat(end_date))
    
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    if format_type == 'csv':
        import csv
        from io import StringIO
        from flask import make_response
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Type', 'Title', 'Message', 'Priority', 'Read', 'Action Required',
                        'Action Taken', 'Created At', 'Read At', 'Expires At'])
        
        # Write data
        for notification in notifications:
            writer.writerow([
                notification.id,
                notification.type,
                notification.title,
                notification.message,
                notification.priority,
                notification.is_read,
                notification.is_action_required,
                notification.action_taken,
                notification.created_at.isoformat() if notification.created_at else '',
                notification.read_at.isoformat() if notification.read_at else '',
                notification.expires_at.isoformat() if notification.expires_at else ''
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=notifications_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        return response
    
    else:  # JSON format
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'is_action_required': notification.is_action_required,
                'action_taken': notification.action_taken,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                'data': notification.data
            })
        
        return jsonify({
            'success': True,
            'count': len(notifications_data),
            'exported_at': datetime.utcnow().isoformat(),
            'notifications': notifications_data
        })

# ==================== Badge Count API ====================

@bp.route('/api/badge-count')
@login_required
def badge_count():
    """API endpoint for getting unread notification count (for mobile badge)"""
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    action_required_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_action_required=True,
        action_taken=False
    ).count()
    
    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'action_required_count': action_required_count,
        'total_count': unread_count + action_required_count
    })

# ==================== WebSocket/Real-time Updates ====================

@bp.route('/api/stream')
@login_required
def notification_stream():
    """SSE endpoint for real-time notification updates"""
    # This is a simplified version. In production, Ill use:
    # - Redis Pub/Sub
    # - WebSockets
    # - Server-Sent Events (SSE)
    
    def generate():
        # Send initial count
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        yield f"data: {json.dumps({'type': 'count', 'unread_count': unread_count})}\n\n"
        
        # In production,  subscribe to a channel and yield updates
        # For now, we'll just return the initial count
        yield "data: {}\n\n"
    
    from flask import Response
    return Response(generate(), mimetype='text/event-stream')v