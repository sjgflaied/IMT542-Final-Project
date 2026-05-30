"""
MHCEWS API Test Script
Run this while the Flask server is running on port 5002.
Replace BASE_URL with your ngrok URL when testing remotely.
"""

import requests
import json

BASE_URL = "http://localhost:5002"
# BASE_URL = "https://your-ngrok-url.ngrok-free.app"  # replace with your ngrok URL

def pretty(response):
    data = response.json()
    print(json.dumps(data, indent=2)[:600])  # print first 600 chars
    print(f"  ... status: {response.status_code}\n")


print("=" * 50)
print("MHCEWS API Test")
print("=" * 50)

print("\n1. GET / — API info")
pretty(requests.get(f"{BASE_URL}/"))

print("\n2. GET /summary — National statistics")
pretty(requests.get(f"{BASE_URL}/summary"))

print("\n3. GET /states/WA — Washington state")
pretty(requests.get(f"{BASE_URL}/states/WA"))

print("\n4. GET /states/risk/High — High risk states")
pretty(requests.get(f"{BASE_URL}/states/risk/High"))

print("\n5. GET /predict/surge — Surge-probable states")
pretty(requests.get(f"{BASE_URL}/predict/surge"))

print("\n6. GET /states?sort=care_gap — All states sorted by care gap")
pretty(requests.get(f"{BASE_URL}/states?sort=care_gap"))

print("\n7. GET /states/XX — Invalid state (error handling)")
pretty(requests.get(f"{BASE_URL}/states/XX"))
