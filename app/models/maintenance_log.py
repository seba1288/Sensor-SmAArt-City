from app.models import db
from datetime import datetime


class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False, index=True)
    
    # Maintenance details
    maintenance_type = db.Column(db.String(50), nullable=False)  # 'check', 'repair', 'battery_replacement', 'cleaning'
    comment = db.Column(db.Text)
    operator = db.Column(db.String(100))
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<MaintenanceLog sensor_id={self.sensor_id} type={self.maintenance_type} at {self.timestamp}>'
