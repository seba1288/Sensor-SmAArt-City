import requests
import json

url = 'http://127.0.0.1:5000/api/sensor-data/ingest'
payload = {
    'device_id': 'auto_device_002',
    'dev_eui': 'TESTEUI0001',
    'application_id': 'bodenfeuchte-dragino',
    'timestamp': '2026-04-25T09:00:00Z',
    'data': [
        {'parameter': 'temperature', 'value': 21.3, 'unit': '°C'},
        {'parameter': 'humidity', 'value': 55.2, 'unit': '%'}
    ],
    'signal': {'rssi': -85, 'snr': 7.5},
    'battery': {'percentage': 76, 'voltage': 3.7}
}

r = requests.post(url, json=payload)
print(r.status_code)
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)
