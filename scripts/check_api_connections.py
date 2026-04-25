"""
Check API connectivity for entries in ingestion_worker/credentials.json.
For each credential entry, derive the base API host from `api_endpoint` (or default)
and call GET /api/applications to validate reachability and sample returned data.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests

ROOT = Path(__file__).resolve().parents[1]
CRED = ROOT / 'ingestion_worker' / 'credentials.json'
DEFAULT_ENDPOINT = os.environ.get('API_ENDPOINT', 'http://localhost:5000/api/sensor-data/ingest')


def load_credentials():
    if not CRED.exists():
        print('Credentials file not found at', CRED)
        return {}
    with CRED.open('r', encoding='utf-8') as f:
        return json.load(f)


def check_endpoint_for_key(name, cfg):
    endpoint = cfg.get('api_endpoint') if isinstance(cfg, dict) else None
    if not endpoint:
        endpoint = DEFAULT_ENDPOINT
    parsed = urlparse(endpoint)
    base = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else endpoint
    apps_url = urljoin(base, '/api/applications')
    headers = {'Accept': 'application/json'}
    # If an API key is configured, add it
    api_key = None
    header_name = None
    if isinstance(cfg, dict):
        api_key = cfg.get('api_key')
        header_name = cfg.get('api_key_header')
    if api_key:
        if header_name and header_name.lower() == 'authorization':
            if not api_key.lower().startswith('bearer '):
                headers['Authorization'] = f'Bearer {api_key}'
            else:
                headers['Authorization'] = api_key
        else:
            headers[header_name or 'X-API-Key'] = api_key

    print(f'Checking [{name}] -> {apps_url} with headers: {list(headers.keys())}')
    try:
        r = requests.get(apps_url, headers=headers, timeout=5)
        print('  Status:', r.status_code)
        if r.status_code == 200:
            try:
                j = r.json()
                print('  Returned applications:', len(j))
                # print a small sample
                for app in j[:3]:
                    app_id = app.get('application_id')
                    sensors = app.get('sensors', [])
                    print(f'    - {app_id}: {len(sensors)} sensors')
            except Exception as e:
                print('  Failed to parse JSON:', e)
        else:
            print('  Response text:', r.text[:200])
    except Exception as e:
        print('  Error connecting:', e)


if __name__ == '__main__':
    creds = load_credentials()
    if not creds:
        print('No credentials to check; using default endpoint only')
        creds = {'default': {}}
    for name, cfg in creds.items():
        check_endpoint_for_key(name, cfg)
    # Also check default
    if 'default' not in creds:
        check_endpoint_for_key('default', {})
