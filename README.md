# IoT Sensor Monitoring and Management Platform
# Aalen Smart City

A complete web-based platform for monitoring and managing heterogeneous LoRaWAN sensors in a smart city environment.

## Features

### Core Capabilities
- **Sensor Management**: Add, edit, view, and manage IoT sensors
- **Real-time Monitoring**: Track sensor status, battery levels, and signal quality
- **Data Ingestion**: MQTT client for The Things Industries (TTI) integration
- **Alert System**: Automatic detection of offline sensors, low battery, and weak signals
- **Battery Monitoring**: Smart battery estimation from voltage or percentage data
- **Root Cause Analysis**: Intelligent diagnosis of sensor issues
- **Maintenance Logging**: Track maintenance activities and repairs
- **Dashboard**: Overview of system status with key metrics and alerts

### Supported Sensor Types
- Environmental (temperature, humidity, pressure)
- Parking (occupancy, available spaces)
- Weather (wind, rainfall)
- Air Quality (CO2, NO2, PM2.5, PM10)

## Architecture

### Technology Stack
- **Backend**: Python Flask
- **Database**: SQLite (easily migrate to PostgreSQL)
- **ORM**: SQLAlchemy
- **Frontend**: Jinja2 templates with Bootstrap 5
- **MQTT**: paho-mqtt for data ingestion
- **Data Format**: JSON normalization layer

### Components

```
Sensor-SmAArt-City/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py
│   │   ├── sensor.py
│   │   ├── sensor_data.py
│   │   ├── battery_status.py
│   │   ├── alert.py
│   │   └── maintenance_log.py
│   ├── services/             # Business logic
│   │   └── __init__.py       # Alert, Battery, RootCause, Sensor services
│   ├── routes/               # Flask blueprints
│   │   ├── auth.py           # Authentication
│   │   ├── sensor.py         # Sensor CRUD
│   │   ├── dashboard.py      # Dashboard & alerts
│   │   └── api.py            # JSON API for ingestion
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   └── sensors/
│   └── static/css/           # Stylesheets
├── ingestion_worker/
│   └── mqtt_client.py        # TTI MQTT ingestion
├── run.py                    # Entry point
└── requirements.txt
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone or create project directory**
```bash
cd Sensor-SmAArt-City
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize database and create admin user**
```bash
flask --app app init-db
flask --app app create-admin
flask --app app create-sample-sensors
```

Default credentials:
- Username: `admin`
- Password: `admin123`

**⚠️ Change this in production!**

5. **Run the application**
```bash
python run.py
```

Access at: `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///iot_sensors.db

# MQTT Configuration (The Things Industries)
MQTT_BROKER=au1.cloud.thethings.industries
MQTT_PORT=8883
MQTT_USERNAME=your-app-id@ttn
MQTT_PASSWORD=your-api-key

# API
API_ENDPOINT=http://localhost:5000/api/sensor-data/ingest
```

### Database Configuration

SQLite is default. To use PostgreSQL:

```python
# app/config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/iot_sensors'
```

Enable WAL mode for concurrent access:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {'timeout': 10},
    'journal_mode': 'WAL',
}
```

## Usage

### 1. Web Dashboard

**Login** → Default credentials above

**Dashboard** shows:
- Total sensors
- Online/offline status
- Low battery sensors
- Active alerts summary

### 2. Sensor Management

**Add Sensor**:
1. Click "Sensors" → "Add Sensor"
2. Enter sensor details (name, type, location, battery info)
3. Save

**View Sensor**:
1. Click sensor name
2. See real-time data, battery status, alerts
3. Log maintenance activities

### 3. MQTT Ingestion

Run the ingestion worker separately:

```bash
python -m ingestion_worker.mqtt_client
```

It will:
1. Connect to TTI MQTT broker
2. Subscribe to uplink topics
3. Normalize payloads
4. Send to Flask API
5. Trigger alert checks

### 4. Payload Normalization

The system handles various sensor formats:

**Input (TTI format)**:
```json
{
  "end_device_ids": {"device_id": "env_001"},
  "received_at": "2025-04-24T10:30:00Z",
  "uplink_message": {
    "decoded_payload": {
      "temperature": 25.5,
      "humidity": 65,
      "battery": 85
    },
    "rx_metadata": [{
      "rssi": -95,
      "snr": 8.5
    }]
  }
}
```

**Normalized (stored)**:
```json
{
  "device_id": "env_001",
  "timestamp": "2025-04-24T10:30:00Z",
  "data": [
    {"parameter": "temperature", "value": 25.5, "unit": "°C"},
    {"parameter": "humidity", "value": 65, "unit": "%"}
  ],
  "signal": {"rssi": -95, "snr": 8.5},
  "battery": {"percentage": 85}
}
```

### 5. Alert System

Alerts are automatically generated for:
- **Offline Sensors**: No data for 15 minutes (configurable)
- **Low Battery**: Below 20% (configurable)
- **Weak Signal**: RSSI < -100 dBm (configurable)

Each alert includes:
- Alert type and severity
- Root cause analysis
- Sensor metadata
- Resolution workflow

## API Endpoints

### Ingest Sensor Data
```
POST /api/sensor-data/ingest
Content-Type: application/json

{
  "device_id": "sensor_id",
  "timestamp": "2025-04-24T10:30:00Z",
  "data": [...],
  "signal": {"rssi": -95, "snr": 8.5},
  "battery": {"percentage": 85}
}
```

### Get Sensor Data
```
GET /api/sensors/<sensor_id>/data?start=...&end=...&parameter=temperature
```

### Get Sensor Status
```
GET /api/sensors/<sensor_id>/status
```

## Database Schema

### Core Tables

**users**: User accounts and sessions
**sensors**: Sensor metadata and configuration
**sensor_data**: Time-series sensor readings
**battery_status**: Current battery level and estimation
**alerts**: System alerts and notifications
**maintenance_logs**: Maintenance history

All tables include proper indexing for performance:
- `idx_sensor_timestamp` on sensor_data
- Indices on sensor_id, timestamp, and status fields

## Intelligent Logic

### Battery Estimation

```
if battery_percentage exists:
  use directly
elif battery_voltage exists:
  estimate = (voltage - min_v) / (max_v - min_v) * 100
else:
  estimate based on consumption patterns over 7 days
```

### Root Cause Analysis

When sensor is offline:
1. Check battery level (critical indicator)
2. Check last signal quality (RSSI/SNR)
3. Compare with nearby sensors
4. Classify:
   - Device Failure (low battery)
   - Network Issue (weak RSSI)
   - Gateway Issue (low SNR)

### Alert Prioritization

- **High**: Device failure, critical offline
- **Medium**: Low battery, weak connectivity
- **Low**: Signal degradation, minor issues

## Production Deployment

### Security

1. Change default admin password immediately
2. Set strong `SECRET_KEY` in environment
3. Use HTTPS (set `SESSION_COOKIE_SECURE=True`)
4. Restrict database access
5. Use production WSGI server (Gunicorn, uWSGI)

### Performance

1. Enable SQLite WAL mode or use PostgreSQL
2. Add database connection pooling
3. Implement caching for dashboard metrics
4. Use Gunicorn with multiple workers
5. Add nginx reverse proxy
6. Monitor ingestion queue

### Deployment Example (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### Monitoring

1. Check `/api/sensors/<id>/status` for health
2. Monitor alert generation rate
3. Track ingestion latency
4. Watch database query performance
5. Monitor MQTT connection uptime

## Extending the Platform

### Add New Sensor Type

1. Update `Sensor.sensor_type` in [sensor.py](app/models/sensor.py)
2. Add normalization rules in [mqtt_client.py](ingestion_worker/mqtt_client.py)
3. Create sensor-specific UI template

### Add New Alert Type

1. Define in `Alert.alert_type`
2. Implement check in [services/__init__.py](app/services/__init__.py)
3. Create resolution workflow in routes

### Integrate with External Systems

Use the JSON API (`/api/sensor-data/ingest`) to integrate:
- LoRaWAN gateways
- Other IoT platforms
- Custom sensors

## Troubleshooting

### Sensors Not Receiving Data

1. Check MQTT broker connection:
   ```
   mosquitto_sub -h broker -t "v3/+/as/up/+/+" -u user -P pass
   ```

2. Verify API endpoint reachable:
   ```
   curl http://localhost:5000/api/sensors/1/status
   ```

3. Check logs:
   ```
   tail -f ingestion_worker.log
   ```

### High Database Lock Errors

Enable WAL mode:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {'timeout': 10, 'check_same_thread': False},
    'json_serializer': str,
}
```

### Memory Usage

1. Limit query results with pagination
2. Archive old data (>30 days) to separate table
3. Implement database cleanup jobs

## Support & Documentation

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [TTI MQTT Reference](https://www.thethingsindustries.com/docs/)
- [Bootstrap 5](https://getbootstrap.com/docs/)

## License

MIT License - See LICENSE file

## Version History

- **v1.0.0** (2025-04-24): Initial release with core features
  - Sensor management
  - Real-time monitoring
  - MQTT ingestion
  - Alert system
  - Battery monitoring
