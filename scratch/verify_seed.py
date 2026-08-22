import json

with open('db_seed_records.json') as f:
    records = json.load(f)

# Math breakdown
from collections import Counter
routes = Counter((r['departure_id'], r['arrival_id']) for r in records)
flights = Counter((r['departure_id'], r['arrival_id'], r['flight_number']) for r in records)
departures = Counter((r['departure_id'], r['arrival_id'], r['flight_number'], r['departure_date']) for r in records)
sources = Counter(r['source'] for r in records)

print(f"Total records: {len(records)}")
print(f"Unique routes: {len(routes)}")
print(f"Unique flights: {len(flights)}")
print(f"Unique (flight, departure_date) combos: {len(departures)}")
print(f"Source breakdown: {dict(sources)}")
print()

# Sample a flight to check departure dates stored
sample_fn = records[0]['flight_number']
sample_dep = records[0]['departure_id']
sample_arr = records[0]['arrival_id']
sample_recs = [r for r in records if r['flight_number'] == sample_fn and r['departure_id'] == sample_dep]
dep_dates = sorted(set(r['departure_date'] for r in sample_recs))
print(f"Sample flight {sample_fn} ({sample_dep}->{sample_arr}):")
print(f"  departure_dates in seed: {dep_dates}")
print(f"  records per departure: {Counter(r['departure_date'] for r in sample_recs)}")

# Check if departure_date field exists
print()
print("Sample record structure:")
print(json.dumps(records[0], indent=2))
