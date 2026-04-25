from flask import Flask
from app.models import db
from app.config import DevelopmentConfig
import os


def create_app(config_class=DevelopmentConfig):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes import auth_bp, sensor_bp, dashboard_bp, api_bp
    from app.routes.applications import apps_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(sensor_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(apps_bp)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def register_cli_commands(app):
    """Register CLI commands."""
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized.')
    
    @app.cli.command()
    def create_admin():
        """Create default admin user."""
        from app.models import User, db
        
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Admin user already exists.')
            return
        
        admin = User(username='admin', email='admin@smartcity.local')
        admin.set_password('admin123')  # Change in production!
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: admin / admin123')
    
    @app.cli.command()
    def create_sample_sensors():
        """Create sample sensor data."""
        from app.models import Sensor, BatteryStatus, db
        
        sensors = [
            {
                'unique_id': 'env_001',
                'name': 'Environmental Monitor - City Center',
                'sensor_type': 'environmental',
                'location': 'Marktplatz Aalen',
                'latitude': 48.8400,
                'longitude': 10.0000,
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
        
        for sensor_data in sensors:
            if Sensor.query.filter_by(unique_id=sensor_data['unique_id']).first():
                continue
            
            sensor = Sensor(**sensor_data)
            battery = BatteryStatus(sensor=sensor, battery_percentage=85.0)
            
            db.session.add(sensor)
            db.session.add(battery)
        
        db.session.commit()
        print(f'Created {len(sensors)} sample sensors.')
