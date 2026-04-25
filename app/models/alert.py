from app.models import db
from datetime import datetime


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False, index=True)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # 'offline', 'low_battery', 'weak_signal', 'anomaly'
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high'
    message = db.Column(db.String(500), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), default='active')  # 'active', 'resolved', 'acknowledged'
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)
    acknowledged_at = db.Column(db.DateTime)
    
    # Root cause analysis
    root_cause = db.Column(db.String(50))  # 'device_failure', 'network_issue', 'gateway_issue', 'unknown'
    alert_metadata = db.Column(db.JSON)  # Additional context

    def __repr__(self):
        return f'<Alert {self.alert_type} sensor_id={self.sensor_id} severity={self.severity}>'

    def resolve(self):
        """Mark alert as resolved."""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()

    def acknowledge(self):
        """Mark alert as acknowledged."""
        self.status = 'acknowledged'
        self.acknowledged_at = datetime.utcnow()

    def get_severity_color(self):
        """Return bootstrap color for severity."""
        colors = {
            'low': 'warning',
            'medium': 'warning',
            'high': 'danger'
        }
        return colors.get(self.severity, 'secondary')
