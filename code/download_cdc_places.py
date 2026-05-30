"""
download_cdc_places.py
----------------------
Downloads real CDC PLACES ZCTA mental health data from:
https://data.cdc.gov/resource/qnzd-25i4.json

Filters to 4 mental health measures:
  MHLTH      - Frequent mental distress
  DEPRESSION - Depression prevalence
  EMOTIONSPT - Lack of social/emotional support
  LONELINESS - Loneliness

Saves as: cdc_places_zcta_mh.csv

Run ONCE before starting the API server:
    pip install requests
    python download_cdc_places.py
"""

import requests
import csv
import time

API_URL    = "https://data.cdc.gov/resource/qnzd-25i4.json"
OUT_FILE   = "cdc_places_zcta_mh.csv"
MH_IDS     = ["MHLTH", "DEPRESSION", "EMOTIONSPT", "LONELINESS"]
BATCH_SIZE = 50000

FIELDS = [
    "year", "locationname", "locationid", "datasource",
    "category", "measure", "measureid", "short_question_text",
    "data_value", "data_value_unit", "data_value_type",
    "low_confidence_limit", "high_confidence_limit",
    "totalpopulation", "totalpop18plus", "geolocation"
]

def download():
    all_rows = []
    for measure_id in MH_IDS:
        print(f"Fetching {measure_id}...")
        offset = 0
        while True:
            params = {
                "$where":  f"measureid='{measure_id}'",
                "$limit":  BATCH_SIZE,
                "$offset": offset,
                "$select": ",".join(FIELDS),
            }
            resp = requests.get(API_URL, params=params, timeout=60)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            all_rows.extend(batch)
            print(f"  {measure_id}: fetched {len(all_rows)} rows so far...")
            if len(batch) < BATCH_SIZE:
                break
            offset += BATCH_SIZE
            time.sleep(0.5)

    print(f"\nTotal rows fetched: {len(all_rows)}")

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved to {OUT_FILE}")
    unique_zips = len(set(r.get("locationname") for r in all_rows))
    print(f"Unique ZIP codes: {unique_zips}")

if __name__ == "__main__":
    download()
