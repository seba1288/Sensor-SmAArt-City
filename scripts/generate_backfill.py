"""
Generate synthetic sensor data for the last N hours for all sensors in DB.
Usage: py scripts\generate_backfill.py [hours] [interval_minutes]
Defaults: hours=96, interval_minutes=60
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'instance' / 'iot_sensors.db'

HOURS = int(sys.argv[1]) if len(sys.argv) > 1 else 96
INTERVAL_MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 60

now = datetime.utcnow()
start = now - timedelta(hours=HOURS)

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

# Load sensors
cur.execute('SELECT id, unique_id, name, sensor_type, lorawan_application_id FROM sensors')
sensors = cur.fetchall()
print(f'Found {len(sensors)} sensors; generating data from {start.isoformat()} to {now.isoformat()} every {INTERVAL_MIN} minutes')

inserted = 0
for s in sensors:
    sensor_id, unique_id, name, sensor_type, app_id = s
    t = start
    while t <= now:
        readings = []
        # Create realistic reading values based on sensor_type or name
        # Environmental sensors: temperature + humidity
        if sensor_type and 'env' in sensor_type.lower() or 'moist' in (name or '').lower() or 'temp' in (name or '').lower() or 'humidity' in (name or '').lower():
            temp = round(15 + 10*random.random(), 1)  # 15-25 C
            hum = round(40 + 30*random.random(), 1)  # 40-70 %
            readings.append(('temperature', temp, '°C'))
            readings.append(('humidity', hum, '%'))
        elif sensor_type and 'rain' in sensor_type.lower() or 'rain' in (name or '').lower():
            # Rain: occasional spikes
            if random.random() < 0.1:  # 10% chance of rain per interval
                rainfall = round(random.uniform(0.1, 5.0), 2)
            else:
                rainfall = 0.0
            readings.append(('rainfall', rainfall, 'mm'))
        elif sensor_type and 'smart' in sensor_type.lower() or 'smart' in (name or '').lower():
            # Smart wall: temperature + occupancy
            temp = round(18 + 8*random.random(), 1)
            occ = 1 if random.random() < 0.05 else 0
            readings.append(('temperature', temp, '°C'))
            readings.append(('occupancy', occ, '%'))
        else:
            # Default: single numeric measurement
            val = round(random.uniform(0, 100), 2)
            readings.append(('value', val, 'count'))

        # Signal quality
        rssi = random.randint(-110, -60)
        snr = round(random.uniform(-5, 10), 1)

        # Build payload object (mimicking API ingest format)
        payload = {
            'device_id': unique_id,
            'dev_eui': None,
            'application_id': app_id,
            'timestamp': t.isoformat() + 'Z',
            'data': [ {'parameter': p, 'value': v, 'unit': u} for (p,v,u) in readings ],
            'signal': {'rssi': rssi, 'snr': snr},
            'battery': {'percentage': round(random.uniform(30, 95),1), 'voltage': round(random.uniform(3.2,3.9),2)}
        }

        # Insert each reading row
        for d in payload['data']:
            cur.execute('INSERT INTO sensor_data (sensor_id, parameter, value, unit, rssi, snr, timestamp, raw_payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
                sensor_id,
                d['parameter'],
                d['value'],
                d.get('unit'),
                rssi,
                snr,
                t.isoformat(),
                json.dumps(payload)
            ))
            inserted += 1

        # Update battery_status last_seen and percentage
        cur.execute('SELECT id FROM battery_status WHERE sensor_id=?', (sensor_id,))
        if cur.fetchone():
            cur.execute('UPDATE battery_status SET battery_percentage=?, last_seen=?, updated_at=CURRENT_TIMESTAMP WHERE sensor_id=?', (payload['battery']['percentage'], t.isoformat(), sensor_id))
        else:
            cur.execute('INSERT INTO battery_status (sensor_id, battery_percentage, last_seen, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (sensor_id, payload['battery']['percentage'], t.isoformat()))

        t = t + timedelta(minutes=INTERVAL_MIN)

conn.commit()
conn.close()
print(f'Inserted {inserted} sensor_data rows')
