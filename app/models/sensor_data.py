from app.models import db
from datetime import datetime


class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    __table_args__ = (
        db.Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False, index=True)
    
    # Normalized data
    parameter = db.Column(db.String(100), nullable=False)  # e.g., 'temperature', 'humidity', 'co2', 'available_parking'
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))  # e.g., '°C', '%', 'ppm', 'count'
    
    # Signal quality
    rssi = db.Column(db.Integer)  # Received Signal Strength Indicator (typically -120 to -30 dBm)
    snr = db.Column(db.Float)  # Signal-to-Noise Ratio (typically -20 to 10 dB)
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    raw_payload = db.Column(db.JSON)  # Store original payload for debugging

    def __repr__(self):
        return f'<SensorData {self.parameter}={self.value}{self.unit} at {self.timestamp}>'

    def get_signal_quality(self):
        """Return signal quality as percentage (0-100)."""
        if self.rssi is None:
            return None
        # RSSI ranges from -120 (poor) to -30 (excellent)
        # Normalize to 0-100
        quality = min(100, max(0, (self.rssi + 120) * 100 / 90))
        return int(quality)
