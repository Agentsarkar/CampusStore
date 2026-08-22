"""
REVISED: Generate 3 months of departure-keyed price history.
For each flight, we generate records for 3 past departure dates
(this month, last month, 2 months ago — all on the same day-of-month as target).
Each departure has 60 days of price history leading UP to that departure.
This lets us compare "days_before_departure" patterns across occurrences.
"""
import json, os, math, random, statistics
from datetime import datetime, timedelta, date

DATA_DIR = 'flight_data'
routes_data = {}
for fname in os.listdir(DATA_DIR):
    if fname.endswith('.json'):
        key = fname.replace('.json', '')
        with open(os.path.join(DATA_DIR, fname)) as f:
            routes_data[key] = json.load(f)

print(f"Loaded {len(routes_data)} routes")

TARGET_DATE = date(2026, 9, 15)   # The date we searched for (Sep 15)
HISTORY_DAYS = 62                  # API gives ~62 days of lookback


def get_flights_for_route(data):
    seen = set()
    unique = []
    for fg in data.get('best_flights', []) + data.get('other_flights', []):
        for leg in fg.get('flights', []):
            fn = leg.get('flight_number', '')
            if fn not in seen:
                seen.add(fn)
                unique.append({
                    'flight_number': fn,
                    'airline': leg.get('airline', ''),
                    'airline_logo': leg.get('airline_logo', ''),
                    'departure_time': leg.get('departure_airport', {}).get('time', ''),
                    'arrival_time': leg.get('arrival_airport', {}).get('time', ''),
                    'duration': fg.get('total_duration', 0),
                    'base_price': fg.get('price', 0),
                })
    return unique


def analyze_price_history(price_history):
    if not price_history:
        return None
    prices = [p['price'] for p in price_history]
    n = len(prices)
    if n < 2:
        return None
    mean = statistics.mean(prices)
    std = statistics.stdev(prices)
    changes = [prices[i] - prices[i-1] for i in range(1, n)]
    avg_change = statistics.mean(changes) if changes else 0
    std_change = statistics.stdev(changes) if len(changes) > 1 else 0
    first_half = statistics.mean(prices[:n//2])
    second_half = statistics.mean(prices[n//2:])
    trend_dir = (second_half - first_half) / first_half if first_half else 0
    spike_freq = sum(1 for p in prices if abs(p - mean) > 1.5 * std) / n
    return {
        'mean': mean, 'std': std,
        'avg_daily_change': avg_change,
        'std_daily_change': std_change,
        'trend_direction': trend_dir,
        'spike_frequency': spike_freq
    }


def generate_departure_history(base_price, trend, flight_number, dep, arr, departure_date, days=62):
    """
    Generate `days` price records leading UP TO `departure_date`.
    recorded_date ranges from (departure_date - days) to (departure_date - 1).
    This mirrors exactly what the SearchAPI returns for a given departure.
    """
    rng = random.Random(hash(f"{flight_number}{departure_date}"))

    if trend:
        mean = trend['mean']
        std = max(trend['std'], mean * 0.02)
        avg_change = trend['avg_daily_change']
        std_change = max(trend['std_daily_change'], mean * 0.02)
        trend_dir = trend['trend_direction']
        spike_freq = trend['spike_frequency']
    else:
        mean = base_price
        std = base_price * 0.15
        avg_change = 0
        std_change = base_price * 0.04
        trend_dir = 0
        spike_freq = 0.05

    records = []
    current_price = mean * rng.uniform(0.88, 1.12)

    for i in range(days):
        days_before_dep = days - i  # counting DOWN to departure
        recorded_date = departure_date - timedelta(days=days_before_dep)

        # Price dynamics based on days_before_departure
        if days_before_dep <= 3:
            # Last 3 days: high urgency — price spikes OR sold out
            urgency = 1.0 + rng.uniform(0.05, 0.20)
        elif days_before_dep <= 7:
            urgency = 1.0 + rng.uniform(0.02, 0.10)
        elif days_before_dep <= 14:
            urgency = 1.0 + rng.uniform(0.00, 0.05)
        else:
            urgency = 1.0

        # Trend pressure
        trend_pressure = (trend_dir / days) * mean * 0.5

        # Random walk
        daily_change = rng.gauss(avg_change, std_change)

        # Spike
        is_spike = rng.random() < spike_freq
        spike_mult = rng.uniform(1.15, 1.40) if is_spike else 1.0

        current_price = (current_price + daily_change + trend_pressure) * urgency * spike_mult
        current_price = max(mean * 0.4, min(mean * 1.9, current_price))

        # Seats: sold out in last 2-5 days before departure (probabilistic)
        sold_out_threshold = rng.randint(2, 6)
        seats_available = days_before_dep > sold_out_threshold

        records.append({
            'flight_number': flight_number,
            'departure_id': dep,
            'arrival_id': arr,
            'departure_date': departure_date.isoformat(),
            'recorded_date': recorded_date.isoformat(),
            'days_before_departure': days_before_dep,
            'price': round(current_price),
            'seats_available': seats_available,
            'source': 'recorded'
        })

    return records


# We generate history for 3 departure instances of the same flight number:
# This month (Sep 15), last month (Aug 15), two months ago (Jul 15)
DEPARTURE_INSTANCES = [
    TARGET_DATE,
    TARGET_DATE.replace(month=TARGET_DATE.month - 1) if TARGET_DATE.month > 1 else TARGET_DATE.replace(year=TARGET_DATE.year-1, month=12),
    TARGET_DATE.replace(month=TARGET_DATE.month - 2) if TARGET_DATE.month > 2 else TARGET_DATE.replace(year=TARGET_DATE.year-1, month=TARGET_DATE.month+10),
]

print(f"Generating records for departure dates: {[d.isoformat() for d in DEPARTURE_INSTANCES]}")

all_records = []
route_summary = {}

for route_key, data in routes_data.items():
    dep, arr = route_key.split('_')
    flights = get_flights_for_route(data)
    price_insights = data.get('price_insights', {})
    price_history = price_insights.get('price_history', [])
    trend = analyze_price_history(price_history)

    td = trend['trend_direction'] if trend else 0
    tm = trend['mean'] if trend else 0
    print(f"\n{dep}->{arr}: {len(flights)} flights, trend_dir={td:.3f}, mean={int(tm)}")

    route_flights = []
    for flight in flights[:4]:
        fn = flight['flight_number']
        bp = flight['base_price']
        airline = flight['airline']

        all_departure_records = []

        for dep_date in DEPARTURE_INSTANCES:
            month_label = "CURRENT" if dep_date == TARGET_DATE else f"{dep_date.strftime('%b').upper()}"
            records = generate_departure_history(bp, trend, fn, dep, arr, dep_date, days=HISTORY_DAYS)
            all_departure_records.extend(records)

            # For CURRENT departure: also store the REAL price_history from API
            if dep_date == TARGET_DATE and price_history:
                for ph in price_history:
                    pdate = ph['iso_date'][:10]
                    # Only add if not already present for this departure
                    existing_dates = {r['recorded_date'] for r in records}
                    if pdate not in existing_dates:
                        all_departure_records.append({
                            'flight_number': fn,
                            'departure_id': dep,
                            'arrival_id': arr,
                            'departure_date': dep_date.isoformat(),
                            'recorded_date': pdate,
                            'days_before_departure': (dep_date - date.fromisoformat(pdate)).days,
                            'price': ph['price'],
                            'seats_available': True,
                            'source': 'api'
                        })

        all_records.extend(all_departure_records)
        print(f"  {fn} ({airline}): {len(all_departure_records)} total records across {len(DEPARTURE_INSTANCES)} departures")

        route_flights.append({
            'flight_number': fn,
            'airline': airline,
            'airline_logo': flight['airline_logo'],
            'departure_time': flight['departure_time'],
            'arrival_time': flight['arrival_time'],
            'duration': flight['duration'],
            'current_price': bp,
            'price_insights': {
                'price_level': price_insights.get('price_level', 'typical'),
                'lowest_price': price_insights.get('lowest_price', bp),
                'typical_price_range': price_insights.get('typical_price_range', {}),
            },
            'real_price_history': price_history,
            'generated_records': all_departure_records
        })

    route_summary[route_key] = {
        'departure_id': dep,
        'arrival_id': arr,
        'flights': route_flights,
        'trend_analysis': trend
    }

with open('dummy_price_history.json', 'w') as f:
    json.dump(route_summary, f, indent=2)

with open('db_seed_records.json', 'w') as f:
    json.dump(all_records, f, indent=2)

print(f"\n\nTotal records generated: {len(all_records)}")
print(f"Records per flight: ~{len(DEPARTURE_INSTANCES)} departures x {HISTORY_DAYS} days = ~{len(DEPARTURE_INSTANCES)*HISTORY_DAYS}")
print("Saved: dummy_price_history.json, db_seed_records.json")

print("""
=== UPDATED SUPABASE SQL ===
CREATE TABLE flight_price_history (
  id BIGSERIAL PRIMARY KEY,
  flight_number TEXT NOT NULL,
  airline TEXT,
  departure_id TEXT NOT NULL,
  arrival_id TEXT NOT NULL,
  departure_date DATE NOT NULL,        -- When this specific flight DEPARTS
  recorded_date DATE NOT NULL,         -- When the price was OBSERVED
  days_before_departure INT,           -- Computed: departure_date - recorded_date
  price INTEGER NOT NULL,
  seats_available BOOLEAN DEFAULT TRUE,
  source TEXT DEFAULT 'recorded',
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Prevents: same price check for same flight on same departure date twice
  UNIQUE (flight_number, departure_id, arrival_id, departure_date, recorded_date)
);

CREATE INDEX idx_fph_flight_dep ON flight_price_history
  (departure_id, arrival_id, flight_number, departure_date, recorded_date);

ALTER TABLE flight_price_history DISABLE ROW LEVEL SECURITY;
""")
