from app.models import db
from datetime import datetime


class BatteryStatus(db.Model):
    __tablename__ = 'battery_status'

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False, unique=True, index=True)
    
    # Battery data
    battery_percentage = db.Column(db.Float)  # 0-100, if available
    battery_voltage = db.Column(db.Float)  # in Volts
    battery_current = db.Column(db.Float)  # in mA, if available
    
    # Estimation method tracking
    estimation_method = db.Column(db.String(50))  # 'percentage', 'voltage', 'estimated'
    
    # Predictions and analysis
    estimated_remaining_days = db.Column(db.Float)  # Based on consumption patterns
    last_seen = db.Column(db.DateTime, index=True)  # Last data point from sensor
    
    # Alert tracking
    is_low_battery = db.Column(db.Boolean, default=False)
    low_battery_threshold = db.Column(db.Float, default=20.0)  # Default 20%
    
    # History
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BatteryStatus sensor_id={self.sensor_id} battery={self.battery_percentage}%>'

    def get_battery_percentage(self):
        """Get effective battery percentage."""
        return self.battery_percentage or 0

    def is_battery_low(self):
        """Check if battery is low."""
        return self.battery_percentage is not None and self.battery_percentage < self.low_battery_threshold
