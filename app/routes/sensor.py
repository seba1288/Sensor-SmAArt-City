"""
Sensor management routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Sensor, SensorData, BatteryStatus, MaintenanceLog, Alert, db
from app.routes.auth import login_required
from app.services import SensorService, BatteryService, RootCauseService
from datetime import datetime

sensor_bp = Blueprint('sensors', __name__, url_prefix='/sensors')


@sensor_bp.route('/', methods=['GET'])
@login_required
def list_sensors():
    """List all sensors."""
    page = request.args.get('page', 1, type=int)
    sensors = Sensor.query.paginate(page=page, per_page=20)
    return render_template('sensors/list.html', sensors=sensors)


@sensor_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_sensor():
    """Add a new sensor."""
    if request.method == 'POST':
        try:
            sensor = Sensor(
                unique_id=request.form.get('unique_id'),
                name=request.form.get('name'),
                sensor_type=request.form.get('sensor_type'),
                location=request.form.get('location'),
                latitude=float(request.form.get('latitude')) if request.form.get('latitude') else None,
                longitude=float(request.form.get('longitude')) if request.form.get('longitude') else None,
                lorawan_dev_eui=request.form.get('lorawan_dev_eui'),
                battery_type=request.form.get('battery_type'),
                battery_voltage_min=float(request.form.get('battery_voltage_min')) if request.form.get('battery_voltage_min') else None,
                battery_voltage_max=float(request.form.get('battery_voltage_max')) if request.form.get('battery_voltage_max') else None,
                notes=request.form.get('notes'),
            )
            
            battery = BatteryStatus(sensor=sensor, battery_percentage=100.0)
            
            db.session.add(sensor)
            db.session.add(battery)
            db.session.commit()
            
            flash(f'Sensor "{sensor.name}" added successfully.', 'success')
            return redirect(url_for('sensors.view_sensor', sensor_id=sensor.id))
        except Exception as e:
            flash(f'Error adding sensor: {str(e)}', 'danger')
    
    return render_template('sensors/add.html')


@sensor_bp.route('/<int:sensor_id>', methods=['GET'])
@login_required
def view_sensor(sensor_id):
    """View sensor details."""
    sensor = Sensor.query.get_or_404(sensor_id)
    latest_data = SensorService.get_sensor_latest_data(sensor_id, limit=20)
    battery = sensor.battery_status
    alerts = Alert.query.filter_by(sensor_id=sensor_id).order_by(Alert.created_at.desc()).limit(10).all()
    maintenance_logs = MaintenanceLog.query.filter_by(sensor_id=sensor_id).order_by(
        MaintenanceLog.timestamp.desc()
    ).limit(10).all()
    
    root_cause_analysis = RootCauseService.analyze_sensor_issue(sensor_id)
    
    return render_template(
        'sensors/detail.html',
        sensor=sensor,
        latest_data=latest_data,
        battery=battery,
        alerts=alerts,
        maintenance_logs=maintenance_logs,
        root_cause_analysis=root_cause_analysis,
    )


@sensor_bp.route('/<int:sensor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sensor(sensor_id):
    """Edit sensor details."""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    if request.method == 'POST':
        try:
            sensor.name = request.form.get('name')
            sensor.sensor_type = request.form.get('sensor_type')
            sensor.location = request.form.get('location')
            sensor.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
            sensor.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
            sensor.battery_type = request.form.get('battery_type')
            sensor.battery_voltage_min = float(request.form.get('battery_voltage_min')) if request.form.get('battery_voltage_min') else None
            sensor.battery_voltage_max = float(request.form.get('battery_voltage_max')) if request.form.get('battery_voltage_max') else None
            sensor.notes = request.form.get('notes')
            
            db.session.commit()
            flash(f'Sensor "{sensor.name}" updated successfully.', 'success')
            return redirect(url_for('sensors.view_sensor', sensor_id=sensor.id))
        except Exception as e:
            flash(f'Error updating sensor: {str(e)}', 'danger')
    
    return render_template('sensors/edit.html', sensor=sensor)


@sensor_bp.route('/<int:sensor_id>/delete', methods=['POST'])
@login_required
def delete_sensor(sensor_id):
    """Delete a sensor."""
    sensor = Sensor.query.get_or_404(sensor_id)
    sensor_name = sensor.name
    
    try:
        db.session.delete(sensor)
        db.session.commit()
        flash(f'Sensor "{sensor_name}" deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting sensor: {str(e)}', 'danger')
    
    return redirect(url_for('sensors.list_sensors'))


@sensor_bp.route('/<int:sensor_id>/maintenance', methods=['POST'])
@login_required
def log_maintenance(sensor_id):
    """Log maintenance activity."""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    try:
        maintenance = MaintenanceLog(
            sensor_id=sensor_id,
            maintenance_type=request.form.get('maintenance_type'),
            comment=request.form.get('comment'),
            operator=request.form.get('operator'),
        )
        db.session.add(maintenance)
        db.session.commit()
        flash('Maintenance log added successfully.', 'success')
    except Exception as e:
        flash(f'Error logging maintenance: {str(e)}', 'danger')
    
    return redirect(url_for('sensors.view_sensor', sensor_id=sensor_id))
