# Architecture & Implementation Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         IoT Sensor Platform                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐                    ┌─────────────────────┐  │
│  │   Web Browser  │◄──────HTTP/REST────►│   Flask App         │  │
│  │   (Jinja2 UI)  │                    │  (Routes/Services)  │  │
│  └────────────────┘                    └─────────────────────┘  │
│                                               │                   │
│  ┌────────────────────────────────────────────▼──────────────┐  │
│  │                  Business Logic Services                   │  │
│  │  • AlertService          (Detection & Management)          │  │
│  │  • BatteryService        (Estimation & Prediction)         │  │
│  │  • RootCauseService      (Diagnosis)                       │  │
│  │  • SensorService         (CRUD & Analytics)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                               │                   │
│  ┌────────────────────────────────────────────▼──────────────┐  │
│  │              SQLAlchemy ORM Layer                          │  │
│  │  • User, Sensor, SensorData, BatteryStatus                 │  │
│  │  • Alert, MaintenanceLog                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                               │                   │
│  ┌────────────────────────────────────────────▼──────────────┐  │
│  │              SQLite Database                               │  │
│  │  (Ready for PostgreSQL migration)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │          MQTT Ingestion Worker (Separate Process)      │     │
│  │                                                        │     │
│  │  ┌──────────────┐         ┌─────────────────────┐    │     │
│  │  │ TTI MQTT     │────────►│ Data Normalization  │    │     │
│  │  │ Broker       │         │ Layer               │    │     │
│  │  └──────────────┘         └──────────┬──────────┘    │     │
│  │                                     │               │     │
│  │  ┌──────────────┐         ┌────────▼───────────┐    │     │
│  │  │ JSON Parsing │◄────────│ JSON API (/ingest) │    │     │
│  │  │ & Transform  │         └────────────────────┘    │     │
│  │  └──────────────┘                                    │     │
│  │                                                        │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Real-time Sensor Data Ingestion

```
TTI MQTT Broker
    ↓
mqtt_client.py (subscribe to v3/+/as/up/+/+)
    ↓
JSON Payload (TTI uplink format)
    ↓
parse_tti_uplink() (extract device_id, timestamp, decoded_payload)
    ↓
normalize_payload() (map temperature→°C, humidity→%, etc.)
    ↓
extract_battery() (voltage or percentage)
    ↓
POST /api/sensor-data/ingest
    ↓
ingest_sensor_data() (Flask API route)
    ↓
Create SensorData records
Update BatteryStatus
    ↓
Alert Checks:
  • check_offline_sensors()
  • check_low_battery()
  • check_weak_signal()
    ↓
Database Commit
    ↓
User sees updates in Dashboard
```

### 2. Web Dashboard Query

```
User Login
    ↓
Session Management (auth_required decorator)
    ↓
Dashboard Route
    ↓
SensorService.get_sensor_stats()
  • Count total_sensors
  • Count online (last_seen > 15 min ago)
  • Count offline
  • Count low_battery
  • Count active_alerts
    ↓
AlertService.get_active_alerts()
    ↓
Render dashboard/index.html with Jinja2
    ↓
HTML sent to browser
    ↓
User sees:
  • Metric cards (Online, Offline, Battery, Alerts)
  • Recent alerts table
  • System status
```

## Key Design Patterns

### 1. Data Normalization Layer

**Problem**: Different sensor manufacturers send data in different formats
- Some: `{"temp": 25.5}`
- Others: `{"temperature_celsius": 25.5}`
- LoRa: Binary payloads (TTI decodes)

**Solution**: `normalize_payload()` function maps all formats to unified schema:
```json
{"parameter": "temperature", "value": 25.5, "unit": "°C"}
```

### 2. Battery Estimation

**Problem**: Different sensors report battery differently
- Some: Direct percentage (0-100)
- Others: Voltage (0.9-1.5V, 3.0-3.7V, etc.)
- Some: No battery info at all

**Solution**: Tiered approach:
```python
if battery_percentage exists:
    use directly
elif battery_voltage exists:
    linear interpolation (min_v to max_v → 0-100%)
else:
    estimate based on 7-day consumption trends
```

### 3. Root Cause Analysis

**Problem**: When a sensor goes offline, why?
- Device failed? (low battery)
- Network issue? (weak signal)
- Gateway down? (low SNR)

**Solution**: Analyze multiple factors:
```python
if battery < 5%:
    root_cause = "device_failure"
elif rssi < -110:
    root_cause = "network_issue"
elif snr < -5:
    root_cause = "gateway_issue"
else:
    root_cause = "unknown"
```

### 4. Separation of Concerns

**Web App** (Flask):
- Routes (thin, only HTTP handling)
- Services (business logic)
- Models (ORM)
- Templates (UI)

**MQTT Worker** (Separate process):
- Handles all MQTT connectivity
- No dependency on Flask
- Can be scaled independently
- Calls Flask API to ingest data

Benefits:
- Web app stays responsive
- MQTT worker resilient to web app crashes
- Easy to debug each component
- Can run on different servers

## Database Schema

### Indexing Strategy

```
Primary Tables:
├── users (indexed: username, email)
├── sensors (indexed: unique_id, created_at)
├── sensor_data (indexed: sensor_id, timestamp)  ← CRITICAL
├── battery_status (indexed: sensor_id, last_seen)
├── alerts (indexed: sensor_id, status, created_at)
└── maintenance_logs (indexed: sensor_id, timestamp)

Composite Indices:
├── (sensor_id, timestamp) on sensor_data
└── (sensor_id, status) on alerts

Strategy:
- All foreign keys indexed (sensor_id)
- All time-series queries indexed (timestamp)
- Filter queries indexed (status, type)
```

### Query Optimization

**Fast Queries**:
- Get online sensors: Uses battery_status.last_seen index
- Get recent alerts: Uses alerts.created_at index
- Get sensor data: Uses (sensor_id, timestamp) composite

**Potential Slow Queries**:
- Join across multiple tables → Use proper select() with joins
- COUNT on large tables → Cache in Redis
- Datetime comparisons → Use index on timestamp

## Services Implementation

### AlertService
```python
Functions:
├── check_offline_sensors(threshold_minutes=15)
├── check_low_battery()
├── check_weak_signal(rssi_threshold=-100)
├── get_active_alerts()
└── get_alerts_by_severity()

Logic:
• Runs during MQTT data ingestion
• Creates/updates Alert records
• Assigns root_cause and severity
• Supports resolution workflow
```

### BatteryService
```python
Functions:
├── estimate_battery_percentage(voltage, sensor)
├── update_battery_status(sensor_id, battery_data)
└── estimate_remaining_days(sensor_id)

Logic:
• Handles multiple battery formats
• Voltage → percentage conversion
• Tracks estimation method
• Predicts battery life from trends
```

### RootCauseService
```python
Functions:
├── analyze_sensor_issue(sensor_id)
└── get_nearby_sensors(sensor_id, radius_km=1.0)

Logic:
• Diagnoses why sensor is offline
• Compares with nearby sensors
• Identifies device vs network issues
• Returns actionable diagnostics
```

### SensorService
```python
Functions:
├── get_sensor_stats()
├── get_sensor_by_unique_id()
├── get_sensor_latest_data()
└── get_sensor_data_for_range()

Logic:
• Dashboard metric computation
• Sensor CRUD helpers
• Data retrieval with caching potential
```

## API Endpoints

### Data Ingestion
```
POST /api/sensor-data/ingest
├── Accepts: TTI uplink or normalized JSON
├── Processing:
│   ├── Normalize payload
│   ├── Extract battery data
│   ├── Store in sensor_data
│   ├── Update battery_status
│   └── Run alert checks
└── Returns: {success, message, sensor_id}
```

### Data Retrieval
```
GET /api/sensors/<id>/data
├── Query: start, end, parameter
├── Returns: Array of readings with metadata
└── Supports: Time range filtering, parameter selection

GET /api/sensors/<id>/status
├── Returns: Current online status, battery, last_seen
└── Use: Real-time health checks
```

## Configuration Management

### Environment-based (12-factor app)
- Development: SQLite, debug=True
- Production: PostgreSQL, debug=False
- Testing: In-memory, isolated

### Hierarchical Config
```python
Config (base) → DevelopmentConfig → ProductionConfig
```

### Sensitive Data
- Stored in .env, never in repo
- API keys, passwords, secrets
- Database credentials
- MQTT authentication

## Performance Considerations

### SQLite Optimization
```python
# WAL mode for concurrency
SQLALCHEMY_ENGINE_OPTIONS = {
    'journal_mode': 'WAL',
    'timeout': 10,
}

# Connection pooling
pool_size=5
pool_recycle=3600
```

### Query Patterns
- Use select() with eager loading
- Avoid N+1 queries
- Paginate dashboard tables
- Cache metrics every 60 seconds

### Scaling Path
1. **Stage 1** (MVP): SQLite, single process
2. **Stage 2** (Growth): PostgreSQL, Gunicorn 4 workers
3. **Stage 3** (Scale): PostgreSQL, Redis caching, separate MQTT queue
4. **Stage 4** (Enterprise): PostgreSQL, TimescaleDB, Kafka, distributed MQTT

## Security Layers

### Authentication
- Session-based (Flask-Session)
- Password hashing (SHA256)
- HTTP-only cookies
- CSRF protection (planned)

### Authorization
- login_required decorator
- Role-based (future: admin, operator, viewer)
- API key authentication (future)

### Data Protection
- SQL injection: SQLAlchemy ORM prevents
- XSS: Jinja2 auto-escapes
- HTTPS: Recommended in production
- MQTT TLS: Enabled for TTI

### Secrets Management
- Environment variables
- No hardcoded credentials
- Separate .env per deployment
- Secure MQTT authentication

## Testing Recommendations

### Unit Tests
- Service logic (Battery, Alert, RootCause)
- Model validation
- Helper functions

### Integration Tests
- API endpoints (/api/sensor-data/ingest)
- Database transactions
- Alert triggering

### End-to-End Tests
- Full MQTT→Dashboard flow
- Web UI workflows
- Authentication

### Load Testing
- MQTT message processing (msgs/sec)
- API response time (ms)
- Database query performance

## Maintenance & Operations

### Regular Tasks
- Database cleanup (VACUUM)
- Archive old data
- Update dependencies
- Security patches
- Backup procedures

### Monitoring
- MQTT connection health
- API response times
- Database size/performance
- Alert generation rate
- Sensor online status

### Alerting
- High: Device failures, critical issues
- Medium: Low battery, weak signals
- Low: Maintenance needed, minor anomalies

## Future Enhancements

### Short Term
- [ ] CSV export of sensor data
- [ ] Sensor grouping/zones
- [ ] Email notifications for alerts
- [ ] Data visualization (charts)
- [ ] User roles (admin, operator, viewer)

### Medium Term
- [ ] Real-time map view
- [ ] Advanced analytics/ML
- [ ] API key management
- [ ] Webhook support
- [ ] Mobile app

### Long Term
- [ ] Edge computing support
- [ ] Multi-region deployment
- [ ] Advanced forecasting
- [ ] Integration marketplace
- [ ] High-availability clustering
