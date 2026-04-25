"""
API routes for MQTT ingestion and external integrations.
"""

from flask import Blueprint, request, jsonify, current_app
from app.models import Sensor, SensorData, BatteryStatus, db
from app.services import SensorService, BatteryService, AlertService
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/sensor-data/ingest', methods=['POST','GET'])
def ingest_sensor_data():
    """Ingest sensor data from MQTT or external sources.
    
    Expected JSON:
    {
        "device_id": "unique_id",
        "timestamp": "ISO8601 string",
        "data": [
            {"parameter": "temperature", "value": 25.5, "unit": "°C"},
            {"parameter": "humidity", "value": 65, "unit": "%"}
        ],
        "signal": {"rssi": -95, "snr": 8.5},
        "battery": {"percentage": 85, "voltage": 3.8}
    }
    """
    try:
        if request.method == 'GET':
            return jsonify({'message': 'POST JSON payload to this endpoint to ingest sensor data.'}), 200
        payload = request.get_json()
        
        # Find sensor; if not found, auto-create it from incoming metadata
        device_id = payload.get('device_id')
        dev_eui = payload.get('dev_eui')
        application_id = payload.get('application_id')

        sensor = SensorService.get_sensor_by_unique_id(device_id)
        # If no sensor found by unique_id, try to find by lorawan_dev_eui
        if not sensor and dev_eui:
            sensor = Sensor.query.filter_by(lorawan_dev_eui=dev_eui).first()
        if not sensor:
            # Infer sensor type from payload data parameters
            def infer_sensor_type(data_list):
                if not data_list:
                    return 'unknown'
                keys = {d.get('parameter', '').lower() for d in data_list}
                if keys & {'temperature', 'temp', 'humidity', 'hum'}:
                    return 'environmental'
                if keys & {'pm2.5', 'pm25', 'pm10', 'co2', 'no2'}:
                    return 'air_quality'
                if keys & {'available_parking', 'available_spaces', 'occupancy'}:
                    return 'parking'
                if keys & {'rain', 'rainfall'}:
                    return 'weather'
                return 'unknown'

            sensor_type = infer_sensor_type(payload.get('data', []))
            # Friendly name and location based on application and device
            name = f"{application_id or 'app'}:{device_id or dev_eui or 'device'}"
            location = f'Application: {application_id}' if application_id else 'auto-created'

            # Auto-create sensor record
            sensor = Sensor(
                unique_id=device_id,
                name=name,
                sensor_type=sensor_type,
                location=location,
                lorawan_dev_eui=dev_eui,
                lorawan_application_id=application_id,
            )
            db.session.add(sensor)
            db.session.flush()
            # create battery placeholder
            battery = BatteryStatus(sensor_id=sensor.id, battery_percentage=None)
            db.session.add(battery)
            db.session.commit()
            current_app.logger.info(f'Auto-created sensor {sensor.unique_id} (type={sensor.sensor_type})')
        
        # Parse timestamp
        timestamp = payload.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            timestamp = datetime.utcnow()
        
        # Store sensor data readings
        for reading in payload.get('data', []):
            data_point = SensorData(
                sensor_id=sensor.id,
                parameter=reading.get('parameter'),
                value=reading.get('value'),
                unit=reading.get('unit'),
                rssi=payload.get('signal', {}).get('rssi'),
                snr=payload.get('signal', {}).get('snr'),
                timestamp=timestamp,
                raw_payload=payload,
            )
            db.session.add(data_point)
        
        # Update battery status
        battery_data = {
            'battery_percentage': payload.get('battery', {}).get('percentage'),
            'battery_voltage': payload.get('battery', {}).get('voltage'),
            'last_seen': timestamp,
        }
        BatteryService.update_battery_status(sensor.id, battery_data)
        
        db.session.commit()
        
        # Run alert checks
        AlertService.check_offline_sensors()
        AlertService.check_low_battery()
        AlertService.check_weak_signal()
        
        return jsonify({
            'success': True,
            'message': 'Data ingested successfully',
            'sensor_id': sensor.id
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sensors/<int:sensor_id>/data', methods=['GET'])
def get_sensor_data(sensor_id):
    """Get sensor data for a time range."""
    start = request.args.get('start')
    end = request.args.get('end')
    parameter = request.args.get('parameter')
    
    sensor = Sensor.query.get_or_404(sensor_id)
    
    query = SensorData.query.filter_by(sensor_id=sensor_id)
    
    if parameter:
        query = query.filter_by(parameter=parameter)
    
    if start:
        query = query.filter(SensorData.timestamp >= datetime.fromisoformat(start))
    
    if end:
        query = query.filter(SensorData.timestamp <= datetime.fromisoformat(end))
    
    data = query.order_by(SensorData.timestamp.asc()).all()
    
    return jsonify({
        'sensor_id': sensor_id,
        'sensor_name': sensor.name,
        'data': [
            {
                'parameter': d.parameter,
                'value': d.value,
                'unit': d.unit,
                'timestamp': d.timestamp.isoformat(),
                'rssi': d.rssi,
                'snr': d.snr,
                'signal_quality': d.get_signal_quality(),
            } for d in data
        ]
    })


@api_bp.route('/sensors/<int:sensor_id>/status', methods=['GET'])
def get_sensor_status(sensor_id):
    """Get current sensor status."""
    sensor = Sensor.query.get_or_404(sensor_id)
    battery = sensor.battery_status
    
    return jsonify({
        'sensor_id': sensor.id,
        'name': sensor.name,
        'online': sensor.is_online(),
        'battery_percentage': battery.battery_percentage if battery else None,
        'last_seen': battery.last_seen.isoformat() if battery and battery.last_seen else None,
    })


@api_bp.route('/applications', methods=['GET'])
def list_applications():
    """Return a list of LoRaWAN applications and their sensors with latest readings."""
    apps = {}
    sensors = Sensor.query.all()
    for s in sensors:
        app_id = s.lorawan_application_id or 'unknown'
        if app_id not in apps:
            apps[app_id] = {
                'application_id': app_id,
                'sensors': []
            }

        latest = SensorData.query.filter_by(sensor_id=s.id).order_by(SensorData.timestamp.desc()).first()
        latest_obj = None
        if latest:
            latest_obj = {
                'parameter': latest.parameter,
                'value': latest.value,
                'unit': latest.unit,
                'timestamp': latest.timestamp.isoformat(),
                'rssi': latest.rssi,
                'snr': latest.snr,
            }

        apps[app_id]['sensors'].append({
            'sensor_id': s.id,
            'unique_id': s.unique_id,
            'name': s.name,
            'type': s.sensor_type,
            'location': s.location,
            'last_reading': latest_obj,
        })

    return jsonify(list(apps.values())), 200
