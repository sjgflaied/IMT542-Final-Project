# This script generates sample data matching the exact structure of
# SAMHSA NSDUH 2023-2024 State Prevalence Tables (CSV)
# Real data source: https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health/state-releases
# Direct CSV download: 2023-2024 State Prevalence Tables: CSV (ZIP)

import csv

states = [
    ("Alabama","AL"),("Alaska","AK"),("Arizona","AZ"),("Arkansas","AR"),
    ("California","CA"),("Colorado","CO"),("Connecticut","CT"),("Delaware","DE"),
    ("Florida","FL"),("Georgia","GA"),("Hawaii","HI"),("Idaho","ID"),
    ("Illinois","IL"),("Indiana","IN"),("Iowa","IA"),("Kansas","KS"),
    ("Kentucky","KY"),("Louisiana","LA"),("Maine","ME"),("Maryland","MD"),
    ("Massachusetts","MA"),("Michigan","MI"),("Minnesota","MN"),("Mississippi","MS"),
    ("Missouri","MO"),("Montana","MT"),("Nebraska","NE"),("Nevada","NV"),
    ("New Hampshire","NH"),("New Jersey","NJ"),("New Mexico","NM"),("New York","NY"),
    ("North Carolina","NC"),("North Dakota","ND"),("Ohio","OH"),("Oklahoma","OK"),
    ("Oregon","OR"),("Pennsylvania","PA"),("Rhode Island","RI"),("South Carolina","SC"),
    ("South Dakota","SD"),("Tennessee","TN"),("Texas","TX"),("Utah","UT"),
    ("Vermont","VT"),("Virginia","VA"),("Washington","WA"),("West Virginia","WV"),
    ("Wisconsin","WI"),("Wyoming","WY")
]

# Representative values approximating real NSDUH state-level estimates
data = {
    "AL": (18.2, 7.1, 4.2, 55.3), "AK": (22.1, 9.4, 5.8, 48.7),
    "AZ": (19.8, 8.2, 5.1, 52.4), "AR": (20.3, 7.8, 4.9, 51.8),
    "CA": (18.9, 8.9, 5.6, 57.2), "CO": (21.4, 9.8, 6.3, 60.1),
    "CT": (20.7, 9.1, 5.9, 61.4), "DE": (21.2, 8.7, 5.5, 58.9),
    "FL": (17.8, 7.3, 4.5, 50.2), "GA": (17.4, 6.9, 4.1, 49.8),
    "HI": (16.9, 7.8, 4.8, 54.3), "ID": (19.1, 7.5, 4.6, 50.7),
    "IL": (19.6, 8.4, 5.3, 56.8), "IN": (20.8, 8.1, 5.0, 52.1),
    "IA": (19.3, 7.9, 4.9, 53.6), "KS": (19.7, 7.6, 4.7, 51.4),
    "KY": (22.4, 8.9, 5.6, 49.3), "LA": (18.6, 7.2, 4.3, 48.1),
    "ME": (23.1, 10.2, 6.7, 62.4), "MD": (19.4, 8.6, 5.4, 59.7),
    "MA": (22.8, 10.4, 6.9, 64.2), "MI": (21.3, 8.8, 5.6, 55.9),
    "MN": (20.6, 8.5, 5.3, 57.8), "MS": (17.1, 6.5, 3.9, 45.2),
    "MO": (21.9, 8.3, 5.2, 52.7), "MT": (22.7, 9.6, 6.1, 57.3),
    "NE": (18.8, 7.7, 4.8, 53.1), "NV": (20.2, 8.0, 5.0, 51.6),
    "NH": (23.5, 10.7, 7.1, 63.8), "NJ": (18.3, 8.2, 5.2, 58.4),
    "NM": (23.8, 10.1, 6.6, 55.7), "NY": (19.1, 8.7, 5.5, 58.9),
    "NC": (19.9, 7.9, 4.9, 52.6), "ND": (18.4, 7.4, 4.5, 51.2),
    "OH": (22.1, 9.0, 5.8, 54.3), "OK": (21.6, 8.3, 5.2, 50.9),
    "OR": (23.9, 11.2, 7.4, 63.5), "PA": (21.7, 8.9, 5.7, 56.2),
    "RI": (22.4, 10.3, 6.8, 62.7), "SC": (18.7, 7.1, 4.3, 50.4),
    "SD": (19.2, 7.8, 4.8, 52.3), "TN": (21.1, 8.0, 5.0, 50.8),
    "TX": (16.8, 6.8, 4.1, 47.9), "UT": (18.5, 7.6, 4.7, 53.8),
    "VT": (24.2, 11.4, 7.6, 65.1), "VA": (19.5, 8.3, 5.2, 57.4),
    "WA": (22.3, 10.0, 6.5, 61.8), "WV": (24.8, 9.7, 6.3, 47.6),
    "WI": (20.4, 8.6, 5.4, 56.7), "WY": (21.8, 8.9, 5.6, 52.9),
}

rows = []
for name, abbr in states:
    amh, smi, mde, tx_rate = data[abbr]
    rows.append({
        "State": name,
        "State_Abbr": abbr,
        "Any_Mental_Illness_Pct": amh,
        "Serious_Mental_Illness_Pct": smi,
        "Major_Depressive_Episode_Pct": mde,
        "Mental_Health_Treatment_Rate_Pct": tx_rate,
    })

with open("nsduh_state_mental_health_2023.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated nsduh_state_mental_health_2023.csv with {len(rows)} states")
