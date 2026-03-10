# app/medications/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Medication, Prescription, Dose, MedicationInventory
from app.utils.helpers import Helper
from app.utils.ai_service import AIService
from app.utils.notification_service import NotificationService
from .forms import MedicationForm, PrescriptionForm, DoseForm
from .services import MedicationService

medications_bp = Blueprint('medications', __name__)
medication_service = MedicationService()
ai_service = AIService()

@medications_bp.route('/')
@login_required
def index():
    """List all medications"""
    medications = Helper.get_user_medications(current_user.id)
    return render_template('medications/index.html', medications=medications)

@medications_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new medication"""
    form = MedicationForm()
    
    if form.validate_on_submit():
        try:
            medication = medication_service.create_medication(
                user_id=current_user.id,
                name=form.name.data,
                strength=form.strength.data,
                form=form.form.data,
                generic_name=form.generic_name.data,
                image_url=form.image_url.data
            )
            
            # Create initial prescription if provided
            if form.has_prescription.data:
                prescription = medication_service.create_prescription(
                    medication_id=medication.id,
                    dosage=form.dosage.data,
                    frequency=form.frequency.data,
                    start_date=form.start_date.data,
                    instructions=form.instructions.data
                )
                
                # Generate schedule
                medication_service.generate_schedule(prescription.id)
            
            flash('Medication added successfully', 'success')
            return redirect(url_for('medications.detail', id=medication.id))
        
        except Exception as e:
            flash(f'Error adding medication: {str(e)}', 'error')
    
    return render_template('medications/add.html', form=form)

@medications_bp.route('/<int:id>')
@login_required
def detail(id):
    """View medication details"""
    medication = Medication.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get AI summary
    summary = ai_service.generate_medication_summary({
        'name': medication.name,
        'strength': medication.strength,
        'form': medication.form
    })
    
    # Get upcoming doses
    upcoming_doses = Dose.query.join(Prescription).filter(
        Prescription.medication_id == id,
        Prescription.user_id == current_user.id,
        Dose.status == 'scheduled'
    ).order_by(Dose.scheduled_time).limit(5).all()
    
    return render_template('medications/detail.html',
                         medication=medication,
                         summary=summary,
                         upcoming_doses=upcoming_doses)

@medications_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit medication"""
    medication = Medication.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    form = MedicationForm(obj=medication)
    
    if form.validate_on_submit():
        try:
            medication_service.update_medication(
                medication_id=id,
                **form.data
            )
            flash('Medication updated successfully', 'success')
            return redirect(url_for('medications.detail', id=id))
        except Exception as e:
            flash(f'Error updating medication: {str(e)}', 'error')
    
    return render_template('medications/edit.html', form=form, medication=medication)

@medications_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete medication"""
    medication = Medication.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        db.session.delete(medication)
        db.session.commit()
        flash('Medication deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting medication: {str(e)}', 'error')
    
    return redirect(url_for('medications.index'))

@medications_bp.route('/<int:id>/take', methods=['POST'])
@login_required
def take_dose(id):
    """Mark dose as taken"""
    data = request.get_json()
    dose_id = data.get('dose_id')
    
    try:
        dose = Dose.query.join(Prescription).filter(
            Dose.id == dose_id,
            Prescription.user_id == current_user.id,
            Prescription.medication_id == id
        ).first_or_404()
        
        dose.status = 'taken'
        dose.actual_time = datetime.utcnow()
        dose.next_dose_time = medication_service.calculate_next_dose(dose)
        db.session.commit()
        
        # Create notification
        NotificationService.create_notification(
            user_id=current_user.id,
            title='✅ Dose Taken',
            message=f'You took {dose.prescription.medication.name}',
            notification_type='medication_taken',
            medication_id=id,
            data={'dose_id': dose_id}
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@medications_bp.route('/<int:id>/snooze', methods=['POST'])
@login_required
def snooze_dose(id):
    """Snooze a dose"""
    data = request.get_json()
    dose_id = data.get('dose_id')
    minutes = data.get('minutes', 10)
    
    try:
        dose = Dose.query.join(Prescription).filter(
            Dose.id == dose_id,
            Prescription.user_id == current_user.id,
            Prescription.medication_id == id
        ).first_or_404()
        
        dose.scheduled_time += timedelta(minutes=minutes)
        dose.snooze_count += 1
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@medications_bp.route('/api/upcoming')
@login_required
def api_upcoming():
    """API endpoint for upcoming doses"""
    hours = request.args.get('hours', 24, type=int)
    upcoming = Helper.get_upcoming_doses(current_user.id, hours)
    
    data = []
    for dose in upcoming:
        data.append({
            'id': dose.id,
            'medication': dose.prescription.medication.name,
            'scheduled_time': Helper.format_datetime(dose.scheduled_time),
            'relative_time': Helper.get_relative_time(dose.scheduled_time),
            'status': dose.status
        })
    
    return jsonify(data)

@medications_bp.route('/api/adherence')
@login_required
def api_adherence():
    """API endpoint for adherence data"""
    days = request.args.get('days', 30, type=int)
    rate = Helper.calculate_adherence_rate(current_user.id, days)
    
    return jsonify({
        'adherence_rate': rate,
        'period_days': days
    })