"""
Wipe all sensors and recreate them based on /api/applications.
- Deletes entries in sensors, sensor_data, battery_status, alerts, maintenance_logs.
- Recreates sensors and battery placeholders from API applications response.

Run with: py scripts\recreate_sensors_from_api.py
"""
import requests
import os
from pathlib import Path
import sqlite3
import json

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'instance' / 'iot_sensors.db'
API = os.environ.get('API_ENDPOINT', 'http://localhost:5000/api/applications')


def fetch_apps():
    r = requests.get(API, timeout=5)
    r.raise_for_status()
    return r.json()


def wipe_db(conn):
    cur = conn.cursor()
    # Disable foreign keys for truncate-like operations
    cur.execute('PRAGMA foreign_keys = OFF')
    # Delete from dependent tables first
    for tbl in ['sensor_data', 'alerts', 'maintenance_logs', 'battery_status', 'sensors']:
        try:
            cur.execute(f'DELETE FROM {tbl}')
            print('Cleared', tbl)
        except Exception as e:
            print('Skipping', tbl, 'error:', e)
    cur.execute('PRAGMA foreign_keys = ON')
    conn.commit()


def insert_sensor(conn, s):
    cur = conn.cursor()
    cur.execute('INSERT INTO sensors (unique_id, name, sensor_type, location, lorawan_dev_eui, lorawan_application_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', (
        s.get('unique_id'), s.get('name') or s.get('unique_id'), s.get('type') or 'unknown', s.get('location') or 'imported', None, s.get('application_id')
    ))
    sensor_id = cur.lastrowid
    # create battery placeholder
    try:
        cur.execute('INSERT INTO battery_status (sensor_id, battery_percentage, last_seen, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (sensor_id, None, None))
    except Exception:
        pass
    conn.commit()
    return sensor_id


def recreate():
    apps = fetch_apps()
    if not DB.exists():
        raise SystemExit('DB not found: ' + str(DB))
    conn = sqlite3.connect(str(DB))
    wipe_db(conn)
    for app in apps:
        app_id = app.get('application_id')
        sensors = app.get('sensors', [])
        for s in sensors:
            # normalize sensor dict: include application_id
            s['application_id'] = app_id
            insert_sensor(conn, s)
            print('Inserted sensor', s.get('unique_id'))
    conn.close()
    print('Recreation complete')


if __name__ == '__main__':
    recreate()
