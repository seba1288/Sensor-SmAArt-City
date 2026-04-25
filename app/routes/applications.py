"""Routes to display LoRaWAN applications and linked sensors."""

from flask import Blueprint, render_template
from app.models import Sensor, SensorData
from app.routes.auth import login_required

apps_bp = Blueprint('applications', __name__, url_prefix='/applications')


@apps_bp.route('/', methods=['GET'])
@login_required
def list_applications():
    # Group sensors by application id
    sensors = Sensor.query.all()
    apps = {}
    for s in sensors:
        app_id = s.lorawan_application_id or 'unknown'
        apps.setdefault(app_id, []).append(s)

    return render_template('applications/list.html', apps=apps)


@apps_bp.route('/<app_id>', methods=['GET'])
@login_required
def view_application(app_id):
    sensors = Sensor.query.filter_by(lorawan_application_id=app_id).all()
    # collect latest reading per sensor
    latest_map = {}
    for s in sensors:
        latest = SensorData.query.filter_by(sensor_id=s.id).order_by(SensorData.timestamp.desc()).first()
        latest_map[s.id] = latest

    return render_template('applications/view.html', app_id=app_id, sensors=sensors, latest_map=latest_map)
