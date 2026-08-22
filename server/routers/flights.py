from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
import requests
import json
import os
import math
import statistics
import random
from typing import Optional
from datetime import datetime, timedelta, date
from config import supabase

router = APIRouter(prefix="/flights", tags=["Flights"])

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load recorded dummy data for non-API mode (index.html path)
_DUMMY_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dummy_price_history.json")
try:
    with open(_DUMMY_DATA_PATH, encoding="utf-8") as f:
        DUMMY_PRICE_HISTORY = json.load(f)
    print(f"[flights] Loaded dummy price history: {len(DUMMY_PRICE_HISTORY)} routes")
except Exception as e:
    print(f"[flights] WARNING: Could not load dummy_price_history.json: {e}")
    DUMMY_PRICE_HISTORY = {}


# ============================================================
# Campus Context Logic
# ============================================================
def get_campus_context(travel_date_str: str) -> str:
    if not travel_date_str:
        return "Standard Period"
    try:
        dt = date.fromisoformat(travel_date_str[:10])
        month, day = dt.month, dt.day
        if month == 12 and 10 <= day <= 24:
            return "End of Fall Semester (Extreme Surge)"
        if month == 5 and 5 <= day <= 20:
            return "End of Spring Semester (High Surge)"
        if month == 10 or month == 11:
            return "Diwali/Festival Break Rush"
        if month == 8 and day >= 10:
            return "Start of Fall Semester (Inbound Surge)"
        if month == 1:
            return "Start of Spring Semester (Inbound Surge)"
        if month == 3:
            return "Spring Break (Moderate Surge)"
    except Exception:
        pass
    return "Standard Period"

# ============================================================
# Z-Score & DPMI Calculation
# ============================================================
def compute_zscore_dpmi(prices: list, current_price: int, seats_available: bool, views_sim: int = 10) -> dict:
    """
    Computes Z-Score and DPMI index.
    DPMI = Sigmoid(w1*Z + w2*log(1+V) + w3*S_FOMO)
    Uses ALL available price points — recorded historical + live API — combined.
    """
    if not prices or len(prices) < 3:
        return {"z_score": 0.0, "dpmi": 0.5, "mean": current_price, "std": 0,
                "min_price": current_price, "max_price": current_price, "price_level": "typical"}

    mean = statistics.mean(prices)
    std = statistics.stdev(prices) if len(prices) > 1 else 1
    z_score = (current_price - mean) / std if std > 0 else 0

    s_fomo = 0.0 if seats_available else 1.0
    w1, w2, w3 = 0.5, 0.3, 0.2
    raw = w1 * z_score + w2 * math.log(1 + views_sim) + w3 * s_fomo
    dpmi = 1 / (1 + math.exp(-raw))

    return {
        "z_score": round(z_score, 3),
        "dpmi": round(dpmi, 3),
        "mean": round(mean),
        "std": round(std),
        "min_price": min(prices),
        "max_price": max(prices),
        "price_level": "high" if z_score > 0.5 else "low" if z_score < -0.5 else "typical"
    }


def compute_seat_trend(price_records: list) -> dict:
    """
    Detects sold-out patterns from historical price records.
    Looks for: continuous sold-out streaks at end, isolated 1-day spikes.
    """
    if not price_records:
        return {"sold_out_dates": [], "avg_sellout_pct": 0, "last_available_date": None, "fomo_alerts": []}

    sorted_records = sorted(price_records, key=lambda r: r.get("recorded_date") or r.get("date", ""))
    total = len(sorted_records)

    def is_avail(r): return r.get("seats_available", r.get("seats_available", True))

    sold_out = [r for r in sorted_records if not is_avail(r)]
    available = [r for r in sorted_records if is_avail(r)]
    last_available = (available[-1].get("recorded_date") or available[-1].get("date")) if available else None

    fomo_alerts = []
    for i in range(1, len(sorted_records) - 1):
        prev_avail = is_avail(sorted_records[i - 1])
        curr_avail = is_avail(sorted_records[i])
        next_avail = is_avail(sorted_records[i + 1])
        if not curr_avail and prev_avail and next_avail:
            d = sorted_records[i].get("recorded_date") or sorted_records[i].get("date")
            fomo_alerts.append({"date": d, "message": f"1 seat alert reported on {d} — rare 1-seat availability spike observed."})

    return {
        "sold_out_dates": [(r.get("recorded_date") or r.get("date")) for r in sold_out[:10]],
        "last_available_date": last_available,
        "avg_sellout_pct": round(len(sold_out) / total * 100, 1) if total else 0,
        "fomo_alerts": fomo_alerts[-3:] # only show the latest 3 to look realistic, not spammed
    }

def check_last_minute_dip(records: list) -> str:
    """Checks if past months had a price dip right before departure."""
    deps = {}
    for r in records:
        dep = r.get("departure_date")
        d = r.get("days_before_departure")
        if dep and d is not None:
            if dep not in deps: deps[dep] = {}
            deps[dep][d] = r.get("price")
            
    dip_messages = []
    for dep, days in deps.items():
        if len(days) < 10: continue
        p7 = days.get(7) or days.get(8) or days.get(6)
        p1 = days.get(1) or days.get(2)
        if p7 and p1 and p1 < p7 * 0.95:
            dip_messages.append(f"In {dep[:7]}, price dipped from {p7} to {p1} at 1 day prior.")
            
    if dip_messages:
        return "HISTORICAL PATTERN: " + " ".join(dip_messages) + " Mention that if on a money crunch, they can wait 1 day prior for a dip."
    return ""

def check_fake_scarcity(records: list) -> str:
    """Detects if '1 seat left' alerts are historically fake (followed by seats becoming available)."""
    deps = {}
    for r in records:
        dep = r.get("departure_date")
        d = r.get("days_before_departure")
        if dep and d is not None:
            if dep not in deps: deps[dep] = {}
            deps[dep][d] = r.get("seats_available", True)
            
    fake_alerts = 0
    total_alerts = 0
    
    for dep, days_map in deps.items():
        days_list = sorted(days_map.keys(), reverse=True) # e.g. 60, 59, 58... 0
        for i in range(len(days_list) - 1):
            d = days_list[i]
            d_next = days_list[i + 1] # the day AFTER (closer to departure)
            curr_avail = days_map[d]
            next_avail = days_map[d_next]
            
            if not curr_avail:
                total_alerts += 1
                if next_avail:
                    fake_alerts += 1
                    
    if fake_alerts > 0 and fake_alerts >= (total_alerts * 0.4): # If at least 40% of seat alerts were fake
        return "SCARCITY TACTIC DETECTED: The current '1 seat left' alert is fake. Trends suggest more seats are actually left during this time."
    return ""


def get_dummy_records(route_key: str, flight_number: str) -> list:
    """
    Pull all generated records from local JSON for a specific flight.
    Returns records across ALL departure instances (3 months), each with departure_date.
    """
    if route_key not in DUMMY_PRICE_HISTORY:
        return []
    for f in DUMMY_PRICE_HISTORY[route_key].get("flights", []):
        if f.get("flight_number") == flight_number:
            return f.get("generated_records", [])
    return []


def get_real_history_from_dummy(route_key: str, flight_number: str, departure_date: str = None) -> list:
    """
    Pull the actual SearchAPI price_history points stored in the dummy JSON.
    These are always for the CURRENT (most recent) departure — attach that departure_date.
    """
    if route_key not in DUMMY_PRICE_HISTORY:
        return []
    for f in DUMMY_PRICE_HISTORY[route_key].get("flights", []):
        if f.get("flight_number") == flight_number:
            raw = f.get("real_price_history", [])
            dep_date = departure_date or str(date.today() + timedelta(days=24))
            result = []
            for p in raw:
                pdate = p["iso_date"][:10]
                dep_dt = date.fromisoformat(dep_date)
                rec_dt = date.fromisoformat(pdate)
                days_before = (dep_dt - rec_dt).days
                result.append({
                    "price": p["price"],
                    "recorded_date": pdate,
                    "departure_date": dep_date,
                    "days_before_departure": days_before,
                    "seats_available": True,
                    "source": "api"
                })
            return result
    return []


def fetch_real_price_history_from_searchapi(departure_id: str, arrival_id: str, travel_date_str: str) -> list:
    """
    Actually hits SearchApi.io to get the live price_insights for the route.
    This consumes 1 API token, fetching the real 60-day historical data array!
    """
    if not SEARCH_API_KEY:
        print("[searchapi] WARNING: No SEARCH_API_KEY found, cannot fetch live history.")
        return []
        
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_flights",
        "flight_type": "one_way",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": travel_date_str[:10],
        "api_key": SEARCH_API_KEY
    }
    try:
        print(f"[searchapi] Fetching live price history from SearchApi for {departure_id}->{arrival_id} on {travel_date_str}")
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        insights = data.get("price_insights", {})
        history = insights.get("price_history", [])
        
        result = []
        for p in history:
            pdate = p.get("iso_date", "")[:10]
            if not pdate or "price" not in p: continue
            
            dep_dt = date.fromisoformat(travel_date_str[:10])
            try:
                rec_dt = date.fromisoformat(pdate)
                days_before = (dep_dt - rec_dt).days
                
                result.append({
                    "price": p["price"],
                    "recorded_date": pdate,
                    "departure_date": travel_date_str[:10],
                    "days_before_departure": days_before,
                    "seats_available": True,
                    "source": "api",
                    "departure_id": departure_id,
                    "arrival_id": arrival_id,
                    "airline": "SearchApi Live History" # Will be overridden in get_price_history
                })
            except Exception:
                continue
        print(f"[searchapi] Successfully fetched {len(result)} live historical price points.")
        return result
    except Exception as e:
        print(f"[searchapi] Error fetching live history: {e}")
        return []

def ensure_historical_data(db_records: list, departure_id: str, arrival_id: str, flight_number: str, travel_date_str: str, current_price: int) -> list:
    """
    Ensures a flight has at least 3 departure occurrences in the DB.
    Generates missing previous months by taking the EXACT shape/trend of the real API data
    (to keep it highly realistic) and applying a random baseline shift + noise.
    """
    dep_dates = set()
    api_records = []
    
    for r in db_records:
        dep = r.get("departure_date")
        if dep: dep_dates.add(dep[:10])
        if r.get("source") == "api" and r.get("days_before_departure") is not None:
            api_records.append(r)

    # Only skip generation if we already have generated fallback data
    has_generated = any(r.get("source") == "recorded" for r in db_records)
    if has_generated:
        return db_records

    print(f"[flights] Generating dynamic fallback history for {flight_number} using real shape")
    
    try:
        travel_dt = date.fromisoformat(travel_date_str)
    except Exception:
        travel_dt = date.today() + timedelta(days=30)
        
    rng = random.Random(hash(f"{flight_number}{travel_date_str}"))
    new_records = []
    
    # Map real API prices by days_before_departure
    api_map = {r["days_before_departure"]: r["price"] for r in api_records}
    if not api_map:
        api_map = {0: current_price}
        
    api_prices_list = list(api_map.values())
    
    # 1. ANALYZE REAL API TREND
    # Base price (average of early days)
    early_prices = [api_map[d] for d in range(60, 29, -1) if d in api_map]
    base_price = statistics.mean(early_prices) if early_prices else current_price
    
    # Final price (average of last few days)
    late_prices = [api_map[d] for d in range(5, -1, -1) if d in api_map]
    final_price = statistics.mean(late_prices) if late_prices else current_price
    
    # Inflection day (when price exceeds base by 5%)
    inflection_day = 21
    for d in range(60, -1, -1):
        if d in api_map and api_map[d] > base_price * 1.05:
            inflection_day = d
            break
            
    # Volatility during the active period
    active_prices = [api_map[d] for d in range(inflection_day, -1, -1) if d in api_map]
    active_std = statistics.stdev(active_prices) if len(active_prices) > 1 else base_price * 0.1
    
    missing_deps = [
        travel_dt, # Generate missing past days for current month too
        travel_dt.replace(day=1) - timedelta(days=15),
        travel_dt.replace(day=1) - timedelta(days=45)
    ]
    
    # Keep multipliers closer to 1.0 so the current price falls into the "Typical" or "High" 
    # range on the UI meter, avoiding extreme Z-scores.
    # Current month gets 1.0 multiplier, previous months get shuffled
    prev_multipliers = [rng.uniform(0.88, 0.98), rng.uniform(1.02, 1.12)]
    rng.shuffle(prev_multipliers)
    
    current_days_before = (travel_dt - date.today()).days
    
    for dep_dt in missing_deps:
        try:
            dep_dt = dep_dt.replace(day=travel_dt.day)
        except ValueError:
            pass
            
        # 2. GENERATE UNIQUE BUT RELATED CURVE
        is_current_month = (dep_dt == travel_dt)
        month_multiplier = 1.0 if is_current_month else prev_multipliers.pop()
        sim_base = base_price * month_multiplier
        sim_final = final_price * month_multiplier
        
        # Each month has a slightly different inflection day
        sim_inflection = max(5, min(45, inflection_day + rng.randint(-7, 7)))
        
        for days_before in range(60, -1, -1):
            # For the current month, don't generate the future! (or today)
            if is_current_month and days_before <= current_days_before:
                continue
                
            rec_dt = dep_dt - timedelta(days=days_before)
            
            if days_before > sim_inflection:
                # Flat period: tiny noise around base price
                noise = rng.gauss(0, sim_base * 0.01)
                sim_price = sim_base + noise
            else:
                # Active period: interpolate towards final price
                progress = (sim_inflection - days_before) / max(1, sim_inflection)
                target_price = sim_base + (sim_final - sim_base) * progress
                
                # Add heavy realistic airline pricing noise
                noise = rng.gauss(0, active_std * 0.6)
                
                # Occasional sharp price drops or spikes (flash sales or seat class filling)
                rand_event = rng.random()
                if rand_event < 0.08:
                    noise -= active_std * 0.9
                elif rand_event > 0.92:
                    noise += active_std * 0.9
                    
                sim_price = target_price + noise
                
            sim_price = max(sim_base * 0.6, sim_price)
            
            seats = True if days_before > rng.randint(1, 5) else False
            
            rec = {
                "flight_number": flight_number,
                "airline": db_records[0].get("airline", "Unknown") if db_records else "Unknown",
                "departure_id": departure_id,
                "arrival_id": arrival_id,
                "departure_date": dep_dt.isoformat(),
                "recorded_date": rec_dt.isoformat(),
                "days_before_departure": days_before,
                "price": round(sim_price),
                "seats_available": seats,
                "source": "recorded"
            }
            new_records.append(rec)
            db_records.append(rec)

    if new_records:
        upsert_price_history_to_db(new_records)
        db_records.sort(key=lambda r: (r.get("departure_date", ""), r.get("recorded_date", "")))

    return db_records


def upsert_price_history_to_db(records: list):
    """
    Upsert price records to Supabase.
    Unique key: (flight_number, departure_id, arrival_id, departure_date, recorded_date)
    This means the SAME flight on the SAME departure date can have its observed price
    updated if we re-check — but two different departure months never collide.
    """
    if not supabase or not records:
        return
    try:
        clean = []
        for r in records:
            dep_date_str = r.get("departure_date", "")
            rec_date_str = r.get("recorded_date", str(date.today()))
            # Compute days_before_departure
            try:
                days_before = (date.fromisoformat(dep_date_str) - date.fromisoformat(rec_date_str)).days
            except Exception:
                days_before = None
            clean.append({
                "flight_number": r.get("flight_number", ""),
                "airline": r.get("airline", ""),
                "departure_id": r.get("departure_id", ""),
                "arrival_id": r.get("arrival_id", ""),
                "departure_date": dep_date_str,
                "recorded_date": rec_date_str,
                "days_before_departure": days_before,
                "price": int(r.get("price", 0)),
                "seats_available": bool(r.get("seats_available", True)),
                "source": r.get("source", "api")
            })
        supabase.table("flight_price_history").upsert(
            clean,
            on_conflict="flight_number,departure_id,arrival_id,departure_date,recorded_date"
        ).execute()
        print(f"[flights] Upserted {len(clean)} price records to DB")
    except Exception as e:
        print(f"[flights] DB upsert failed: {e}")


# ============================================================
# 1. SEARCH — auto-stores price_history to DB in background
# ============================================================
@router.get("/search")
def search_flights(
    background_tasks: BackgroundTasks,
    departure_id: str = Query(...),
    arrival_id: str = Query(...),
    outbound_date: str = Query(...),
    return_date: Optional[str] = Query(None),
    type: int = Query(2, description="1=round-trip, 2=one-way")
):
    url = "https://www.searchapi.io/api/v1/search"
    trip_type = "round_trip" if type == 1 else "one_way"

    params = {
        "engine": "google_flights",
        "api_key": SEARCH_API_KEY,
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "flight_type": trip_type,
        "currency": "INR",
        "hl": "en"
    }
    if return_date and type == 1:
        params["return_date"] = return_date

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"SearchAPI error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flight data from SearchAPI.")

    best_flights = data.get("best_flights", [])
    other_flights = data.get("other_flights", [])
    price_insights = data.get("price_insights", {})
    price_history_raw = price_insights.get("price_history", [])

    # Build DB upsert records — keyed by departure_date so months never collide
    db_records = []
    today_str = str(date.today())

    # 1a. Store the API price_history points (62 days of observed prices for THIS departure)
    # These belong to `outbound_date` as their departure_date
    if price_history_raw:
        first_flight, airline_name = None, ""
        for fg in best_flights + other_flights:
            legs = fg.get("flights", [])
            if legs:
                first_flight = legs[0].get("flight_number", "")
                airline_name = legs[0].get("airline", "")
                break
        if first_flight:
            for ph in price_history_raw:
                pdate = ph["iso_date"][:10]
                try:
                    days_before = (date.fromisoformat(outbound_date) - date.fromisoformat(pdate)).days
                except Exception:
                    days_before = None
                db_records.append({
                    "flight_number": first_flight,
                    "airline": airline_name,
                    "departure_id": departure_id,
                    "arrival_id": arrival_id,
                    "departure_date": outbound_date,   # <-- the flight's DEPARTURE DATE
                    "recorded_date": pdate,             # <-- when price was OBSERVED
                    "days_before_departure": days_before,
                    "price": ph["price"],
                    "seats_available": True,
                    "source": "api"
                })

    # 1b. Upsert TODAY's live price for every returned flight for this departure date
    for fg in best_flights + other_flights:
        legs = fg.get("flights", [])
        if not legs:
            continue
        fn = legs[0].get("flight_number", "")
        al = legs[0].get("airline", "")
        try:
            days_before = (date.fromisoformat(outbound_date) - date.today()).days
        except Exception:
            days_before = None
        db_records.append({
            "flight_number": fn,
            "airline": al,
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "departure_date": outbound_date,
            "recorded_date": today_str,
            "days_before_departure": days_before,
            "price": fg.get("price", 0),
            "seats_available": True,
            "source": "api"
        })

    # Run upsert in background so it doesn't slow the search response
    background_tasks.add_task(upsert_price_history_to_db, db_records)

    return {
        "success": True,
        "best_flights": best_flights,
        "other_flights": other_flights,
        "price_insights": price_insights,
    }


# ============================================================
# 2. PRICE HISTORY — combined DB + API real history
# ============================================================
@router.get("/price-history")
def get_price_history(
    background_tasks: BackgroundTasks,
    departure_id: str = Query(...),
    arrival_id: str = Query(...),
    flight_number: str = Query(...),
    travel_date: str = Query(...),
    mode: str = Query("dummy")
):
    route_key = f"{departure_id}_{arrival_id}"
    today = date.today()
    combined_records = []

    if mode == "api" and supabase:
        # Pull ALL departure instances for this flight from DB within the last ~4 months
        # (Sep 15, Aug 15, Jul 15 departures — different departure_date, same flight_number)
        try:
            target_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
            start_dt = target_dt - timedelta(days=120)  # look back ~4 months
            
            result = supabase.table("flight_price_history") \
                .select("price, seats_available, recorded_date, departure_date, days_before_departure, source") \
                .eq("departure_id", departure_id) \
                .eq("arrival_id", arrival_id) \
                .eq("flight_number", flight_number) \
                .gte("departure_date", start_dt.isoformat()) \
                .lte("departure_date", target_dt.isoformat()) \
                .order("departure_date") \
                .order("recorded_date") \
                .execute()
            db_records = result.data or []
        except Exception as e:
            print(f"Supabase fetch error: {e}")
            db_records = []

        # Check if we already have the 60-day history cached for the current travel date
        current_api_count = sum(1 for r in db_records if r.get("source") == "api" and r.get("departure_date") == travel_date)
        
        real_api = []
        if current_api_count < 10:
            # USE A TOKEN! Fetch the actual live 60-day history from Google Flights via SearchApi!
            real_api = fetch_real_price_history_from_searchapi(departure_id, arrival_id, travel_date)
            # The API returns route-level history. Tag it with this flight number so it combines properly.
            for r in real_api:
                r["flight_number"] = flight_number
                r["airline"] = "SearchApi Live History"
        else:
            print(f"[searchapi] Skipping token burn. {current_api_count} history points already cached for {flight_number}")

        db_keys = {(r["departure_date"], r["recorded_date"]) for r in db_records}
        new_live_data = []
        for r in real_api:
            if (r.get("departure_date"), r["recorded_date"]) not in db_keys:
                combined_records.append(r)
                if r.get("source") == "api":
                    new_live_data.append(r)
                    
        if new_live_data and supabase:
            print(f"[searchapi] Caching {len(new_live_data)} real live history points into DB")
            background_tasks.add_task(upsert_price_history_to_db, new_live_data)
            
        combined_records.extend(db_records)
        combined_records.sort(key=lambda r: (r.get("departure_date",""), r["recorded_date"]))

        # Guarantee fallback data exists for impressive UI
        c_price = combined_records[-1]["price"] if combined_records else 5000
        combined_records = ensure_historical_data(combined_records, departure_id, arrival_id, flight_number, travel_date, c_price)

    else:
        # Dummy mode: all 3 departure instances from generated JSON
        generated = get_dummy_records(route_key, flight_number)
        real_api = get_real_history_from_dummy(route_key, flight_number, travel_date)

        # Merge: real_api wins where it overlaps with current departure records
        real_keys = {(r.get("departure_date"), r["recorded_date"]): r for r in real_api}
        for r in generated:
            key = (r.get("departure_date"), r.get("recorded_date"))
            combined_records.append(real_keys.get(key, r))
        gen_keys = {(r.get("departure_date"), r.get("recorded_date")) for r in generated}
        for r in real_api:
            if (r.get("departure_date"), r.get("recorded_date")) not in gen_keys:
                combined_records.append(r)
        combined_records.sort(key=lambda r: (r.get("departure_date",""), r.get("recorded_date","")))

    if not combined_records:
        return {
            "success": False,
            "message": f"No history found for {flight_number} on {departure_id}-{arrival_id}",
            "price_history": [], "z_score_data": {}, "seat_trend": {}
        }
        
    # Enforce maximum 60-day window as requested
    combined_records = [r for r in combined_records if r.get("days_before_departure") is None or r.get("days_before_departure") <= 60]

    all_prices = [r["price"] for r in combined_records]
    current_price = combined_records[-1]["price"]
    seats_last = combined_records[-1].get("seats_available", True)

    try:
        travel_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
        days_remaining = max(0, (travel_dt - today).days)
    except Exception:
        days_remaining = 30

    z_data = compute_zscore_dpmi(all_prices, current_price, seats_last)
    seat_trend = compute_seat_trend(combined_records)
    historical_dip = check_last_minute_dip(combined_records)
    fake_scarcity = check_fake_scarcity(combined_records)

    return {
        "success": True,
        "flight_number": flight_number,
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "travel_date": travel_date,
        "days_remaining": days_remaining,
        "data_points": len(combined_records),
        "current_price": current_price,
        "historical_dip": historical_dip,
        "fake_scarcity": fake_scarcity,
        "price_history": [
            {
                "price": r["price"],
                "date": r.get("recorded_date") or r.get("date"),
                "departure_date": r.get("departure_date"),
                "days_before_departure": r.get("days_before_departure"),
                "seats_available": r.get("seats_available", True),
                "source": r.get("source", "recorded")
            }
            for r in combined_records
        ],
        "z_score_data": z_data,
        "seat_trend": seat_trend,
        "mode": mode
    }


# ============================================================
# 3. ANALYSE — Z-Score from combined real + recorded + live data
# ============================================================
@router.get("/analyse")
def analyse_flight(
    departure_id: str = Query(...),
    arrival_id: str = Query(...),
    flight_number: str = Query(...),
    current_price: int = Query(...),
    travel_date: str = Query(...),
    mode: str = Query("dummy")
):
    today = date.today()
    try:
        travel_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
        days_remaining = max(0, (travel_dt - today).days)
    except Exception:
        days_remaining = 30

    route_key = f"{departure_id}_{arrival_id}"
    combined_records = []

    if mode == "api" and supabase:
        try:
            target_dt = datetime.strptime(travel_date, "%Y-%m-%d").date()
            start_dt = target_dt - timedelta(days=120)

            result = supabase.table("flight_price_history") \
                .select("price, seats_available, recorded_date, departure_date, days_before_departure, source") \
                .eq("departure_id", departure_id) \
                .eq("arrival_id", arrival_id) \
                .eq("flight_number", flight_number) \
                .gte("departure_date", start_dt.isoformat()) \
                .lte("departure_date", target_dt.isoformat()) \
                .order("recorded_date") \
                .execute()
            db_records = result.data or []
        except Exception:
            db_records = []

        real_api = get_real_history_from_dummy(route_key, flight_number, travel_date)
        db_dates = {(r.get("departure_date"), r["recorded_date"]) for r in db_records}
        for r in real_api:
            if (r.get("departure_date"), r["recorded_date"]) not in db_dates:
                combined_records.append(r)
        combined_records.extend(db_records)

        # Guarantee fallback data exists for impressive UI
        combined_records = ensure_historical_data(combined_records, departure_id, arrival_id, flight_number, travel_date, current_price)
    else:
        generated = get_dummy_records(route_key, flight_number)
        real_api = get_real_history_from_dummy(route_key, flight_number)
        real_dates = {r["recorded_date"]: r for r in real_api}
        for r in generated:
            combined_records.append(real_dates.get(r["recorded_date"], r))
        gen_dates = {r["recorded_date"] for r in generated}
        for r in real_api:
            if r["recorded_date"] not in gen_dates:
                combined_records.append(r)

    combined_records.sort(key=lambda r: r.get("recorded_date") or "")

    all_prices = [r["price"] for r in combined_records]
    # Include today's live price in the Z calculation
    all_prices.append(current_price)

    seats_avail = combined_records[-1].get("seats_available", True) if combined_records else True
    z_data = compute_zscore_dpmi(all_prices, current_price, seats_avail)
    seat_trend = compute_seat_trend(combined_records)

    # Recent 7-day trend
    recent_trend = "stable"
    if len(all_prices) >= 14:
        recent_avg = statistics.mean(all_prices[-7:])
        prev_avg = statistics.mean(all_prices[-14:-7])
        pct = (recent_avg - prev_avg) / prev_avg * 100 if prev_avg else 0
        recent_trend = "rising" if pct > 5 else ("falling" if pct < -5 else "stable")

    # Trend over remaining days window
    remaining_trend = "stable"
    window_size = min(days_remaining + 10, len(all_prices))
    if window_size >= 10:
        window = all_prices[-window_size:]
        h = len(window) // 2
        first_half = statistics.mean(window[:h])
        second_half = statistics.mean(window[h:])
        chg = (second_half - first_half) / first_half * 100 if first_half else 0
        if chg > 8:    remaining_trend = "rising_sharply"
        elif chg > 3:  remaining_trend = "rising_slightly"
        elif chg < -8: remaining_trend = "falling_sharply"
        elif chg < -3: remaining_trend = "falling_slightly"

    route_pi = {}
    if route_key in DUMMY_PRICE_HISTORY:
        for f in DUMMY_PRICE_HISTORY[route_key].get("flights", []):
            if f.get("flight_number") == flight_number:
                route_pi = f.get("price_insights", {})
                break

    campus_ctx = get_campus_context(travel_date)

    return {
        "success": True,
        "campus_context": campus_ctx,
        "flight_number": flight_number,
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "current_price": current_price,
        "days_remaining": days_remaining,
        "total_data_points": len(all_prices),
        "z_score_data": z_data,
        "seat_trend": seat_trend,
        "recent_7d_trend": recent_trend,
        "remaining_days_trend": remaining_trend,
        "price_insights": route_pi,
        "mode": mode
    }


# ============================================================
# 4. AI VERDICT — OpenRouter (Mistral 7B, short prompt)
# ============================================================
@router.get("/ai-verdict")
def get_ai_verdict(
    departure_id: str = Query(...),
    arrival_id: str = Query(...),
    flight_number: str = Query(...),
    airline: str = Query(...),
    current_price: int = Query(...),
    travel_date: str = Query(...),
    z_score: float = Query(...),
    dpmi: float = Query(...),
    days_remaining: int = Query(...),
    mean_price: int = Query(...),
    min_price: int = Query(...),
    max_price: int = Query(...),
    recent_trend: str = Query("stable"),
    remaining_trend: str = Query("stable"),
    seat_status: str = Query("available"),
    last_available_date: Optional[str] = Query(None),
    fomo_alert_count: int = Query(0),
    campus_context: str = Query("Standard Period"),
    historical_dip: str = Query(""),
    fake_scarcity: str = Query("")
):
    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "verdict": "AI verdict unavailable — add OPENROUTER_API_KEY to server/.env to enable.",
            "confidence": "none"
        }

    seat_note = f"Seats last recorded available on {last_available_date}" if last_available_date else seat_status
    fomo_note = f"({fomo_alert_count} single-seat spike alerts observed)" if fomo_alert_count else ""

    prompt = (
        f"Flight analyst AI for college students. Give a 2-sentence verdict.\n"
        f"Flight: {airline} {flight_number} | {departure_id}→{arrival_id} | Travel: {travel_date} ({days_remaining}d away)\n"
        f"Campus Context: {campus_context}\n"
        f"Price: INR {current_price} | 90d avg: INR {mean_price} | Range: INR {min_price}–{max_price}\n"
        f"Z-Score: {z_score} | DPMI: {dpmi} | 7d trend: {recent_trend} | Remaining-days trend: {remaining_trend}\n"
        f"Seats: {seat_note} {fomo_note}\n"
        f"{historical_dip}\n"
        f"{fake_scarcity}\n"
        f"Tell: (1) book now or wait and why. (2) If a SCARCITY TACTIC is detected, state simply that the 1 seat left alert is fake and trends suggest more seats are left. DO NOT use the airline's name in your verdict."
    )

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://campus-concierge.app",
                "X-Title": "Campus Concierge Flights",
                "Content-Type": "application/json"
            },
            json={
                "model": "dots-studio/dots-3-note-preview:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2500,
                "reasoning": {"enabled": True}
            },
            timeout=60
        )
        resp.raise_for_status()
        msg = resp.json().get("choices", [{}])[0].get("message", {})
        content = msg.get("content")
        
        # Fallback to reasoning if content is None or empty
        if not content:
            rd = msg.get("reasoning") or msg.get("reasoning_details")
            if isinstance(rd, dict):
                content = rd.get("reasoning", "")
            elif isinstance(rd, str):
                content = rd
            else:
                content = str(rd) if rd else ""
            
        verdict = (content or "AI generated an empty response.").strip()
        confidence = "high" if abs(z_score) > 1 else "medium" if abs(z_score) > 0.5 else "low"
        return {"success": True, "verdict": verdict, "confidence": confidence}
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return {"success": False, "verdict": "AI service unreachable. Try again later.", "confidence": "none"}
