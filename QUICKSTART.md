# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
flask --app app init-db
flask --app app create-admin
flask --app app create-sample-sensors
```

### 3. Run Application
```bash
python run.py
```

### 4. Access Dashboard
Open browser → `http://localhost:5000`
- **Username**: `admin`
- **Password**: `admin123`

---

## Testing Data Flow

### Manual Sensor Data Ingestion

```bash
curl -X POST http://localhost:5000/api/sensor-data/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "env_001",
    "timestamp": "2025-04-24T10:30:00Z",
    "data": [
      {"parameter": "temperature", "value": 25.5, "unit": "°C"},
      {"parameter": "humidity", "value": 65, "unit": "%"}
    ],
    "signal": {"rssi": -95, "snr": 8.5},
    "battery": {"percentage": 85}
  }'
```

### Check Sensor Status
```bash
curl http://localhost:5000/api/sensors/1/status
```

### Get Sensor Data
```bash
curl http://localhost:5000/api/sensors/1/data
```

---

## Running MQTT Ingestion Worker

### Configure TTI Credentials
Create `.env`:
```env
MQTT_BROKER=au1.cloud.thethings.industries
MQTT_PORT=8883
MQTT_USERNAME=my-app@ttn
MQTT_PASSWORD=your-api-key
API_ENDPOINT=http://localhost:5000/api/sensor-data/ingest
```

### Start Worker
```bash
python -m ingestion_worker.mqtt_client
```

Expected output:
```
INFO - Starting MQTT client...
INFO - Broker: au1.cloud.thethings.industries:8883
INFO - Connected to MQTT broker
INFO - Subscribed to topic: v3/+/as/up/+/+
INFO - MQTT client running. Press Ctrl+C to stop.
```

---

## Exploring the Dashboard

### Dashboard View
Shows real-time metrics:
- Total sensors online/offline
- Battery status overview
- Active alerts

### Add a Sensor
1. Click "Sensors" → "Add Sensor"
2. Fill in details:
   - Unique ID: `parking_001`
   - Name: "Parking Sensor A"
   - Type: "parking"
   - Location: "Zone A"
3. Save

### View Sensor Details
Click sensor name to see:
- Latest readings
- Battery status
- Active alerts
- Maintenance history
- Signal quality

### Manage Alerts
1. Go to "Alerts"
2. See all active alerts
3. Click "Resolve" to close

---

## Database Inspection

### Flask Shell
```bash
flask shell
```

### Query Examples
```python
from app.models import Sensor, Alert, SensorData

# Get all sensors
sensors = Sensor.query.all()

# Get online sensors
online = Sensor.query.join(Sensor.battery_status).filter(...)

# Get recent alerts
alerts = Alert.query.filter_by(status='active').order_by(Alert.created_at.desc()).all()

# Get sensor readings
readings = SensorData.query.filter_by(sensor_id=1).order_by(SensorData.timestamp.desc()).limit(10).all()
```

---

## Common Tasks

### Change Admin Password
```python
flask shell
>>> from app.models import User
>>> user = User.query.filter_by(username='admin').first()
>>> user.set_password('new_password')
>>> db.session.commit()
```

### Delete a Sensor
```python
flask shell
>>> from app.models import Sensor
>>> sensor = Sensor.query.filter_by(unique_id='env_001').first()
>>> db.session.delete(sensor)
>>> db.session.commit()
```

### Check Alerts
```python
flask shell
>>> from app.models import Alert
>>> Alert.query.filter_by(status='active').all()
```

### Clear Old Data
```python
flask shell
>>> from app.models import SensorData
>>> from datetime import datetime, timedelta
>>> cutoff = datetime.utcnow() - timedelta(days=30)
>>> SensorData.query.filter(SensorData.timestamp < cutoff).delete()
>>> db.session.commit()
```

---

## Troubleshooting

### "Failed to connect to database"
- Ensure SQLite file is writable
- Check database path in config
- Reset database: `rm iot_sensors.db && flask --app app init-db`

### "ImportError: No module named flask"
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### "Address already in use"
- Flask is already running on port 5000
- Kill process: `lsof -i :5000` (macOS/Linux)
- Use different port: `python run.py --port 5001`

### MQTT Not Connecting
- Check credentials in .env
- Verify firewall allows port 8883
- Test: `mosquitto_sub -h broker -t topic -u user -P pass`

---

## Next Steps

1. **Configure MQTT**: Set up TTI credentials
2. **Add Real Sensors**: Register devices in TTI console
3. **Deploy**: Follow production setup in CONFIG.md
4. **Monitor**: Set up logging and alerts
5. **Extend**: Add custom sensor types or notifications

---

For detailed documentation, see [README.md](README.md) and [CONFIG.md](CONFIG.md)
