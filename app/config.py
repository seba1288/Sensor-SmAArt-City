import os
from datetime import timedelta
import json


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///iot_sensors.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 10},
        'json_serializer': json.dumps,
        'json_deserializer': json.loads,
    }
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application config
    SENSORS_OFFLINE_THRESHOLD_MINUTES = 15
    BATTERY_LOW_THRESHOLD = 20.0  # percentage
    SIGNAL_WEAK_THRESHOLD = -100  # dBm (RSSI)
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # MQTT Config (for local development, override with environment variables)
    MQTT_BROKER = os.environ.get('MQTT_BROKER') or 'localhost'
    MQTT_PORT = int(os.environ.get('MQTT_PORT') or 1883)
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME') or 'mqtt_user'
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD') or 'mqtt_password'
    MQTT_TOPICS = ['v3/+/as/up/+/+']  # TTI uplink topic pattern


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
