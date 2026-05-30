"""
MHCEWS Flask API Server
Mental Health Crisis Early-Warning System
-----------------------------------------
Data Source: CDC PLACES ZCTA Data 2024 Release
API: https://data.cdc.gov/resource/qnzd-25i4.json

Run:
    pip install flask
    python mhcews_api.py

Endpoints:
    GET /                         - API info
    GET /zipcodes                 - All ZIP codes with risk scores
    GET /zipcodes/<zip>           - Single ZIP code e.g. /zipcodes/98118
    GET /zipcodes/risk/<tier>     - Filter by High / Moderate / Low
    GET /summary                  - National summary statistics
    GET /predict/surge            - ZIP codes flagged as surge-probable
    GET /refresh                  - Re-load data from CSV
"""

from flask import Flask, jsonify, request
import csv, json
from statistics import mean

app = Flask(__name__)

DATA_FILE  = "cdc_places_zcta_mh.csv"
API_SOURCE = "https://data.cdc.gov/resource/qnzd-25i4.json"
MODEL_VER  = "mhcews-v2.0.0"
DATA_YEAR  = "2023"

MH_MEASURES = {
    "MHLTH":      "frequent_mental_distress_pct",
    "DEPRESSION": "depression_pct",
    "EMOTIONSPT": "lack_emotional_support_pct",
    "LONELINESS": "loneliness_pct",
}

def load_data(filepath=DATA_FILE):
    zip_map = {}
    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            zc  = row.get("locationname", "").strip()
            mid = row.get("measureid",    "").strip()
            val = row.get("data_value",   "").strip()
            pop = row.get("totalpopulation", "").strip()
            lo  = row.get("low_confidence_limit",  "").strip()
            hi  = row.get("high_confidence_limit", "").strip()
            lat = lon = ""
            geo = row.get("geolocation", "")
            if geo and "coordinates" in str(geo):
                try:
                    g   = json.loads(geo)
                    lon = g["coordinates"][0]
                    lat = g["coordinates"][1]
                except Exception:
                    pass
            if not zc or mid not in MH_MEASURES:
                continue
            if zc not in zip_map:
                zip_map[zc] = {
                    "zip_code":         zc,
                    "total_population": int(pop) if pop.isdigit() else None,
                    "latitude":  lat, "longitude": lon,
                    "data_source":   "CDC PLACES ZCTA 2024 Release",
                    "api_endpoint":  API_SOURCE,
                    "survey_year":   DATA_YEAR,
                    "model_version": MODEL_VER,
                }
            field = MH_MEASURES[mid]
            try:
                zip_map[zc][field]              = float(val)
                zip_map[zc][field+"_ci_low"]    = float(lo) if lo else None
                zip_map[zc][field+"_ci_high"]   = float(hi) if hi else None
            except ValueError:
                zip_map[zc][field] = None
    records = list(zip_map.values())
    print(f"[Load] {len(records)} ZIP codes loaded.")
    return records

def enrich(records):
    valid = [r for r in records
             if r.get("frequent_mental_distress_pct") is not None
             and r.get("depression_pct") is not None]
    avg_d  = mean(r["frequent_mental_distress_pct"] for r in valid)
    avg_dp = mean(r["depression_pct"]               for r in valid)
    avg_lo = mean(r["loneliness_pct"] for r in valid if r.get("loneliness_pct") is not None)
    avg_es = mean(r["lack_emotional_support_pct"] for r in valid if r.get("lack_emotional_support_pct") is not None)

    for r in records:
        d  = r.get("frequent_mental_distress_pct")
        dp = r.get("depression_pct")
        lo = r.get("loneliness_pct")
        es = r.get("lack_emotional_support_pct")

        r["care_gap"] = round(d * (es / 100), 2) if d and es else None

        if d and dp:
            s  = (d  / avg_d)  * 40
            s += (dp / avg_dp) * 35
            s += (lo / avg_lo) * 25 if lo else 0
            r["risk_score"] = round(s, 1)
        else:
            r["risk_score"] = None

        s = r["risk_score"]
        r["risk_tier"] = (
            "High"     if s and s >= 110 else
            "Moderate" if s and s >= 95  else
            "Low"      if s              else "Unknown"
        )
        r["surge_probable"] = bool(
            d  and d  > avg_d  and
            dp and dp > avg_dp
        )

    print(f"[Enrich] Done. avg_distress={round(avg_d,2)}% avg_depression={round(avg_dp,2)}%")
    return records, avg_d, avg_dp, avg_lo, avg_es

# ── Bootstrap ──────────────────────────────────────────────────
try:
    _raw = load_data()
    RECORDS, AVG_D, AVG_DP, AVG_LO, AVG_ES = enrich(_raw)
    BY_ZIP = {r["zip_code"]: r for r in RECORDS}
except Exception as e:
    print(f"[ERROR] {e}")
    RECORDS = []; BY_ZIP = {}
    AVG_D = AVG_DP = AVG_LO = AVG_ES = 0

# ── Endpoints ──────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "api":              "Mental Health Crisis Early-Warning System (MHCEWS)",
        "version":          MODEL_VER,
        "data_source":      "CDC PLACES ZCTA Data 2024 Release",
        "api_source":       API_SOURCE,
        "license":          "CC BY 4.0",
        "zip_codes_loaded": len(RECORDS),
        "endpoints": {
            "GET /zipcodes":             "All ZIP codes with risk scores",
            "GET /zipcodes/<zip>":       "Single ZIP e.g. /zipcodes/98118",
            "GET /zipcodes/risk/<tier>": "Filter by High / Moderate / Low",
            "GET /summary":              "National summary statistics",
            "GET /predict/surge":        "ZIP codes flagged as surge-probable",
            "GET /refresh":              "Re-load data from CSV",
        }
    })

@app.route("/zipcodes")
def get_all():
    sort_by = request.args.get("sort", "risk_score")
    desc    = request.args.get("order", "desc") == "desc"
    limit   = request.args.get("limit", None)
    if sort_by not in ("risk_score","care_gap","frequent_mental_distress_pct","depression_pct","zip_code"):
        sort_by = "risk_score"
    out = sorted(RECORDS, key=lambda r: r.get(sort_by) or 0, reverse=desc)
    if limit:
        try: out = out[:int(limit)]
        except ValueError: pass
    return jsonify({"count": len(out), "sort_by": sort_by, "data": out})

@app.route("/zipcodes/<zip_code>")
def get_zip(zip_code):
    r = BY_ZIP.get(zip_code.strip())
    if not r:
        return jsonify({"error": f"ZIP code '{zip_code}' not found."}), 404
    return jsonify(r)

@app.route("/zipcodes/risk/<tier>")
def get_by_tier(tier):
    t = tier.capitalize()
    if t not in ("High","Moderate","Low"):
        return jsonify({"error": "tier must be High, Moderate, or Low"}), 400
    out = sorted([r for r in RECORDS if r.get("risk_tier")==t],
                 key=lambda r: r.get("risk_score") or 0, reverse=True)
    return jsonify({"tier": t, "count": len(out), "data": out})

@app.route("/summary")
def get_summary():
    valid = [r for r in RECORDS if r.get("risk_score")]
    high  = [r for r in RECORDS if r.get("risk_tier")=="High"]
    mod   = [r for r in RECORDS if r.get("risk_tier")=="Moderate"]
    low   = [r for r in RECORDS if r.get("risk_tier")=="Low"]
    surge = [r for r in RECORDS if r.get("surge_probable")]
    return jsonify({
        "total_zip_codes":                  len(RECORDS),
        "national_avg_mental_distress_pct": round(AVG_D,  2),
        "national_avg_depression_pct":      round(AVG_DP, 2),
        "national_avg_loneliness_pct":      round(AVG_LO, 2),
        "national_avg_lack_support_pct":    round(AVG_ES, 2),
        "risk_tier_breakdown": {"High": len(high), "Moderate": len(mod), "Low": len(low)},
        "surge_probable_count": len(surge),
        "highest_risk_zip": max(valid, key=lambda r: r["risk_score"])["zip_code"] if valid else None,
        "lowest_risk_zip":  min(valid, key=lambda r: r["risk_score"])["zip_code"] if valid else None,
        "data_source":   "CDC PLACES ZCTA Data 2024 Release",
        "model_version": MODEL_VER,
    })

@app.route("/predict/surge")
def get_surge():
    surge = sorted([r for r in RECORDS if r.get("surge_probable")],
                   key=lambda r: r.get("risk_score") or 0, reverse=True)
    return jsonify({
        "description": "ZIP codes where both mental distress and depression exceed national average",
        "criteria": {
            "mental_distress_above": round(AVG_D,  2),
            "depression_above":      round(AVG_DP, 2),
        },
        "count": len(surge),
        "data":  surge
    })

@app.route("/refresh")
def refresh():
    global RECORDS, BY_ZIP, AVG_D, AVG_DP, AVG_LO, AVG_ES
    try:
        raw = load_data()
        RECORDS, AVG_D, AVG_DP, AVG_LO, AVG_ES = enrich(raw)
        BY_ZIP = {r["zip_code"]: r for r in RECORDS}
        return jsonify({"status": "ok", "zip_codes_loaded": len(RECORDS)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
