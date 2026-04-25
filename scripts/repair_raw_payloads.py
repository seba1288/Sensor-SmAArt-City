"""
Repair invalid JSON stored in sensor_data.raw_payload column.
This script opens the SQLite DB directly and attempts to parse raw_payload values that are stored as Python repr (single quotes).
It will try json.loads first; on failure it will try ast.literal_eval to parse Python literals and then write a corrected JSON string.
"""
import sqlite3
import json
import ast
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'instance' / 'iot_sensors.db'

def repair():
    if not DB_PATH.exists():
        print('DB not found at', DB_PATH)
        return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id, raw_payload FROM sensor_data")
    rows = cur.fetchall()
    updated = 0
    for id_, raw in rows:
        if raw is None:
            continue
        # raw may already be valid JSON text; try to load
        try:
            json.loads(raw)
            continue
        except Exception:
            pass
        # try to parse Python literal
        try:
            parsed = ast.literal_eval(raw)
            # ensure parsed is JSON-serializable
            corrected = json.dumps(parsed)
            cur.execute("UPDATE sensor_data SET raw_payload = ? WHERE id = ?", (corrected, id_))
            updated += 1
        except Exception as e:
            # as a last resort, try replacing single quotes with double quotes
            try:
                corrected = raw.replace("'", '"')
                json.loads(corrected)
                cur.execute("UPDATE sensor_data SET raw_payload = ? WHERE id = ?", (corrected, id_))
                updated += 1
            except Exception:
                print('Could not repair id', id_)
    conn.commit()
    conn.close()
    print(f'Repair complete, updated {updated} rows')

if __name__ == '__main__':
    repair()
