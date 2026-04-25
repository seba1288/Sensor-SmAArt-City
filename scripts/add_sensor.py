"""
Add a sensor record to the local SQLite DB.
Usage:
  py scripts\add_sensor.py --unique-id UNIQUE_ID --name NAME [--type TYPE] [--app APP_ID] [--dev-eui DEVEUI]
Example:
  py scripts\add_sensor.py --unique-id eui-a84041416187208e --name LHT65 --type environmental --app bodenfeuchte-dragino --dev-eui eui-a84041416187208e
"""
import sqlite3
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'instance' / 'iot_sensors.db'

parser = argparse.ArgumentParser()
parser.add_argument('--unique-id', required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--type', default='unknown')
parser.add_argument('--app', default=None)
parser.add_argument('--dev-eui', default=None)
args = parser.parse_args()

if not DB.exists():
    raise SystemExit('DB not found: ' + str(DB))

conn = sqlite3.connect(str(DB))
cur = conn.cursor()
# Ensure unique_id not already present
cur.execute('SELECT id FROM sensors WHERE unique_id=?', (args.unique_id,))
if cur.fetchone():
    print('Sensor with unique_id already exists:', args.unique_id)
    conn.close()
    raise SystemExit(1)

cur.execute('INSERT INTO sensors (unique_id, name, sensor_type, location, lorawan_dev_eui, lorawan_application_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', (
    args.unique_id, args.name, args.type, 'imported', args.dev_eui, args.app
))
sensor_id = cur.lastrowid
# battery placeholder
try:
    cur.execute('INSERT INTO battery_status (sensor_id, battery_percentage, last_seen, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (sensor_id, None, None))
except Exception:
    pass
conn.commit()
conn.close()
print('Inserted sensor', sensor_id, args.unique_id)
