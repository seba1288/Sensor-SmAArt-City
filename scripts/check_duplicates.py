import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parents[1] / 'instance' / 'iot_sensors.db'
con = sqlite3.connect(str(DB))
cur = con.cursor()
# Look for sensor with id 4 (test_auto_device_001). Adjust if not present.
sensor_id = 4
cur.execute('SELECT id, sensor_id, parameter, value, timestamp, rssi, raw_payload FROM sensor_data WHERE sensor_id=? ORDER BY timestamp DESC LIMIT 20', (sensor_id,))
rows = cur.fetchall()
for r in rows:
    print(r)
con.close()
