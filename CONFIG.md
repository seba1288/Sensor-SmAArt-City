# Configuration Guide

## Environment Setup

### .env File Template

Copy this to `.env` in the project root and customize:

```env
# ====================
# FLASK CONFIGURATION
# ====================
FLASK_ENV=development
SECRET_KEY=change-me-to-random-string-in-production
DEBUG=True

# ====================
# DATABASE
# ====================
# SQLite (default)
DATABASE_URL=sqlite:///iot_sensors.db

# Or PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/iot_sensors

# ====================
# MQTT CONFIGURATION (The Things Industries)
# ====================
# Broker settings
MQTT_BROKER=au1.cloud.thethings.industries
MQTT_PORT=8883
MQTT_USERNAME=your-app-id@ttn
MQTT_PASSWORD=your-api-key

# TTI Topics (adjust region if needed)
# au1 = Australia
# eu1 = Europe
# us1 = United States
# as1 = Asia (Singapore)
# can1 = Canada
# jp1 = Japan
# in1 = India

# ====================
# API CONFIGURATION
# ====================
API_ENDPOINT=http://localhost:5000/api/sensor-data/ingest

# ====================
# SENSOR THRESHOLDS
# ====================
SENSORS_OFFLINE_THRESHOLD_MINUTES=15
BATTERY_LOW_THRESHOLD=20.0
SIGNAL_WEAK_THRESHOLD=-100
```

## Getting TTI Credentials

### Step 1: Create TTI Account
1. Go to https://console.cloud.thethings.industries/
2. Sign up or log in
3. Create an organization

### Step 2: Create Application
1. Go to "Applications" → "Create application"
2. Fill in the details
3. Copy the Application ID

### Step 3: Create API Key
1. In the application, go to "API keys" → "Create API key"
2. Select permissions:
   - `application.traffic.read` (for MQTT subscribe)
   - `application.link.read`
3. Copy the API key

### Step 4: Add Device
1. Go to "Devices" → "Register end device"
2. Enter device details:
   - DevEUI (from device)
   - AppEUI (from your app)
   - AppKey (from device)
3. Note the Device ID

### Step 5: Test Connection
```bash
# Test MQTT connection
mosquitto_sub -h au1.cloud.thethings.industries \
  -t 'v3/your-app-id@ttn/as/up/+/+' \
  -u 'your-app-id@ttn' \
  -P 'your-api-key' \
  --cafile ca.pem
```

## Database Initialization

### SQLite Setup

```bash
# Create database and tables
flask --app app init-db

# Create admin user
flask --app app create-admin

# Add sample sensors
flask --app app create-sample-sensors
```

### PostgreSQL Migration

1. **Install PostgreSQL**:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/
```

2. **Create database**:
```sql
CREATE DATABASE iot_sensors;
CREATE USER iot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE iot_sensors TO iot_user;
```

3. **Update .env**:
```env
DATABASE_URL=postgresql://iot_user:secure_password@localhost:5432/iot_sensors
```

4. **Initialize**:
```bash
flask --app app init-db
```

## Production Configuration

### Gunicorn Setup

```bash
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 60 run:app
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/app/static/;
    }
}
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

### Systemd Service

Create `/etc/systemd/system/iot-platform.service`:

```ini
[Unit]
Description=IoT Sensor Platform
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/Sensor-SmAArt-City
Environment="PATH=/path/to/Sensor-SmAArt-City/venv/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=/path/to/.env
ExecStart=/path/to/Sensor-SmAArt-City/venv/bin/gunicorn -w 4 run:app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-platform
sudo systemctl start iot-platform
```

## Monitoring & Logging

### Application Logs

```bash
# View application logs
journalctl -u iot-platform -f

# Or with syslog
tail -f /var/log/syslog | grep iot-platform
```

### Database Optimization

For SQLite, enable WAL mode:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 10, 'check_same_thread': False},
}
```

Manually run maintenance:
```bash
flask shell
>>> from app.models import db
>>> from sqlalchemy import text
>>> db.session.execute(text("VACUUM"))
>>> db.session.commit()
```

### Performance Tuning

1. **Database Indexes**: Already configured in models
2. **Query Caching**: Add Redis for dashboard metrics
3. **Connection Pooling**: Configure in PostgreSQL
4. **MQTT Batching**: Collect multiple readings before sending

## Backup & Restore

### SQLite Backup

```bash
# Backup
cp iot_sensors.db iot_sensors.db.backup

# Restore
cp iot_sensors.db.backup iot_sensors.db
```

### PostgreSQL Backup

```bash
# Backup
pg_dump iot_sensors > backup.sql

# Restore
psql iot_sensors < backup.sql
```

## Security Checklist

- [ ] Change admin password
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS (SSL certificate)
- [ ] Restrict database access
- [ ] Use strong MQTT credentials
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Enable firewall
- [ ] Backup critical data regularly
- [ ] Monitor access logs
