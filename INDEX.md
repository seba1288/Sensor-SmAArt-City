# IoT Sensor Monitoring Platform - Documentation Index

Welcome! This is your guide to the complete IoT Sensor Monitoring Platform for Aalen Smart City.

## 📋 Start Here

### For First-Time Users
1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ START HERE (5 minutes)
   - Fast setup instructions
   - Manual testing with examples
   - Common tasks

2. **[README.md](README.md)** (Comprehensive overview)
   - Complete feature list
   - Installation guide
   - Configuration
   - API reference
   - Troubleshooting

### For Developers
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** (System design)
   - Architecture diagrams
   - Design patterns
   - Service implementation
   - Database optimization
   - Security architecture

4. **[CONFIG.md](CONFIG.md)** (Detailed configuration)
   - TTI MQTT setup (step-by-step)
   - PostgreSQL migration
   - Production deployment
   - Monitoring & backup
   - Security checklist

### For Operations
5. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**
   - Complete feature checklist
   - Deployment options
   - Performance metrics
   - Next steps

6. **[DELIVERABLES.md](DELIVERABLES.md)**
   - Full deliverables checklist
   - Production readiness assessment
   - Testing recommendations

## 🚀 Quick Navigation

### I want to...

#### ✅ Get Started Immediately
→ See [QUICKSTART.md](QUICKSTART.md)
```bash
pip install -r requirements.txt
flask --app app init-db
flask --app app create-admin
python run.py
```

#### ✅ Deploy to Production
→ See [CONFIG.md](CONFIG.md) → Production Deployment section
- Docker Compose setup
- Gunicorn + Nginx
- SSL certificate (Let's Encrypt)
- Systemd service

#### ✅ Configure MQTT (The Things Industries)
→ See [CONFIG.md](CONFIG.md) → Getting TTI Credentials section
- Step-by-step credential setup
- Test MQTT connection
- Register devices

#### ✅ Understand the Architecture
→ See [ARCHITECTURE.md](ARCHITECTURE.md)
- System diagrams
- Design patterns
- Data flow
- Scaling strategy

#### ✅ Set Up Custom Sensors
→ See [README.md](README.md) → Core Features → Sensor Management
- Add sensor via UI
- Configure battery parameters
- Set up LoRaWAN metadata

#### ✅ Troubleshoot Issues
→ See [README.md](README.md) → Troubleshooting section

#### ✅ Test Data Ingestion
→ See [QUICKSTART.md](QUICKSTART.md) → Testing Data Flow
- Manual curl examples
- MQTT worker setup
- Database inspection

## 📁 Project Structure

```
Sensor-SmAArt-City/
│
├── 📚 Documentation (READ THESE FIRST)
│   ├── README.md                    Main documentation (500+ lines)
│   ├── QUICKSTART.md               5-minute quick start ⭐
│   ├── CONFIG.md                   Configuration guide
│   ├── ARCHITECTURE.md             System design & patterns
│   ├── IMPLEMENTATION_SUMMARY.md    Feature checklist & summary
│   └── DELIVERABLES.md             Deliverables checklist
│
├── 📦 Application Code
│   ├── app/
│   │   ├── __init__.py            Flask app factory
│   │   ├── config.py              Configuration classes
│   │   ├── models/                Database models (6 tables)
│   │   ├── services/              Business logic
│   │   ├── routes/                Flask routes (4 blueprints)
│   │   ├── templates/             HTML templates (10+ pages)
│   │   └── static/css/            Stylesheets
│   │
│   ├── ingestion_worker/
│   │   └── mqtt_client.py         TTI MQTT client
│   │
│   ├── run.py                     Entry point
│   └── db_utils.py                Database utilities
│
├── ⚙️ Configuration
│   ├── requirements.txt            Python dependencies
│   ├── .env.example               Environment template
│   ├── Dockerfile                 Container image
│   └── docker-compose.yml         Full stack (database + app + worker)
│
└── 📋 Project Files
    └── .gitignore                 Git ignore rules
```

## 🎯 Feature Overview

### Core Capabilities
- **Sensor Management**: Add, edit, delete sensors with full metadata
- **Real-time Monitoring**: Live dashboard with status, battery, signals
- **Data Ingestion**: MQTT client for The Things Industries (TTI)
- **Alert System**: Offline, low battery, weak signal detection
- **Battery Monitoring**: Voltage estimation, consumption prediction
- **Root Cause Analysis**: Device vs network vs gateway issue diagnosis
- **Maintenance Tracking**: Log maintenance activities and repairs
- **Web API**: REST endpoints for data ingestion and retrieval

### Supported Sensor Types
- Environmental (temperature, humidity, pressure)
- Parking (occupancy, available spaces)
- Weather (wind, rainfall)
- Air Quality (CO2, NO2, PM2.5, PM10)

## 🔧 Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (PostgreSQL ready)
- **ORM**: SQLAlchemy
- **Frontend**: Jinja2 + Bootstrap 5
- **MQTT**: paho-mqtt (The Things Industries)
- **Deployment**: Docker, Gunicorn, Nginx
- **Configuration**: python-dotenv

## 📊 System Architecture

```
┌─────────────────────────────────────────┐
│     Browser (Web UI - Jinja2/Bootstrap) │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼──────────┐
        │   Flask App       │
        │ (Routes/Services) │
        └────────┬──────────┘
                 │
        ┌────────▼──────────────────┐
        │  Business Logic Services  │
        │  • Alert, Battery, Sensor │
        │  • Root Cause Analysis    │
        └────────┬──────────────────┘
                 │
        ┌────────▼──────────┐
        │   SQLAlchemy ORM  │
        └────────┬──────────┘
                 │
        ┌────────▼──────────┐
        │   Database        │
        │   (SQLite/PG)     │
        └───────────────────┘

        ┌─────────────────────────┐
        │  MQTT Ingestion Worker  │
        │  (Separate Process)     │
        │  TTI Broker → Data In   │
        │  → Flask API → Store    │
        └─────────────────────────┘
```

## ⚡ Quick Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
flask --app app init-db
flask --app app create-admin
flask --app app create-sample-sensors
```

### Run
```bash
# Development
python run.py

# With MQTT worker (separate terminals)
# Terminal 1
python run.py

# Terminal 2
python -m ingestion_worker.mqtt_client
```

### Docker
```bash
# Full stack (PostgreSQL, Flask, MQTT worker)
docker-compose up

# Individual services
docker-compose up postgres      # Database only
docker-compose up app          # Flask app only
docker-compose up mqtt-worker  # MQTT ingestion
```

## 🔐 Security

✅ Password hashing (SHA256)
✅ Session management
✅ MQTT TLS encryption
✅ SQL injection prevention (ORM)
✅ XSS prevention (Jinja2 auto-escape)
✅ HTTPS ready
✅ Environment variable security

See [CONFIG.md](CONFIG.md) for complete security checklist

## 📈 Performance

✅ Database indexing on all query paths
✅ Composite indices for time-series queries
✅ SQLite WAL mode for concurrent access
✅ Query optimization with SQLAlchemy
✅ Stateless design for horizontal scaling
✅ Pagination on all list views

## 🧪 Testing

Ready for:
- Unit tests (services, models)
- Integration tests (API, database)
- End-to-end tests (workflows)
- Load testing (MQTT throughput)
- Security testing

## 🚀 Deployment

### Development (Local)
```bash
python run.py
```

### Production (Docker)
```bash
docker-compose up -d
```

### Production (Linux Server)
See [CONFIG.md](CONFIG.md) for:
- Gunicorn setup
- Nginx reverse proxy
- SSL certificate
- Systemd service

### Cloud Platforms
AWS, Azure, DigitalOcean, etc. - all supported via Docker or standard deployment

## 📞 Getting Help

### Problem Solving
1. Check [README.md](README.md) → Troubleshooting
2. Check [QUICKSTART.md](QUICKSTART.md) → Troubleshooting
3. Check application logs: `tail -f app.log`
4. Use Flask shell: `flask shell`

### Configuration Issues
1. See [CONFIG.md](CONFIG.md)
2. Copy `.env.example` to `.env`
3. Fill in your credentials

### MQTT Issues
1. See [CONFIG.md](CONFIG.md) → Getting TTI Credentials
2. Test connection manually (instructions provided)
3. Check MQTT worker logs

## 📚 Documentation Map

```
QUICKSTART.md                    ← Start here (5 min)
    ├─ Basic setup
    ├─ Manual testing
    └─ Common tasks
    
README.md                        ← Feature overview
    ├─ Installation
    ├─ Features
    ├─ API docs
    ├─ Troubleshooting
    └─ Support resources
    
CONFIG.md                        ← Configuration details
    ├─ Environment setup
    ├─ TTI MQTT guide
    ├─ Production deployment
    ├─ Database migration
    ├─ Monitoring
    └─ Security checklist
    
ARCHITECTURE.md                  ← System design
    ├─ Architecture diagrams
    ├─ Data flow
    ├─ Design patterns
    ├─ Service details
    ├─ Database schema
    ├─ Scaling strategy
    └─ Future enhancements
    
IMPLEMENTATION_SUMMARY.md        ← Completion status
    ├─ Feature checklist
    ├─ Deliverables
    ├─ Deployment options
    ├─ Testing guide
    └─ Next steps
    
DELIVERABLES.md                  ← Deliverables checklist
    ├─ Code completeness
    ├─ Feature completeness
    ├─ Production readiness
    └─ Quality metrics
```

## ✅ Success Checklist

After reading this index:
- [ ] Read QUICKSTART.md (5 min)
- [ ] Run local setup (`python run.py`)
- [ ] Access dashboard (http://localhost:5000)
- [ ] Add a sensor manually
- [ ] Review README.md for full features
- [ ] Check CONFIG.md for your use case
- [ ] Plan deployment strategy

## 🎓 Learning Path

### Beginner
1. QUICKSTART.md - Get running in 5 minutes
2. Add a sensor via UI
3. View sensor details
4. Trigger an alert manually (post data)

### Intermediate
1. CONFIG.md - Configure MQTT credentials
2. Run MQTT worker
3. Send real sensor data
4. Watch alerts trigger automatically
5. Review ARCHITECTURE.md - Understand design

### Advanced
1. Customize business logic (services)
2. Add new sensor types
3. Implement custom alerts
4. Deploy to production
5. Scale infrastructure

## 🌟 Quick Tips

- **Default Login**: admin / admin123 (change this!)
- **Sample Sensors**: Create with `flask --app app create-sample-sensors`
- **Database File**: SQLite at `iot_sensors.db`
- **Configuration**: Environment variables in `.env`
- **Logs**: Check Flask output in terminal
- **Database Shell**: Run `flask shell` for interactive access
- **API Testing**: Use curl examples in QUICKSTART.md

## 📞 Need More Help?

- **QUICKSTART.md**: 5-minute setup examples
- **README.md**: Comprehensive feature documentation
- **CONFIG.md**: Configuration and deployment details
- **ARCHITECTURE.md**: System design and patterns
- **Application logs**: Run `python run.py` and check console output

---

**Happy deploying! 🚀**

Your complete IoT platform is ready to go. Start with QUICKSTART.md and you'll be monitoring sensors in 5 minutes!
