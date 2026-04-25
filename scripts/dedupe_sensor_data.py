"""
Remove duplicate sensor_data rows keeping the earliest id for identical (sensor_id, parameter, value, timestamp).
"""
import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parents[1] / 'instance' / 'iot_sensors.db'
con = sqlite3.connect(str(DB))
cur = con.cursor()
# Count before
cur.execute('SELECT COUNT(*) FROM sensor_data')
before = cur.fetchone()[0]
print('Rows before:', before)
# Delete duplicates
cur.execute("DELETE FROM sensor_data WHERE id NOT IN (SELECT MIN(id) FROM sensor_data GROUP BY sensor_id, parameter, value, timestamp)")
con.commit()
# Count after
cur.execute('SELECT COUNT(*) FROM sensor_data')
after = cur.fetchone()[0]
print('Rows after:', after)
con.close()
