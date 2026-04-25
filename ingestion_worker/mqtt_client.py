"""
MQTT Ingestion Worker for The Things Industries (TTI)

Connects to TTI MQTT broker and ingests sensor data in real-time.
Run separately from the Flask app: python -m ingestion_worker.mqtt_client
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
from collections import OrderedDict
import os
import signal
import sys
from datetime import datetime
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MQTT_SERVER = os.environ.get('MQTT_BROKER', 'eu1.cloud.thethings.industries')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME', 'bodenfeuchte-dragino@stadt-aalen')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', 'NNSXS.ABCDEF...')
MQTT_TOPICS = ['v3/+/as/up/+/+']  # TTI uplink topics
API_ENDPOINT = os.environ.get('API_ENDPOINT', 'http://localhost:5000/api/sensor-data/ingest')

# Per-sensor credentials file (JSON). Format example in ingestion_worker/credentials.example.json
# {
#   "device-123": {"api_key": "secret1", "api_endpoint": "http://localhost:5000/api/sensor-data/ingest", "api_key_header": "X-API-Key"},
#   "device-456": {"api_key": "secret2", "api_key_header": "Authorization"},
#   "default": {"api_key": "globalkey", "api_key_header": "X-API-Key"}
# }
CREDENTIALS_FILE = os.environ.get('SENSOR_CREDENTIALS_FILE') or str(Path(__file__).parent / 'credentials.json')
API_KEY_HEADER_DEFAULT = os.environ.get('API_KEY_HEADER', 'X-API-Key')

# Load per-sensor credentials if available
credentials_map = {}
try:
    cred_path = Path(CREDENTIALS_FILE)
    if cred_path.is_file():
        with cred_path.open('r', encoding='utf-8') as f:
            credentials_map = json.load(f)
        logger.info(f'Loaded credentials for {len(credentials_map)} devices from {cred_path}')
    else:
        logger.warning(f'Credentials file not found at {cred_path}; proceeding without per-sensor API keys')
except Exception as e:
    logger.error(f'Failed to load credentials file {CREDENTIALS_FILE}: {e}')

# For graceful shutdown
running = True

# Simple in-memory dedupe cache to avoid processing the same uplink multiple times
# Keyed by (dev_eui, received_at) with short TTL (seconds). This handles cases
# where multiple MQTT clients subscribe to overlapping topics and deliver the
# same message more than once.
RECENT_MESSAGES = OrderedDict()
RECENT_TTL = int(os.environ.get('MQTT_DEDUPE_TTL', 30))
RECENT_MAX = int(os.environ.get('MQTT_DEDUPE_MAX', 1024))


def on_connect(client, userdata, flags, rc):
    """MQTT connect callback."""
    if rc == 0:
        logger.info('Connected to MQTT broker')
        # Per-client topics may be attached to the client object
        topics = getattr(client, '_topics', MQTT_TOPICS)
        for topic in topics:
            client.subscribe(topic)
            logger.info(f'Subscribed to topic: {topic}')
    else:
        logger.error(f'Failed to connect, return code {rc}')


def on_disconnect(client, userdata, rc):
    """MQTT disconnect callback."""
    if rc != 0:
        logger.warning(f'Unexpected disconnection, return code {rc}')


def on_message(client, userdata, msg):
    """MQTT message callback - processes incoming sensor data."""
    global running
    
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        logger.debug(f'Received message on {msg.topic}')

        # Deduplicate: use dev_eui and received_at timestamp when available
        end_ids = payload.get('end_device_ids', {})
        dev_eui = end_ids.get('dev_eui') or end_ids.get('device_id')
        received_at = payload.get('received_at') or payload.get('uplink_message', {}).get('received_at')
        dedupe_key = None
        if dev_eui and received_at:
            dedupe_key = f"{dev_eui}|{received_at}"
            # Clean out expired entries
            now = time.time()
            keys_to_delete = []
            for k, ts in RECENT_MESSAGES.items():
                if now - ts > RECENT_TTL:
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                RECENT_MESSAGES.pop(k, None)

            if dedupe_key in RECENT_MESSAGES:
                logger.info(f'Duplicate uplink ignored for {dedupe_key}')
                return
            # Insert new key
            RECENT_MESSAGES[dedupe_key] = now
            # Maintain size
            while len(RECENT_MESSAGES) > RECENT_MAX:
                RECENT_MESSAGES.popitem(last=False)

        # Parse TTI uplink message
        data = parse_tti_uplink(payload)
        
        if data:
            # Send to Flask API
            send_to_api(data)
    
    except json.JSONDecodeError:
        logger.error('Failed to decode message payload')
    except Exception as e:
        logger.error(f'Error processing message: {str(e)}')


def parse_tti_uplink(payload):
    """Parse TTI MQTT uplink message.
    
    TTI format:
    {
        "end_device_ids": {"device_id": "...", "dev_eui": "..."},
        "received_at": "...",
        "uplink_message": {
            "rx_metadata": [...],
            "settings": {...},
            "decoded_payload": {...}
        }
    }
    """
    try:
        end_ids = payload.get('end_device_ids', {})
        device_id = end_ids.get('device_id')
        dev_eui = end_ids.get('dev_eui')
        # application id can appear under several keys in TTI payloads
        application_id = (end_ids.get('application_ids', {}) or {}).get('application_id') or payload.get('application_ids', {}).get('application_id')
        timestamp = payload.get('received_at')
        
        uplink_msg = payload.get('uplink_message', {})
        decoded = uplink_msg.get('decoded_payload', {})
        
        # Get signal quality from RX metadata
        rx_metadata = uplink_msg.get('rx_metadata', [])
        rssi = None
        snr = None
        
        if rx_metadata:
            first_gw = rx_metadata[0]
            rssi = first_gw.get('rssi')
            snr = first_gw.get('snr')
        
        # Normalize sensor data
        sensor_data = normalize_payload(decoded, device_id)
        
        return {
            'device_id': device_id,
            'dev_eui': dev_eui,
            'application_id': application_id,
            'timestamp': timestamp,
            'data': sensor_data,
            'signal': {
                'rssi': rssi,
                'snr': snr,
            },
            'battery': extract_battery(decoded),
        }
    
    except Exception as e:
        logger.error(f'Error parsing TTI uplink: {str(e)}')
        return None


def normalize_payload(decoded, device_id):
    """Normalize heterogeneous payload formats into standard schema.
    
    Handles different sensor types:
    - Environmental: temperature, humidity, pressure
    - Weather: wind_speed, wind_direction, rainfall
    - Air Quality: co2, no2, pm25, pm10
    - Parking: available_spaces, occupancy
    """
    data = []
    
    # Map common parameter names
    parameter_map = {
        'temp': ('temperature', '°C'),
        'temperature': ('temperature', '°C'),
        'hum': ('humidity', '%'),
        'humidity': ('humidity', '%'),
        'pres': ('pressure', 'hPa'),
        'pressure': ('pressure', 'hPa'),
        'co2': ('co2', 'ppm'),
        'no2': ('no2', 'ppb'),
        'pm25': ('pm2.5', 'µg/m³'),
        'pm25_value': ('pm2.5', 'µg/m³'),
        'pm10': ('pm10', 'µg/m³'),
        'available_parking': ('available_parking', 'count'),
        'available_spaces': ('available_spaces', 'count'),
        'occupancy': ('occupancy', '%'),
        'wind_speed': ('wind_speed', 'm/s'),
        'wind_direction': ('wind_direction', '°'),
        'rainfall': ('rainfall', 'mm'),
    }
    
    for key, value in decoded.items():
        if key in parameter_map:
            param_name, unit = parameter_map[key]
            data.append({
                'parameter': param_name,
                'value': value,
                'unit': unit,
            })
        else:
            # Generic unknown parameter
            data.append({
                'parameter': key,
                'value': value,
                'unit': 'unknown',
            })
    
    return data


def extract_battery(decoded):
    """Extract battery information from payload."""
    battery = {}
    
    # Check for percentage
    for key in ['battery', 'battery_percentage', 'batt_percent', 'batt', 'battery_pct']:
        if key in decoded:
            battery['percentage'] = decoded[key]
            break
    
    # Check for voltage
    for key in ['battery_voltage', 'battery_v', 'batt_v', 'voltage']:
        if key in decoded:
            battery['voltage'] = decoded[key]
            break
    
    return battery if battery else None


def send_to_api(data):
    """Send normalized data to Flask API."""
    try:
        # Determine device-specific credentials (fall back to default)
        device_id = data.get('device_id') or data.get('dev_eui')
        application_id = data.get('application_id')

        # Lookup order: device_id -> application_id -> MQTT_USERNAME (env) -> default
        creds = None
        if device_id:
            creds = credentials_map.get(device_id) or credentials_map.get(str(device_id))
        if not creds and application_id:
            creds = credentials_map.get(application_id)
        if not creds:
            creds = credentials_map.get(MQTT_USERNAME) or credentials_map.get('default')

        endpoint = API_ENDPOINT
        headers = {'Content-Type': 'application/json'}

        if creds:
            # Override endpoint per-device if provided
            endpoint = creds.get('api_endpoint') or endpoint

            api_key = creds.get('api_key')
            header_name = creds.get('api_key_header') or API_KEY_HEADER_DEFAULT

            if api_key:
                # If header chosen is Authorization, ensure Bearer scheme
                if header_name.lower() == 'authorization':
                    if not api_key.lower().startswith('bearer '):
                        headers['Authorization'] = f'Bearer {api_key}'
                    else:
                        headers['Authorization'] = api_key
                else:
                    headers[header_name] = api_key

        logger.debug(f'Sending data for device {device_id} to {endpoint} with headers {list(headers.keys())}')

        response = requests.post(
            endpoint,
            json=data,
            timeout=5,
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info(f'Data ingested for device {data.get("device_id")}')
        else:
            logger.warning(f'API returned status {response.status_code}: {response.text}')
    
    except requests.exceptions.ConnectionError:
        logger.error(f'Failed to connect to API: {API_ENDPOINT}')
    except requests.exceptions.Timeout:
        logger.error('API request timed out')
    except Exception as e:
        logger.error(f'Error sending to API: {str(e)}')


def handle_signal(signum, frame):
    """Handle graceful shutdown."""
    global running
    logger.info('Shutdown signal received')
    running = False


def main():
    """Main MQTT client loop."""
    global running
    
    logger.info(f'Starting MQTT client...')
    logger.info(f'Broker: {MQTT_SERVER}:{MQTT_PORT}')
    logger.info(f'Topics: {MQTT_TOPICS}')
    logger.info(f'API Endpoint: {API_ENDPOINT}')
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Determine if credentials file contains per-application MQTT credentials
    mqtt_clients = []
    try:
        # Build client per-entry if mqtt_username/password provided
        for key, cfg in credentials_map.items():
            if isinstance(cfg, dict) and (cfg.get('mqtt_username') or cfg.get('mqtt_password')):
                cname = key
                client = mqtt.Client(client_id=f'iot-platform-ingestion-{cname}')
                client.on_connect = on_connect
                client.on_disconnect = on_disconnect
                client.on_message = on_message

                # Attach per-client topics
                client._topics = cfg.get('mqtt_topics') or MQTT_TOPICS

                # Connect using per-app credentials (fall back to env)
                username = cfg.get('mqtt_username') or MQTT_USERNAME
                password = cfg.get('mqtt_password') or MQTT_PASSWORD
                client.username_pw_set(username, password)
                client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
                client.loop_start()
                mqtt_clients.append(client)
                logger.info(f'Started MQTT client for {cname} (user={username})')

        # If no per-app clients were created, fall back to single client using environment vars
        if not mqtt_clients:
            client = mqtt.Client(client_id='iot-platform-ingestion')
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.on_message = on_message
            client._topics = MQTT_TOPICS
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
            client.loop_start()
            mqtt_clients.append(client)
            logger.info('Started single MQTT client using environment credentials')

        logger.info('MQTT client(s) running. Press Ctrl+C to stop.')

        # Keep running until shutdown signal. Sleep briefly to avoid CPU spin.
        # This prevents the process from pegging a core when idle.
        while running:
            time.sleep(0.5)

        logger.info('Shutting down MQTT client(s)...')
        for c in mqtt_clients:
            try:
                c.loop_stop()
                c.disconnect()
            except Exception:
                pass

    except Exception as e:
        logger.error(f'Fatal error: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
