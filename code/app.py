"""
Mental Health Crisis Early-Warning System
State-Level Prevalence Analyzer

Data source: SAMHSA NSDUH 2023-2024 State Prevalence Tables
https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health/state-releases

Usage:
    python app.py                  # Full dashboard
    python app.py --state WA       # Single state report
    python app.py --risk           # Show high-risk states only
"""

import csv
import sys
import argparse
from statistics import mean, stdev


# ── 1. Read & transform data ─────────────────────────────────────────────────

def load_data(filepath="nsduh_state_mental_health_2023.csv"):
    """Read NSDUH CSV and return list of state dicts."""
    records = []
    with open(filepath, newline="") as f:
        for row in csv.DictReader(f):
            records.append({
                "state":      row["State"],
                "abbr":       row["State_Abbr"],
                "any_mi":     float(row["Any_Mental_Illness_Pct"]),
                "smi":        float(row["Serious_Mental_Illness_Pct"]),
                "mde":        float(row["Major_Depressive_Episode_Pct"]),
                "tx_rate":    float(row["Mental_Health_Treatment_Rate_Pct"]),
            })
    return records


# ── 2. Compute derived metrics ────────────────────────────────────────────────

def compute_care_gap(record):
    """
    Care gap = % with Any Mental Illness who are NOT receiving treatment.
    Higher = more people going untreated.
    """
    untreated_pct = record["any_mi"] - (record["any_mi"] * record["tx_rate"] / 100)
    return round(untreated_pct, 2)


def compute_risk_score(record, avg_mi, avg_smi, avg_gap):
    """
    Composite risk score (0–100):
      - 40% weight: Any mental illness prevalence vs national avg
      - 35% weight: Serious mental illness prevalence vs national avg
      - 25% weight: Care gap vs national avg
    Scores > 60 = High Risk, 40–60 = Moderate, < 40 = Low
    """
    mi_norm  = min((record["any_mi"] / avg_mi) * 40, 55)
    smi_norm = min((record["smi"] / avg_smi) * 35, 48)
    gap_norm = min((record["care_gap"] / avg_gap) * 25, 35)
    return round(mi_norm + smi_norm + gap_norm, 1)


def risk_tier(score):
    if score >= 65:
        return "🔴 HIGH"
    elif score >= 48:
        return "🟡 MODERATE"
    else:
        return "🟢 LOW"


def enrich(records):
    """Add care_gap and risk_score to each record."""
    for r in records:
        r["care_gap"] = compute_care_gap(r)

    avg_mi  = mean(r["any_mi"]   for r in records)
    avg_smi = mean(r["smi"]      for r in records)
    avg_gap = mean(r["care_gap"] for r in records)

    for r in records:
        r["risk_score"] = compute_risk_score(r, avg_mi, avg_smi, avg_gap)
        r["risk_tier"]  = risk_tier(r["risk_score"])

    return records, avg_mi, avg_smi, avg_gap


# ── 3. Visualize ──────────────────────────────────────────────────────────────

def bar(value, max_val=30, width=30, fill="█"):
    filled = int((value / max_val) * width)
    return fill * filled + "░" * (width - filled)


def print_header():
    print("\n" + "═" * 72)
    print("  🧠  MENTAL HEALTH CRISIS EARLY-WARNING SYSTEM")
    print("       State-Level Prevalence Analyzer | SAMHSA NSDUH 2023–2024")
    print("═" * 72)


def print_national_summary(records, avg_mi, avg_smi, avg_gap):
    high_risk = [r for r in records if r["risk_tier"] == "🔴 HIGH"]
    print(f"\n{'─'*72}")
    print(f"  NATIONAL SUMMARY")
    print(f"{'─'*72}")
    print(f"  States analyzed          : {len(records)}")
    print(f"  Avg Any Mental Illness   : {avg_mi:.1f}%")
    print(f"  Avg Serious MI           : {avg_smi:.1f}%")
    print(f"  Avg Care Gap             : {avg_gap:.1f}%")
    print(f"  High-risk states         : {len(high_risk)}")
    print(f"{'─'*72}\n")


def print_full_table(records):
    sorted_records = sorted(records, key=lambda r: r["risk_score"], reverse=True)
    print(f"  {'STATE':<22} {'ANY MI%':>7} {'SMI%':>6} {'TX RATE%':>9} {'CARE GAP%':>10} {'RISK':>5}  {'TIER'}")
    print(f"  {'─'*22} {'─'*7} {'─'*6} {'─'*9} {'─'*10} {'─'*5}  {'─'*10}")
    for r in sorted_records:
        print(f"  {r['state']:<22} {r['any_mi']:>7.1f} {r['smi']:>6.1f} "
              f"{r['tx_rate']:>9.1f} {r['care_gap']:>10.1f} "
              f"{r['risk_score']:>5.1f}  {r['risk_tier']}")


def print_care_gap_chart(records):
    print(f"\n{'─'*72}")
    print(f"  CARE GAP CHART  (% with mental illness not receiving treatment)")
    print(f"  Top 15 States by Care Gap")
    print(f"{'─'*72}")
    top15 = sorted(records, key=lambda r: r["care_gap"], reverse=True)[:15]
    for r in top15:
        print(f"  {r['abbr']}  {bar(r['care_gap'], max_val=22)}  {r['care_gap']:.1f}%")


def print_state_report(record):
    print(f"\n{'─'*72}")
    print(f"  STATE REPORT: {record['state']} ({record['abbr']})")
    print(f"{'─'*72}")
    print(f"  Any Mental Illness          : {record['any_mi']:.1f}%   {bar(record['any_mi'], 30)}")
    print(f"  Serious Mental Illness      : {record['smi']:.1f}%    {bar(record['smi'], 15)}")
    print(f"  Major Depressive Episode    : {record['mde']:.1f}%    {bar(record['mde'], 10)}")
    print(f"  Mental Health Treatment Rate: {record['tx_rate']:.1f}%  {bar(record['tx_rate'], 70)}")
    print(f"  Care Gap (untreated)        : {record['care_gap']:.1f}%  {bar(record['care_gap'], 22)}")
    print(f"\n  ► Risk Score : {record['risk_score']}")
    print(f"  ► Risk Tier  : {record['risk_tier']}")
    if record["risk_tier"] == "🔴 HIGH":
        print(f"\n  ⚠  RECOMMENDATION: Pre-position mobile crisis teams.")
        print(f"     Alert community mental health partners of elevated need.")
    elif record["risk_tier"] == "🟡 MODERATE":
        print(f"\n  ℹ  RECOMMENDATION: Monitor 211 call volume trends weekly.")
        print(f"     Increase outreach to underserved ZIP codes.")
    else:
        print(f"\n  ✓  RECOMMENDATION: Maintain current resource levels.")
        print(f"     Continue routine community health worker check-ins.")


def print_high_risk(records):
    high = [r for r in records if r["risk_tier"] == "🔴 HIGH"]
    high = sorted(high, key=lambda r: r["risk_score"], reverse=True)
    print(f"\n{'─'*72}")
    print(f"  HIGH-RISK STATES  ({len(high)} states requiring priority attention)")
    print(f"{'─'*72}")
    for r in high:
        print(f"\n  {r['state']} ({r['abbr']})  —  Risk Score: {r['risk_score']}")
        print(f"    Any MI: {r['any_mi']:.1f}%  |  SMI: {r['smi']:.1f}%  "
              f"|  Care Gap: {r['care_gap']:.1f}%")
        print(f"    {bar(r['care_gap'], max_val=22)}  untreated")


# ── 4. Predict ────────────────────────────────────────────────────────────────

def predict_surge_risk(records):
    """
    Simple rule-based surge predictor:
    Flags states where care gap > 15% AND SMI > 9% as 'surge-probable'
    within the next 2-4 weeks based on unmet need pressure.
    """
    print(f"\n{'─'*72}")
    print(f"  SURGE RISK PREDICTION  (next 2–4 weeks)")
    print(f"  Criteria: Care Gap > 15%  AND  Serious MI > 9%")
    print(f"{'─'*72}")
    surge_states = [r for r in records if r["care_gap"] > 15 and r["smi"] > 9]
    surge_states = sorted(surge_states, key=lambda r: r["risk_score"], reverse=True)
    if surge_states:
        print(f"  ⚠  {len(surge_states)} state(s) flagged as SURGE-PROBABLE:\n")
        for r in surge_states:
            print(f"  → {r['state']:<22}  Gap:{r['care_gap']:.1f}%  SMI:{r['smi']:.1f}%  "
                  f"Score:{r['risk_score']}")
    else:
        print("  No states currently meet surge-probable threshold.")


# ── 5. Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Mental Health Crisis Early-Warning System"
    )
    parser.add_argument("--state", type=str, help="Two-letter state abbreviation (e.g. WA)")
    parser.add_argument("--risk",  action="store_true", help="Show high-risk states only")
    args = parser.parse_args()

    records = load_data()
    records, avg_mi, avg_smi, avg_gap = enrich(records)

    print_header()

    if args.state:
        match = next((r for r in records if r["abbr"] == args.state.upper()), None)
        if match:
            print_national_summary(records, avg_mi, avg_smi, avg_gap)
            print_state_report(match)
        else:
            print(f"\n  State '{args.state}' not found. Use two-letter abbreviation (e.g. WA).")
    elif args.risk:
        print_national_summary(records, avg_mi, avg_smi, avg_gap)
        print_high_risk(records)
        predict_surge_risk(records)
    else:
        print_national_summary(records, avg_mi, avg_smi, avg_gap)
        print_full_table(records)
        print_care_gap_chart(records)
        predict_surge_risk(records)

    print(f"\n{'═'*72}")
    print(f"  Data: SAMHSA NSDUH 2023–2024 State Prevalence Tables")
    print(f"  Source: samhsa.gov/data | Generated for MSIM Crisis Navigator Project")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
