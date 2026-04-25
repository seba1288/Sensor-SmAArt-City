"""
Business logic services for IoT platform.
"""

from app.models import db, Alert, Sensor, BatteryStatus, SensorData
from datetime import datetime, timedelta


class AlertService:
    """Handle alert detection and management."""

    @staticmethod
    def check_offline_sensors(threshold_minutes=15):
        """Detect offline sensors and create alerts."""
        from app.models import Sensor, Alert
        
        threshold = datetime.utcnow() - timedelta(minutes=threshold_minutes)
        offline_sensors = db.session.query(Sensor).join(BatteryStatus).filter(
            BatteryStatus.last_seen < threshold
        ).all()
        
        for sensor in offline_sensors:
            existing_alert = Alert.query.filter_by(
                sensor_id=sensor.id,
                alert_type='offline',
                status='active'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    sensor_id=sensor.id,
                    alert_type='offline',
                    severity='high',
                    message=f'Sensor "{sensor.name}" has not reported data for {threshold_minutes} minutes.',
                    root_cause='unknown'
                )
                db.session.add(alert)
        
        db.session.commit()

    @staticmethod
    def check_low_battery():
        """Detect low battery sensors and create alerts."""
        from app.models import BatteryStatus, Alert
        
        low_battery = BatteryStatus.query.filter(
            BatteryStatus.battery_percentage < BatteryStatus.low_battery_threshold,
            BatteryStatus.battery_percentage.isnot(None)
        ).all()
        
        for battery in low_battery:
            existing_alert = Alert.query.filter_by(
                sensor_id=battery.sensor_id,
                alert_type='low_battery',
                status='active'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    sensor_id=battery.sensor_id,
                    alert_type='low_battery',
                    severity='medium',
                    message=f'Battery level is {battery.battery_percentage}%.',
                    root_cause='device_failure'
                )
                db.session.add(alert)
            
            battery.is_low_battery = True
        
        db.session.commit()

    @staticmethod
    def check_weak_signal(rssi_threshold=-100):
        """Detect weak signal and create alerts."""
        from app.models import SensorData, Alert
        
        # Get latest data points for each sensor
        subquery = db.session.query(
            SensorData.sensor_id,
            db.func.max(SensorData.id).label('max_id')
        ).group_by(SensorData.sensor_id).subquery()
        
        weak_signals = db.session.query(SensorData).join(
            subquery,
            (SensorData.id == subquery.c.max_id)
        ).filter(SensorData.rssi < rssi_threshold).all()
        
        for data in weak_signals:
            existing_alert = Alert.query.filter_by(
                sensor_id=data.sensor_id,
                alert_type='weak_signal',
                status='active'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    sensor_id=data.sensor_id,
                    alert_type='weak_signal',
                    severity='low',
                    message=f'Signal strength is weak (RSSI: {data.rssi} dBm).',
                    root_cause='network_issue',
                    alert_metadata={'rssi': data.rssi, 'snr': data.snr}
                )
                db.session.add(alert)
        
        db.session.commit()

    @staticmethod
    def get_active_alerts():
        """Get all active alerts."""
        return Alert.query.filter_by(status='active').order_by(Alert.created_at.desc()).all()

    @staticmethod
    def get_alerts_by_severity(severity):
        """Get alerts by severity."""
        return Alert.query.filter_by(status='active', severity=severity).order_by(
            Alert.created_at.desc()
        ).all()


class BatteryService:
    """Handle battery estimation and analysis."""

    @staticmethod
    def estimate_battery_percentage(voltage, sensor):
        """Estimate battery percentage from voltage."""
        if not voltage or not sensor.battery_voltage_min or not sensor.battery_voltage_max:
            return None
        
        # Linear interpolation
        min_v = sensor.battery_voltage_min
        max_v = sensor.battery_voltage_max
        
        if voltage <= min_v:
            return 0.0
        if voltage >= max_v:
            return 100.0
        
        percentage = ((voltage - min_v) / (max_v - min_v)) * 100
        return max(0, min(100, percentage))

    @staticmethod
    def update_battery_status(sensor_id, battery_data):
        """Update battery status with latest data."""
        battery = BatteryStatus.query.filter_by(sensor_id=sensor_id).first()
        
        if not battery:
            battery = BatteryStatus(sensor_id=sensor_id)
            db.session.add(battery)
        
        # Determine battery percentage
        if 'battery_percentage' in battery_data and battery_data['battery_percentage'] is not None:
            battery.battery_percentage = battery_data['battery_percentage']
            battery.estimation_method = 'percentage'
        elif 'battery_voltage' in battery_data and battery_data['battery_voltage'] is not None:
            sensor = Sensor.query.get(sensor_id)
            estimated_percent = BatteryService.estimate_battery_percentage(
                battery_data['battery_voltage'],
                sensor
            )
            battery.battery_percentage = estimated_percent
            battery.battery_voltage = battery_data['battery_voltage']
            battery.estimation_method = 'voltage'
        
        # Update tracking info
        if 'last_seen' in battery_data:
            battery.last_seen = battery_data['last_seen']
        
        battery.updated_at = datetime.utcnow()
        db.session.add(battery)
        db.session.commit()

    @staticmethod
    def estimate_remaining_days(sensor_id):
        """Estimate remaining battery days based on consumption."""
        battery = BatteryStatus.query.filter_by(sensor_id=sensor_id).first()
        if not battery or battery.battery_percentage is None:
            return None
        
        # Get last 7 days of data
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        data_points = SensorData.query.filter(
            SensorData.sensor_id == sensor_id,
            SensorData.timestamp >= seven_days_ago
        ).count()
        
        if data_points < 2:
            return None
        
        # Rough estimation: if battery is declining, estimate when it'll reach 10%
        # This is a simplified model
        current_battery = battery.battery_percentage
        if current_battery > 10:
            daily_drain = (current_battery - 10) / 7  # Rough average drain
            if daily_drain > 0:
                return (current_battery - 10) / daily_drain
        
        return None


class RootCauseService:
    """Analyze root cause of issues."""

    @staticmethod
    def analyze_sensor_issue(sensor_id):
        """Analyze why sensor is not reporting."""
        sensor = Sensor.query.get(sensor_id)
        if not sensor:
            return None
        
        root_cause = 'unknown'
        factors = {
            'device_failure': False,
            'network_issue': False,
            'gateway_issue': False,
        }
        
        # Check battery status
        battery = sensor.battery_status
        if battery and battery.battery_percentage is not None and battery.battery_percentage < 5:
            factors['device_failure'] = True
        
        # Check signal quality from last message
        last_data = SensorData.query.filter_by(sensor_id=sensor_id).order_by(
            SensorData.timestamp.desc()
        ).first()
        
        if last_data and last_data.rssi is not None:
            if last_data.rssi < -110:
                factors['network_issue'] = True
            elif last_data.snr is not None and last_data.snr < -5:
                factors['gateway_issue'] = True
        
        # Determine primary root cause
        if factors['device_failure']:
            root_cause = 'device_failure'
        elif factors['network_issue']:
            root_cause = 'network_issue'
        elif factors['gateway_issue']:
            root_cause = 'gateway_issue'
        
        return {
            'root_cause': root_cause,
            'factors': factors,
            'last_signal': last_data.rssi if last_data else None,
        }

    @staticmethod
    def get_nearby_sensors(sensor_id, radius_km=1.0):
        """Get nearby sensors to compare signal quality."""
        sensor = Sensor.query.get(sensor_id)
        if not sensor or not sensor.latitude or not sensor.longitude:
            return []
        
        # Simple distance calculation (in real world, use PostGIS or similar)
        nearby = Sensor.query.filter(
            Sensor.id != sensor_id,
            Sensor.latitude.isnot(None),
            Sensor.longitude.isnot(None),
        ).all()
        
        # Filter by rough distance (simplified)
        filtered = []
        for s in nearby:
            # Very rough distance: each degree ~ 111 km
            dist = abs(s.latitude - sensor.latitude) + abs(s.longitude - sensor.longitude)
            if dist < (radius_km / 111):
                filtered.append(s)
        
        return filtered


class SensorService:
    """Handle sensor CRUD operations."""

    @staticmethod
    def get_sensor_stats():
        """Get sensor statistics for dashboard."""
        total_sensors = Sensor.query.count()
        
        online_threshold = datetime.utcnow() - timedelta(minutes=15)
        online_sensors = db.session.query(Sensor).join(BatteryStatus).filter(
            BatteryStatus.last_seen >= online_threshold
        ).count()
        
        offline_sensors = total_sensors - online_sensors
        
        low_battery_sensors = db.session.query(Sensor).join(BatteryStatus).filter(
            BatteryStatus.battery_percentage < BatteryStatus.low_battery_threshold,
            BatteryStatus.battery_percentage.isnot(None)
        ).count()
        
        active_alerts = Alert.query.filter_by(status='active').count()
        
        return {
            'total_sensors': total_sensors,
            'online_sensors': online_sensors,
            'offline_sensors': offline_sensors,
            'low_battery_sensors': low_battery_sensors,
            'active_alerts': active_alerts,
        }

    @staticmethod
    def get_sensor_by_unique_id(unique_id):
        """Get sensor by unique ID."""
        return Sensor.query.filter_by(unique_id=unique_id).first()

    @staticmethod
    def get_sensor_latest_data(sensor_id, limit=10):
        """Get latest sensor readings."""
        return SensorData.query.filter_by(sensor_id=sensor_id).order_by(
            SensorData.timestamp.desc()
        ).limit(limit).all()

    @staticmethod
    def get_sensor_data_for_range(sensor_id, parameter, start_date, end_date):
        """Get sensor data for a specific parameter and date range."""
        return SensorData.query.filter(
            SensorData.sensor_id == sensor_id,
            SensorData.parameter == parameter,
            SensorData.timestamp >= start_date,
            SensorData.timestamp <= end_date
        ).order_by(SensorData.timestamp.asc()).all()

    @staticmethod
    def get_recent_messages(limit=25):
        """Return recent sensor data messages with sensor info."""
        results = db.session.query(SensorData, Sensor).join(Sensor, Sensor.id == SensorData.sensor_id).order_by(SensorData.timestamp.desc()).limit(limit).all()
        messages = []
        for sd, s in results:
            messages.append({
                'sensor_id': s.id,
                'sensor_name': s.name,
                'application_id': s.lorawan_application_id,
                'parameter': sd.parameter,
                'value': sd.value,
                'unit': sd.unit,
                'timestamp': sd.timestamp,
                'rssi': sd.rssi,
                'snr': sd.snr,
            })
        return messages

    @staticmethod
    def get_ingestion_stats(minutes=60):
        """Return count of messages per application in the last `minutes` minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        # join SensorData -> Sensor and group by lorawan_application_id
        rows = db.session.query(Sensor.lorawan_application_id, db.func.count(SensorData.id)).join(SensorData, Sensor.id == SensorData.sensor_id).filter(SensorData.timestamp >= cutoff).group_by(Sensor.lorawan_application_id).all()
        stats = {r[0] or 'unknown': r[1] for r in rows}
        return stats
