import os
import sys

# Ensure project root is on sys.path so we can import the `app` package when
# running this script directly from the scripts/ directory.
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from app import create_app
from app.models import db, User, Sensor, BatteryStatus

app = create_app()

with app.app_context():
    print('Ensuring database tables exist...')
    db.create_all()

    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Admin user already exists.')
    else:
        admin = User(username='admin', email='admin@smartcity.local')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: admin / admin123')

    # Create sample sensors if none exist
    if Sensor.query.count() == 0:
        sensors = [
            {
                'unique_id': 'env_001',
                'name': 'Environmental Monitor - City Center',
                'sensor_type': 'environmental',
                'location': 'Marktplatz Aalen',
                'latitude': 48.84,
                'longitude': 10.0,
                'lorawan_dev_eui': 'A81234000000001',
                'battery_type': 'AA 2000mAh',
                'battery_voltage_min': 0.9,
                'battery_voltage_max': 1.5,
            },
            {
                'unique_id': 'parking_001',
                'name': 'Parking Sensor - Zone A',
                'sensor_type': 'parking',
                'location': 'Parking Zone A',
                'latitude': 48.8405,
                'longitude': 10.0005,
                'lorawan_dev_eui': 'A81234000000002',
                'battery_type': 'Solar + Battery',
            },
            {
                'unique_id': 'air_001',
                'name': 'Air Quality Monitor',
                'sensor_type': 'air_quality',
                'location': 'Industrial Area',
                'latitude': 48.8410,
                'longitude': 10.0010,
                'lorawan_dev_eui': 'A81234000000003',
                'battery_type': 'Li-Ion 5000mAh',
            },
        ]
        for s in sensors:
            if Sensor.query.filter_by(unique_id=s['unique_id']).first():
                continue
            sensor = Sensor(**s)
            db.session.add(sensor)
            battery = BatteryStatus(sensor=sensor, battery_percentage=85.0)
            db.session.add(battery)
        db.session.commit()
        print(f'Created {len(sensors)} sample sensors.')
    else:
        print('Sample sensors already present.')
