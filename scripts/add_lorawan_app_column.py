import os
import sys
import sqlite3

proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(proj_root, 'iot_sensors.db')
# The app config may use a different path; check app.config
if not os.path.exists(db_path):
    # try relative to instance
    db_path = os.path.join(proj_root, 'instance', 'iot_sensors.db')

if not os.path.exists(db_path):
    print('Database file not found at', db_path)
    sys.exit(1)

print('Using DB:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
# Check if column exists
cur.execute("PRAGMA table_info(sensors);")
cols = [r[1] for r in cur.fetchall()]
if 'lorawan_application_id' in cols:
    print('Column already exists; nothing to do.')
else:
    print('Adding column lorawan_application_id to sensors table...')
    cur.execute('ALTER TABLE sensors ADD COLUMN lorawan_application_id TEXT;')
    conn.commit()
    print('Column added.')

conn.close()
