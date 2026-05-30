"""
MHCEWS Flask API Server
Mental Health Crisis Early-Warning System
-----------------------------------------
Run:
    pip install flask
    python mhcews_api.py

Endpoints:
    GET /                          - API info
    GET /states                    - All states with risk scores
    GET /states/<abbr>             - Single state (e.g. /states/WA)
    GET /states/risk/<tier>        - Filter by risk tier (High/Moderate/Low)
    GET /summary                   - National summary statistics
    GET /predict/surge             - States flagged as surge-probable
"""

from flask import Flask, jsonify, request
import csv
from statistics import mean

app = Flask(__name__)

# ── Load data on server start ──────────────────────────────────
def load_data():
    records = []
    with open("nsduh_state_mental_health_2023.csv", newline="") as f:
        for row in csv.DictReader(f):
            rec = {
                "state":       row["State"],
                "abbr":        row["State_Abbr"],
                "any_mi_pct":  float(row["Any_Mental_Illness_Pct"]),
                "smi_pct":     float(row["Serious_Mental_Illness_Pct"]),
                "mde_pct":     float(row["Major_Depressive_Episode_Pct"]),
                "tx_rate_pct": float(row["Mental_Health_Treatment_Rate_Pct"]),
            }
            rec["care_gap"] = round(
                rec["any_mi_pct"] - rec["any_mi_pct"] * rec["tx_rate_pct"] / 100, 2
            )
            records.append(rec)

    avg_mi  = mean(r["any_mi_pct"] for r in records)
    avg_smi = mean(r["smi_pct"]    for r in records)
    avg_gap = mean(r["care_gap"]   for r in records)

    for r in records:
        # Raw score centers around 100; use stdev-based tiers
        score = (r["any_mi_pct"] / avg_mi) * 40 \
              + (r["smi_pct"]    / avg_smi) * 35 \
              + (r["care_gap"]   / avg_gap) * 25
        r["risk_score"] = round(score, 1)
        # Tiers based on distribution: High > 106, Low < 94, else Moderate
        r["risk_tier"]  = (
            "High"     if score >= 106 else
            "Moderate" if score >= 94  else
            "Low"
        )
        # Surge: care_gap above avg AND smi above avg
        r["surge_probable"] = (
            r["care_gap"] > avg_gap and r["smi_pct"] > avg_smi
        )

    return records, avg_mi, avg_smi, avg_gap


RECORDS, AVG_MI, AVG_SMI, AVG_GAP = load_data()
RECORDS_BY_ABBR = {r["abbr"]: r for r in RECORDS}


# ── Endpoints ──────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "api": "Mental Health Crisis Early-Warning System (MHCEWS)",
        "version": "1.0.0",
        "source": "SAMHSA NSDUH 2023-2024 State Prevalence Tables",
        "endpoints": {
            "GET /states":             "All 50 states with risk scores",
            "GET /states/<abbr>":      "Single state — e.g. /states/WA",
            "GET /states/risk/<tier>": "Filter by tier: High / Moderate / Low",
            "GET /summary":            "National summary statistics",
            "GET /predict/surge":      "States flagged as surge-probable",
        }
    })


@app.route("/states")
def get_all_states():
    sort_by = request.args.get("sort", "risk_score")
    reverse = request.args.get("order", "desc") == "desc"
    if sort_by not in ("risk_score", "care_gap", "any_mi_pct", "state"):
        sort_by = "risk_score"
    sorted_records = sorted(RECORDS, key=lambda r: r[sort_by], reverse=reverse)
    return jsonify({
        "count": len(sorted_records),
        "sort_by": sort_by,
        "data": sorted_records
    })


@app.route("/states/<abbr>")
def get_state(abbr):
    record = RECORDS_BY_ABBR.get(abbr.upper())
    if not record:
        return jsonify({
            "error": f"State '{abbr}' not found. Use two-letter abbreviation e.g. WA"
        }), 404
    return jsonify(record)


@app.route("/states/risk/<tier>")
def get_by_tier(tier):
    tier_clean = tier.capitalize()
    if tier_clean not in ("High", "Moderate", "Low"):
        return jsonify({"error": "tier must be High, Moderate, or Low"}), 400
    filtered = sorted(
        [r for r in RECORDS if r["risk_tier"] == tier_clean],
        key=lambda r: r["risk_score"], reverse=True
    )
    return jsonify({
        "tier": tier_clean,
        "count": len(filtered),
        "data": filtered
    })


@app.route("/summary")
def get_summary():
    high     = [r for r in RECORDS if r["risk_tier"] == "High"]
    moderate = [r for r in RECORDS if r["risk_tier"] == "Moderate"]
    low      = [r for r in RECORDS if r["risk_tier"] == "Low"]
    surge    = [r for r in RECORDS if r["surge_probable"]]
    return jsonify({
        "total_states": len(RECORDS),
        "national_avg_any_mi_pct":   round(AVG_MI,  2),
        "national_avg_smi_pct":      round(AVG_SMI, 2),
        "national_avg_care_gap_pct": round(AVG_GAP, 2),
        "risk_tier_breakdown": {
            "High":     len(high),
            "Moderate": len(moderate),
            "Low":      len(low),
        },
        "surge_probable_count": len(surge),
        "highest_risk_state": max(RECORDS, key=lambda r: r["risk_score"])["state"],
        "lowest_risk_state":  min(RECORDS, key=lambda r: r["risk_score"])["state"],
    })


@app.route("/predict/surge")
def get_surge():
    surge_states = sorted(
        [r for r in RECORDS if r["surge_probable"]],
        key=lambda r: r["risk_score"], reverse=True
    )
    return jsonify({
        "description": (
            "States where care_gap and serious mental illness "
            "are both above the national average — flagged as surge-probable"
        ),
        "criteria": {
            "care_gap_above_avg": round(AVG_GAP, 2),
            "smi_above_avg": round(AVG_SMI, 2),
        },
        "count": len(surge_states),
        "data": surge_states
    })


if __name__ == "__main__":
    app.run(debug=True, port=5002)
