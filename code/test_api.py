"""
MHCEWS API Test Script
Run while Flask server is running on port 5002.
Replace BASE_URL with your ngrok URL for remote testing.
"""
import requests, json

BASE_URL = "http://localhost:5002"
# BASE_URL = "https://your-ngrok-url.ngrok-free.app"

def pretty(resp):
    data = resp.json()
    print(json.dumps(data, indent=2)[:600])
    print(f"  ... status: {resp.status_code}\n")

print("=" * 55)
print("MHCEWS CDC PLACES API Test")
print("=" * 55)

print("\n1. GET / — API info")
pretty(requests.get(f"{BASE_URL}/"))

print("\n2. GET /summary — National statistics")
pretty(requests.get(f"{BASE_URL}/summary"))

print("\n3. GET /zipcodes/98118 — Rainier Valley Seattle")
pretty(requests.get(f"{BASE_URL}/zipcodes/98118"))

print("\n4. GET /zipcodes/risk/High — High risk ZIP codes")
pretty(requests.get(f"{BASE_URL}/zipcodes/risk/High"))

print("\n5. GET /predict/surge — Surge-probable ZIP codes")
pretty(requests.get(f"{BASE_URL}/predict/surge"))

print("\n6. GET /zipcodes?sort=frequent_mental_distress_pct&limit=5")
pretty(requests.get(f"{BASE_URL}/zipcodes?sort=frequent_mental_distress_pct&limit=5"))

print("\n7. GET /zipcodes/risk/Critical — Invalid tier (error handling)")
pretty(requests.get(f"{BASE_URL}/zipcodes/risk/Critical"))

print("\n8. GET /zipcodes/00000 — ZIP not found (error handling)")
pretty(requests.get(f"{BASE_URL}/zipcodes/00000"))
