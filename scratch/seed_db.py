"""
Seeds flight_price_history table with 8,380 pre-recorded price records.
Run AFTER creating the table via the SQL in supabase_setup.md.

Math: 10 routes × 4 flights × 3 departures × 62 days = 7,440 recorded
      + 940 api (real SearchAPI price_history for current departure)
      = 8,380 total
"""
import json, os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'server', '.env'))
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_ANON_KEY in server/.env first.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

with open('db_seed_records.json') as f:
    records = json.load(f)

print(f"Seeding {len(records)} records...")

# Validate schema matches new structure
required_fields = {'flight_number', 'departure_id', 'arrival_id', 'departure_date', 'recorded_date', 'price'}
sample = records[0]
missing = required_fields - set(sample.keys())
if missing:
    print(f"ERROR: Seed records missing fields: {missing}")
    print("Re-run scratch/generate_dummy_data.py first.")
    sys.exit(1)

CHUNK = 500
inserted = 0
for i in range(0, len(records), CHUNK):
    batch = records[i:i + CHUNK]
    clean = []
    for r in batch:
        clean.append({
            'flight_number': r['flight_number'],
            'airline': r.get('airline', ''),
            'departure_id': r['departure_id'],
            'arrival_id': r['arrival_id'],
            'departure_date': r['departure_date'],
            'recorded_date': r['recorded_date'],
            'days_before_departure': r.get('days_before_departure'),
            'price': int(r['price']),
            'seats_available': bool(r.get('seats_available', True)),
            'source': r.get('source', 'recorded')
        })
    result = supabase.table('flight_price_history').upsert(
        clean,
        on_conflict='flight_number,departure_id,arrival_id,departure_date,recorded_date'
    ).execute()
    inserted += len(clean)
    print(f"  Batch {i//CHUNK + 1}: inserted {len(clean)} records (total so far: {inserted})")

print(f"\nDone! {inserted} records seeded successfully.")
print("Routes covered: CCU-BLR, CCU-DEL, CCU-BOM, BLR-DEL, BLR-BOM, DEL-BOM, DEL-HYD, DEL-MAA, BOM-HYD, BOM-MAA")
