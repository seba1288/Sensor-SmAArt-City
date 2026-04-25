"""
Database utilities for maintenance and backup.
"""

import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import SensorData, Alert


def cleanup_old_data(days_to_keep=30):
    """Remove sensor data older than specified days."""
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = SensorData.query.filter(SensorData.timestamp < cutoff).delete()
        db.session.commit()
        print(f"Deleted {deleted} records older than {days_to_keep} days")


def resolve_old_alerts(days_old=7):
    """Auto-resolve alerts older than specified days."""
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        resolved = Alert.query.filter(
            Alert.status == 'active',
            Alert.created_at < cutoff
        ).update({'status': 'resolved', 'resolved_at': datetime.utcnow()})
        db.session.commit()
        print(f"Auto-resolved {resolved} old alerts")


def compact_database():
    """Run VACUUM on SQLite to reclaim space."""
    app = create_app()
    with app.app_context():
        from sqlalchemy import text
        db.session.execute(text("VACUUM"))
        print("Database compacted")


def export_sensor_data(sensor_id, start_date, end_date, filename):
    """Export sensor data to CSV."""
    import csv
    from app.models import SensorData
    
    app = create_app()
    with app.app_context():
        data = SensorData.query.filter(
            SensorData.sensor_id == sensor_id,
            SensorData.timestamp >= start_date,
            SensorData.timestamp <= end_date
        ).order_by(SensorData.timestamp.asc()).all()
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Parameter', 'Value', 'Unit', 'RSSI', 'SNR'])
            for d in data:
                writer.writerow([
                    d.timestamp.isoformat(),
                    d.parameter,
                    d.value,
                    d.unit,
                    d.rssi,
                    d.snr,
                ])
        
        print(f"Exported {len(data)} records to {filename}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python db_utils.py [cleanup|resolve_alerts|compact|export]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        cleanup_old_data(days)
    elif command == 'resolve_alerts':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        resolve_old_alerts(days)
    elif command == 'compact':
        compact_database()
    elif command == 'export':
        sensor_id = int(sys.argv[2])
        start = sys.argv[3]
        end = sys.argv[4]
        filename = sys.argv[5] if len(sys.argv) > 5 else f'sensor_{sensor_id}_export.csv'
        export_sensor_data(sensor_id, start, end, filename)
    else:
        print(f"Unknown command: {command}")
