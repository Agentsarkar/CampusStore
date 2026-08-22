import requests, json, os, time

API_KEY = 'Go3pknRDn579RRBEDxVXi7B4'
BASE_URL = 'https://www.searchapi.io/api/v1/search'

# 10 major Indian routes - searching ~4 weeks out for good price history
TARGET_DATE = '2026-09-15'

routes = [
    ('CCU', 'BLR'),
    ('CCU', 'DEL'),
    ('CCU', 'BOM'),
    ('BLR', 'DEL'),
    ('BLR', 'BOM'),
    ('DEL', 'BOM'),
    ('DEL', 'HYD'),
    ('DEL', 'MAA'),
    ('BOM', 'HYD'),
    ('BOM', 'MAA'),
]

os.makedirs('flight_data', exist_ok=True)

for dep, arr in routes:
    params = {
        'engine': 'google_flights',
        'api_key': API_KEY,
        'departure_id': dep,
        'arrival_id': arr,
        'outbound_date': TARGET_DATE,
        'flight_type': 'one_way',
        'currency': 'INR',
        'hl': 'en'
    }
    print(f'Fetching {dep} -> {arr}...')
    r = requests.get(BASE_URL, params=params, timeout=30)
    data = r.json()
    with open(f'flight_data/{dep}_{arr}.json', 'w') as f:
        json.dump(data, f, indent=2)
    pi = data.get('price_insights', {})
    ph = pi.get('price_history', [])
    level = pi.get('price_level', 'N/A')
    print(f'  status={r.status_code} | price_level={level} | history_points={len(ph)}')
    time.sleep(1)

print('Done!')
