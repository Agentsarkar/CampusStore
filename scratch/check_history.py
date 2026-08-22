import json
with open('dummy_price_history.json') as f:
    d = json.load(f)
route = d['CCU_BLR']
for flight in route['flights']:
    ph = flight.get('real_price_history', [])
    if ph:
        fn = flight['flight_number']
        print(f"{fn}: {len(ph)} real points, first={ph[0]['iso_date'][:10]}, last={ph[-1]['iso_date'][:10]}")
        break
