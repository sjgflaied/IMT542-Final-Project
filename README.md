# Mental Health Crisis Early-Warning System (MHCEWS)

**IMT 542 — Portable Information Structures · Group 8 · Cumulative Final Project**

A portable information structure for publishing ZIP-code-level weekly mental-health risk records in the United States, built on real federal open-data APIs (CDC PLACES and SAMHSA FindTreatment.gov) and designed end-to-end around the FAIR principles.

> **Scope note.** MHCEWS is a proposed information structure designed for this course. It is not a deployed production service. The example in this repository demonstrates how MHCEWS records can be assembled today from real, publicly accessible federal APIs so that the structure can be implemented immediately on existing open-data infrastructure.

---

## Table of Contents

1. [Information Story](#information-story)
2. [Who This Is For](#who-this-is-for)
3. [FAIR Principles in MHCEWS](#fair-principles-in-mhcews)
4. [Architecture Overview](#architecture-overview)
5. [Record Schema — Four Metadata Layers + Provenance](#record-schema--four-metadata-layers--provenance)
6. [Real Federal APIs Used](#real-federal-apis-used)
7. [Quickstart](#quickstart)
8. [API Endpoints](#api-endpoints)
9. [Example Record](#example-record)
10. [Quality, Performance, and Security](#quality-performance-and-security)
11. [Ethics, Limitations, and Responsible Use](#ethics-limitations-and-responsible-use)
12. [Repository Layout](#repository-layout)
13. [License](#license)

---

## Information Story

In communities where crisis lines are chronically understaffed and mobile crisis teams are perpetually reactive, mental-health surges are detected only after a person calls 911, 988, or 211 — by which point the demand has already become an emergency. The information needed to anticipate these surges *already exists* in the federal open-data ecosystem (CDC PLACES, SAMHSA, BRFSS), but it lives in formats, geographies, and release cycles that make it nearly impossible for a public-health coordinator to act on it in a weekly operational rhythm.

**MHCEWS restructures this information so that a King County public-health analyst — or any coordinator in any U.S. jurisdiction — can answer one question every Monday morning:**

> *"Which ZIP codes in my region are likely to experience elevated mental-health crisis demand this week, and what should I do about it?"*

The information story is a shift from **reactive emergency response to preventive resource deployment**. By restructuring annual federal datasets into weekly, ZIP-code-level records with a built-in recommended action, MHCEWS enables a 2–4 week predictive window before demand overwhelms capacity.

## Who This Is For

| User | Goal |
|------|------|
| Public-health agency analysts | Decide where to surge mobile crisis team coverage week over week |
| 988 / crisis-line operators | Anticipate call-volume spikes by geography |
| Community mental-health organizations | Pre-position outreach resources |
| Academic researchers | Study spatial and temporal patterns in community mental-health risk with full provenance |
| Journalists | Report on under-served high-need areas with citable, openly-licensed data |

---

## FAIR Principles in MHCEWS

MHCEWS is designed so that **every** FAIR principle is a concrete property of the schema, not just a stated aspiration.

### 🔍 Findable

Every record is uniquely identified by a composite key of `zip_code` + ISO 8601 `week_start_date` and described through a four-layer metadata structure — **Identity, Signal, Prediction, Action** — providing both human-readable labels and machine-readable typed values so downstream systems can interpret the data without additional context.

### 🌐 Accessible

Records are accessible via a REST API over standard HTTP protocols that are open, free, and universally implementable. Aggregate risk outputs are openly available without authentication, while sensitive data streams (e.g., real-time dispatch logs) are gated behind OAuth 2.0.

### 🔗 Interoperable

All data fields follow `snake_case` conventions aligned with JSON-LD practices, and geographic identifiers use standardized vocabularies — Census **FIPS** and **ZCTA** ZIP codes maintained by the U.S. Census Bureau — ensuring interoperability with any system that adopts these widely used standards.

### ♻️ Reusable

Each record includes a detailed **provenance block** capturing `data_source`, `model_version`, and `data_freshness` timestamps for every contributing input, enabling full traceability of how risk scores are generated. Public outputs are released under **Creative Commons Attribution 4.0 (CC BY 4.0)**, ensuring clarity in reuse conditions and supporting transparency and reproducibility.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  UPSTREAM FEDERAL OPEN-DATA SOURCES                              │
│  ──────────────────────────────────────────                      │
│  • CDC PLACES ZCTA dataset (Socrata SODA API)                    │
│  • SAMHSA FindTreatment.gov locator                              │
│  • 988 Suicide & Crisis Lifeline aggregates (where available)    │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTPS / JSON
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  MHCEWS TRANSFORMATION PIPELINE                                  │
│  ──────────────────────────────────                              │
│  download_cdc_places.py  →  pivot measure-per-row to ZIP-per-row │
│  enrichment              →  join SAMHSA facility counts          │
│  risk model              →  composite 0–100 risk_score + tier    │
│  provenance              →  stamp every record with sources/ver  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  MHCEWS REST API  (Flask · mhcews_api.py · port 5002)            │
│  ────────────────────────────────────────────────                │
│  /zipcodes  ·  /zipcodes/<zip>  ·  /zipcodes/risk/<tier>         │
│  /summary   ·  /predict/surge   ·  /refresh                      │
└─────────────────────────┬────────────────────────────────────────┘
                          │ JSON · CSV · GeoJSON
                          ▼
        ┌──────────────────┬──────────────────┬─────────────────┐
        │ Public-health    │ 988 / crisis     │ Researchers /   │
        │ analyst dashboard│ dispatch CRM     │ journalists     │
        └──────────────────┴──────────────────┴─────────────────┘
```

---

## Record Schema — Four Metadata Layers + Provenance

Every MHCEWS record is a JSON object organized into four metadata layers plus a provenance block. The composite primary key is `zip_code` + `week_start_date`.

### Identity Layer — *who and where*

| Field | Type | Description |
|---|---|---|
| `zip_code` | string (ZCTA, 5-digit) | U.S. Census ZCTA ZIP code (matches CDC PLACES `locationname`) |
| `state_fips` | string (2-digit) | Census state FIPS code |
| `county_fips` | string (5-digit) | Census county FIPS code |
| `week_start_date` | string (ISO 8601 date) | Monday of the ISO week |

### Signal Layer — *the raw inputs*

| Field | Type | Description | Upstream source |
|---|---|---|---|
| `frequent_mental_distress_pct` | float (0–100) | % adults reporting frequent mental distress | CDC PLACES `MHLTH` |
| `social_isolation_pct` | float (0–100) | % adults reporting social isolation | CDC PLACES `ISOLATION` |
| `lack_emotional_support_pct` | float (0–100) | % adults lacking social/emotional support | CDC PLACES `EMOTIONSPT` |
| `nearby_treatment_facility_count` | integer | Count of SAMHSA-listed facilities within ZIP | SAMHSA FindTreatment.gov |

### Prediction Layer — *the model output*

| Field | Type | Description |
|---|---|---|
| `risk_score` | float (0–100) | Composite weekly crisis risk score |
| `risk_tier` | enum | `low` \| `moderate` \| `elevated` \| `high` |
| `confidence_interval` | object `{lower, upper}` | 95% CI on the risk score |
| `trend_4wk` | enum | `rising` \| `stable` \| `falling` |

### Action Layer — *what to do about it*

| Field | Type | Description |
|---|---|---|
| `recommended_action` | string | Human-readable suggested response |
| `priority` | enum | `routine` \| `watch` \| `urgent` |
| `suggested_resources` | array of strings | URIs of relevant local resources (988, SAMHSA, county) |

### Provenance Block

| Field | Type | Description |
|---|---|---|
| `data_source` | array of strings | Identifiers of contributing inputs (e.g. `cdc_places_zcta_qnzd-25i4`) |
| `model_version` | string (semver) | Version of the risk model used |
| `data_freshness` | object `{source: timestamp}` | Last-updated timestamp per input |
| `license` | string | `CC-BY-4.0` for MHCEWS-derived outputs |

---

## Real Federal APIs Used

| Service | Base URL | Auth | License |
|---|---|---|---|
| CDC PLACES ZCTA dataset (Socrata SODA) | `https://data.cdc.gov/resource/qnzd-25i4.json` | None (public) | U.S. Government work |
| CDC PLACES portal | `https://www.cdc.gov/places/` | n/a | n/a |
| SAMHSA FindTreatment.gov | `https://findtreatment.gov/` | API key on request | Public domain |
| 988 Suicide & Crisis Lifeline | `https://988lifeline.org/` | n/a | n/a |

---

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/mhcews.git
cd mhcews
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download the CDC PLACES data

```bash
python download_cdc_places.py
# → writes cdc_places_zcta_mh.csv to project root
```

This script pulls all four mental-health measures (`MHLTH`, `DEPRESSION`, `EMOTIONSPT`, `LONELINESS`) from the CDC PLACES SODA API for all ~32,520 ZCTAs.

### 4. Start the API

```bash
python mhcews_api.py
# → listening on http://localhost:5002
```

### 5. Query a ZIP code

```bash
curl http://localhost:5002/zipcodes/98101
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | API metadata and endpoint listing |
| `GET /zipcodes` | All ZIP codes with risk scores (supports `?sort=` and `?limit=`) |
| `GET /zipcodes/<zip>` | Single ZIP code lookup |
| `GET /zipcodes/risk/<tier>` | Filter by `High` / `Moderate` / `Low` |
| `GET /summary` | National summary statistics |
| `GET /predict/surge` | Surge-probable ZIP codes (above national distress + depression averages) |
| `GET /refresh` | Reload data from the local CSV |

---

## Example Record

**Request to CDC PLACES** (Signal-layer input — real, executable, no auth):

```http
GET /resource/qnzd-25i4.json?locationname=98101&measureid=MHLTH HTTP/1.1
Host: data.cdc.gov
Accept: application/json
```

**Assembled MHCEWS record returned downstream:**

```json
{
  "identity": {
    "zip_code": "98101",
    "state_fips": "53",
    "county_fips": "53033",
    "week_start_date": "2026-05-11"
  },
  "signal": {
    "frequent_mental_distress_pct": 16.8,
    "social_isolation_pct": 22.1,
    "lack_emotional_support_pct": 19.4,
    "nearby_treatment_facility_count": 12
  },
  "prediction": {
    "risk_score": 73.4,
    "risk_tier": "elevated",
    "confidence_interval": { "lower": 69.1, "upper": 77.8 },
    "trend_4wk": "rising"
  },
  "action": {
    "recommended_action": "Increase mobile crisis team coverage and notify local 988 dispatch.",
    "priority": "urgent",
    "suggested_resources": [
      "https://988lifeline.org",
      "https://findtreatment.gov/locator?zip=98101",
      "https://kingcounty.gov/depts/community-human-services/mental-health-substance-abuse.aspx"
    ]
  },
  "provenance": {
    "data_source": [
      "cdc_places_zcta_qnzd-25i4",
      "samhsa_findtreatment_locator",
      "wa_doh_988_aggregate"
    ],
    "model_version": "0.1.0-prototype",
    "data_freshness": {
      "cdc_places_zcta_qnzd-25i4": "2025-12-11T00:00:00Z",
      "samhsa_findtreatment_locator": "2026-05-15T00:00:00Z",
      "wa_doh_988_aggregate": "2026-05-17T23:00:00Z"
    },
    "license": "CC-BY-4.0"
  }
}
```

**Interpretation:** the analyst sees `risk_tier: "elevated"` with a rising 4-week trend and an urgent recommended priority. She uses the `recommended_action` text directly in her staffing memo, cites the upstream `data_source` IDs so a reviewer can re-pull the exact CDC PLACES row, and routes the suggested 988 and SAMHSA links to her communications team.

---

## Quality, Performance, and Security

### Quality targets

| Metric | Goal |
|---|---|
| API uptime | 99% during active development |
| Functional test pass rate | 100% before any deployment |
| Data completeness | All 4 mental-health measures present for every ZIP |
| Risk score accuracy | Matches formula to 2 decimal places |
| CDC data freshness | Updated within 90 days of each annual CDC release |

### Performance targets

| Endpoint | Target |
|---|---|
| `GET /zipcodes/<zip>` | < 150 ms |
| `GET /zipcodes` (full dataset) | < 500 ms |
| `GET /predict/surge` | < 300 ms |
| 50 concurrent users | < 3 s p95, zero 500 errors |
| Cold start with full ~32K-ZCTA dataset | < 5 s |

### Data quality checks (run on every ingest)

- All four mental-health measures present per ZIP (warn if any missing)
- All percentage values fall in `[0, 100]`
- Confidence interval bounds satisfy `low_ci < data_value < high_ci`
- No duplicate ZIP codes after pivot
- `model_version` field stamped on every output record (hard error if missing)

### Security model

- **Aggregate risk outputs** — open, unauthenticated, CC BY 4.0
- **Sensitive streams** (real-time dispatch logs, individual-level data) — OAuth 2.0, never reach public endpoints
- **No individual-level data is collected, stored, or processed.** All signals are aggregated to the ZCTA level.
- **Prohibited uses** (enforced via data use agreement): criminal justice, immigration enforcement, insurance underwriting, employment screening, or any individual-level clinical decision-making.

See [`docs/test_plan.md`](docs/test_plan.md) for the full functional, performance, and monitoring test matrix.

---

## Ethics, Limitations, and Responsible Use

MHCEWS is **decision-support, not decision-replacement**. It does not substitute for clinical judgment, individual mental-health assessment, or direct crisis intervention. Every prediction is published with a confidence interval that consumers are expected to factor into resource allocation.

Known limitations:

- **Baseline lag.** CDC PLACES and BRFSS update annually; predictions may lag real-world conditions by 1–2 years on the slowest inputs.
- **Geographic coarseness.** ZCTAs can mask hyperlocal disparities within a single risk score.
- **Underrepresentation.** Communities with lower digital and survey participation — elderly residents, recent immigrants, lower-income households — are structurally underrepresented and may receive systematically lower scores than actual need warrants. Adopting jurisdictions are expected to supplement MHCEWS with non-digital outreach in these communities regardless of score.

See [`docs/ethics_statement.md`](docs/ethics_statement.md) for the full Availability, Limitations, Ethics, and Societal Impact statement, including the virtue-ethics, consequentialist, and non-consequentialist framing.

---

## Repository Layout

```
mhcews/
├── README.md                          ← this file
├── requirements.txt
├── download_cdc_places.py             ← pulls CDC PLACES via Socrata SODA
├── mhcews_api.py                      ← Flask API (port 5002)
├── test_api.py                        ← functional smoke tests
├── cdc_places_zcta_mh.csv             ← downloaded source data (gitignored)
├── docs/
│   ├── information_architecture.md    ← FAIR assessment + schema rationale
│   ├── test_plan.md                   ← functional / performance / quality tests
│   ├── ethics_statement.md            ← availability, limitations, ethics
│   └── wireframes/                    ← coordinator dashboard mockups
└── presentation/
    └── MHCEWS_final.pptx              ← in-class presentation deck
```

---

## License

- **MHCEWS-derived outputs** — [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Upstream sources retain their own licenses:**
  - CDC PLACES — U.S. Government work (public domain)
  - SAMHSA FindTreatment.gov — public domain
- **Code in this repository** — MIT License (see `LICENSE`)

---

## Citation

If you use MHCEWS-derived records in research, please cite the upstream `data_source` IDs from each record's provenance block (e.g. `cdc_places_zcta_qnzd-25i4`) and the `model_version` so the exact upstream rows can be re-pulled.

---

*MHCEWS · IMT 542 Portable Information Structures · University of Washington Information School*
