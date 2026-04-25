import os
import sys
import json

# Ensure project root is importable
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from app import create_app
from app.models import db, Sensor, BatteryStatus

APP = create_app()

with APP.app_context():
    cred_path = os.environ.get('SENSOR_CREDENTIALS_FILE') or os.path.join(os.path.dirname(__file__), '..', 'ingestion_worker', 'credentials.json')
    cred_path = os.path.abspath(cred_path)
    if not os.path.exists(cred_path):
        print('Credentials file not found:', cred_path)
        sys.exit(1)

    with open(cred_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)

    # Remove existing sensors (per user request: remove current and add real ones)
    print('Deleting existing sensors...')
    Sensor.query.delete()
    BatteryStatus.query.delete()
    db.session.commit()

    created = 0
    for app_id, cfg in creds.items():
        if app_id == 'default':
            continue
        # Determine sensor type from known app ids
        if 'bodenfeuchte' in app_id:
            s_type = 'moisture'
            name = 'Bodenfeuchte (Moisture Sensors)'
        elif 'rain' in app_id:
            s_type = 'rain'
            name = 'Regen (Rain Sensors)'
        elif 'smart' in app_id:
            s_type = 'smart_wall'
            name = 'Smart Wall'
        else:
            s_type = 'unknown'
            name = app_id

        unique_id = app_id
        sensor = Sensor(
            unique_id=unique_id,
            name=name,
            sensor_type=s_type,
            location='LoRaWAN Application',
            lorawan_application_id=app_id,
        )
        db.session.add(sensor)
        db.session.flush()
        # Add an empty battery status placeholder
        battery = BatteryStatus(sensor_id=sensor.id, battery_percentage=None)
        db.session.add(battery)
        created += 1

    db.session.commit()
    print(f'Created {created} sensors from credentials file.')
