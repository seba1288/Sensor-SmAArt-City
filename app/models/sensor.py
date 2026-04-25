from app.models import db
from datetime import datetime


class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)  # e.g., 'environmental', 'parking', 'weather', 'air_quality'
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # LoRaWAN specific
    lorawan_dev_eui = db.Column(db.String(255), unique=True)
    lorawan_application_id = db.Column(db.String(255), index=True)
    communication = db.Column(db.String(50), default='LoRaWAN')
    
    # Battery info
    battery_type = db.Column(db.String(255))  # e.g., 'AA 2000mAh', '3.7V Li-Ion', 'Solar'
    battery_voltage_min = db.Column(db.Float)  # Minimum voltage for battery
    battery_voltage_max = db.Column(db.Float)  # Maximum voltage for battery
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sensor_data = db.relationship('SensorData', backref='sensor', lazy=True, cascade='all, delete-orphan')
    battery_status = db.relationship('BatteryStatus', backref='sensor', lazy=True, uselist=False, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='sensor', lazy=True, cascade='all, delete-orphan')
    maintenance_logs = db.relationship('MaintenanceLog', backref='sensor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sensor {self.name} ({self.unique_id})>'

    def is_online(self, threshold_minutes=15):
        """Check if sensor is online based on last seen timestamp."""
        if not self.battery_status or not self.battery_status.last_seen:
            return False
        from datetime import timedelta
        return (datetime.utcnow() - self.battery_status.last_seen) < timedelta(minutes=threshold_minutes)

    def get_status_badge(self):
        """Return status badge for UI."""
        if self.is_online():
            return 'online'
        return 'offline'
