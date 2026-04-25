from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.user import User
from app.models.sensor import Sensor
from app.models.sensor_data import SensorData
from app.models.battery_status import BatteryStatus
from app.models.alert import Alert
from app.models.maintenance_log import MaintenanceLog

__all__ = ['db', 'User', 'Sensor', 'SensorData', 'BatteryStatus', 'Alert', 'MaintenanceLog']
