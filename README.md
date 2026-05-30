# Mental Health Crisis Early-Warning System (MHCEWS)

> **IMT 542 — Portable Information Structures | Final Project**
> Group 5 · University of Washington Information School

The **Mental Health Crisis Early-Warning System (MHCEWS)** restructures publicly available SAMHSA mental health data into a portable, queryable information structure that predicts which U.S. states are at risk of a mental health crisis surge. The original SAMHSA data exists — but it is not portable. MHCEWS transforms it into a typed JSON schema with computed fields, a REST API, and a command-line analysis tool, so the same data can drive a real-time dashboard, an automated alert, or a staffing decision.

**Insight area:** *Predict*.

---

## Table of Contents

1. [Ideate a Use Case — Info Story, Requirements, Wireframes](#1-ideate-a-use-case--info-story-requirements-wireframes)
2. [Define and Assess Existing Information Using FAIR](#2-define-and-assess-existing-information-using-fair)
3. [Analyze Deficiencies and Design Improvements](#3-analyze-deficiencies-and-design-improvements)
4. [Improve the Existing Information Structure](#4-improve-the-existing-information-structure)
5. [Control Quality, Performance, and Security](#5-control-quality-performance-and-security)

---

## 1. Ideate a Use Case — Info Story, Requirements, Wireframes

### 1.1 Information Story

#### Primary User

| | |
|---|---|
| **Role** | 211 crisis line coordinator / state public health analyst |
| **Organization** | A regional 211 contact center or state behavioral health agency |
| **Goal** | Allocate weekly staffing and outreach resources across regions |
| **Decision cadence** | Weekly capacity planning + ad-hoc surge response |

#### Problem Statement

When the coordinator opens her week, she has no leading indicator of whether call volume will exceed capacity. The most authoritative source — the SAMHSA NSDUH State Prevalence Tables — is published once a year as a CSV that requires a separate PDF codebook to interpret. By the time she has it cleaned and joined to her own staffing roster, it is already two years stale and offers no computed risk signal. She is forced to make a high-stakes staffing decision either from intuition or from a hand-built spreadsheet.

#### What MHCEWS Delivers

MHCEWS restructures the same SAMHSA data into a weekly, state-level risk signal accessible via API. A single call to `GET /predict/surge` returns a ranked list of states where care gap and serious mental illness prevalence both exceed the national average — a leading indicator of crisis line overflow. The coordinator gets a typed, machine-readable record per state with `risk_score`, `risk_tier`, and an actionable `surge_probable` flag, plus provenance fields so the underlying NSDUH release and model version are traceable.

#### Motivation

Mental health crisis response in the United States is delivered by a fragmented network of state agencies, 211 / 988 lines, and community organizations, each making weekly resource decisions on local data. Making the national prevalence signal **portable** — typed, computed, queryable — lets those frontline coordinators act on the same evidence base without each rebuilding a CSV pipeline. The underlying insight already exists in public data; only the information structure prevents it from being used.

### 1.2 Requirements

#### Functional Requirements

1. Return aggregate mental-health prevalence and a computed risk score for each of the 50 U.S. states.
2. Support lookup by individual state abbreviation.
3. Support filtering by computed risk tier (`High`, `Moderate`, `Low`).
4. Return a national-summary endpoint with averages and tier counts.
5. Return a surge-prediction endpoint listing only states that meet the surge criterion.
6. Every response must include provenance fields (`data_source`, `model_version`).
7. The data file backing the API must be regenerable from a single Python script.

#### Portability Requirements (FAIR)

| Principle | Requirement |
|---|---|
| **Findable** | Each record uniquely identified by `abbr + survey_year`; schema is self-describing; no PDF codebook required to interpret any field. |
| **Accessible** | Aggregate scores accessible over HTTPS with no authentication; queryable by state, tier, or surge flag; on-demand recomputation. |
| **Interoperable** | snake_case JSON fields aligned with JSON-LD practice; standard USPS state abbreviations; ISO 8601 dates where applicable; typed numeric fields. |
| **Reusable** | `data_source` and `model_version` on every record; license clearly stated; transformation logic open-source in this repository. |

#### In Scope

- State-level aggregate risk prediction (50 U.S. states)
- Weekly cadence (model recomputes on demand from the latest CSV release)
- Public, no-auth read access to aggregate risk scores
- Surge prediction based on `care_gap × smi_pct`
- Provenance fields on every record
- REST API + command-line analysis tool

#### Out of Scope

- Individual-level or ZIP / county-level data
- Real-time 988 / 211 call-volume integration
- Clinical diagnostic recommendations
- Cross-country or international data
- Write access, user accounts, or user-submitted data
- OAuth 2.0 / authenticated feeds (listed as future work)

### 1.3 Wireframes

Because MHCEWS is an API-first product, the "wireframe" is the JSON response contract and the CLI dashboard layout — these are the actual user-facing surfaces.

#### User Flow

```text
   ┌─────────────────────┐     ┌────────────────────┐     ┌──────────────────┐
   │ Monday 8:00 AM      │     │  curl /predict/    │     │  Ranked JSON     │
   │ Coordinator opens   │ ──▶ │  surge             │ ──▶ │  list of states  │
   │ planning workspace  │     │                    │     │  with risk_tier  │
   └─────────────────────┘     └────────────────────┘     └──────────────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │ Update staffing      │
                                                       │ roster + send alert  │
                                                       └──────────────────────┘
```

#### API Response Wireframe — `GET /states/WA`

```json
{
  "identity":   { "state": "Washington", "abbr": "WA" },
  "signal":     { "any_mi_pct": 24.1, "smi_pct": 6.8,
                  "mde_pct": 9.2, "tx_rate_pct": 51.4 },
  "prediction": { "care_gap": 11.7, "risk_score": 108.3, "risk_tier": "High" },
  "action":     { "surge_probable": true },
  "provenance": { "data_source": "samhsa_nsduh_2023",
                  "model_version": "0.1.0",
                  "survey_year": 2023 }
}
```

#### CLI Dashboard Wireframe — `python app.py --risk`

```text
MHCEWS — High-Risk States (model_version 0.1.0, samhsa_nsduh_2023)
─────────────────────────────────────────────────────────────────
RANK  STATE  RISK_SCORE  RISK_TIER  CARE_GAP  SURGE
  1   OR     118.4       High       13.2      ✓
  2   WA     108.3       High       11.7      ✓
  3   MT     106.9       High       12.0      ✓
  4   NV     104.1       Moderate   10.8      ·
─────────────────────────────────────────────────────────────────
Surge-probable states: 3   |   National avg score: 100.0
```

---

## 2. Define and Assess Existing Information Using FAIR

### 2.1 Data Source

**SAMHSA NSDUH 2023–2024 State Prevalence Tables**

| | |
|---|---|
| **Publisher** | Substance Abuse and Mental Health Services Administration |
| **URL** | <https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health/state-releases> |
| **Format** | CSV |
| **Coverage** | All 50 U.S. states, civilian non-institutionalized population aged 12+ |
| **Update frequency** | Annual |
| **License** | U.S. Government Open Data (public domain) |

> **Note on the included file.** `nsduh_state_mental_health_2023.csv` in this repository is a **synthetic dataset** generated by `generate_sample_data.py` that matches the schema and value ranges of the real NSDUH State Prevalence Tables. To run MHCEWS on the actual SAMHSA release, download the official CSV from the URL above and replace the included file — the transformation logic, API endpoints, and risk model are identical in both cases.

### 2.2 Existing Structure

The NSDUH State Prevalence Tables are published as a single flat CSV. Each row is a state; each column is a prevalence measure. Column names use SAMHSA-internal abbreviations (e.g. `AMIPY`, `SMIPY`, `MDEPY`, `TXRECMI`) that cannot be interpreted without the accompanying PDF codebook. Values are untyped — numeric values, suppression markers, and missing flags all appear as strings in the same column.

### 2.3 Original Use Case of the Data

The NSDUH tables are designed for **annual epidemiological reporting**, not for operational decision-making. The intended audience is researchers writing peer-reviewed surveillance articles. The format was not designed for an API consumer, a dashboard, or a weekly staffing decision.

### 2.4 Access Methodology

| Aspect | Original SAMHSA |
|---|---|
| Distribution | Annual bulk CSV download from a static URL |
| Authentication | None |
| Query interface | None — file is downloaded whole |
| Programmatic filter | None — requires local processing |
| Rate limit | N/A (static file) |

### 2.5 Quality of the Existing Data

- **Completeness:** 50 / 50 states present in each annual release.
- **Suppression:** small-sample cells are suppressed; the suppression marker is a string, not a typed null, requiring downstream cleanup.
- **Documentation:** column meaning requires the separate codebook PDF; field-level metadata is not embedded in the file.
- **Staleness:** annual release cadence means up to 24 months of lag between the survey period and the published table.

### 2.6 Performance of the Existing Access Path

A static CSV has no runtime performance — but the operational cost is in the pipeline a consumer has to build every year: download, decode, clean suppression markers, join the codebook, and compute any derived field. There is no programmatic way to ask "which states are above the national average on serious mental illness?"; the consumer must compute it locally each time.

### 2.7 FAIR Assessment of the Original Data

| Principle | Score | Reasoning |
|---|---|---|
| **Findable** | 2 / 5 | File URL is hard to locate from the SAMHSA portal; no unique record ID; PDF codebook required to interpret columns. |
| **Accessible** | 2 / 5 | Bulk download only; annual cadence; no API; no programmatic filtering. |
| **Interoperable** | 1 / 5 | No schema; non-standard column abbreviations; untyped values; no controlled vocabulary. |
| **Reusable** | 2 / 5 | No provenance on the record itself; no version number; license stated only on the parent portal. |

---

## 3. Analyze Deficiencies and Design Improvements

### 3.1 Deficiencies Identified

Mapping each deficiency from §2 to a concrete impact on the coordinator's workflow:

| # | Deficiency | Impact on the user |
|---|---|---|
| D-1 | Non-self-describing column names (`AMIPY`, `SMIPY`, …) | Coordinator must keep the PDF codebook open at all times to read the CSV. |
| D-2 | Untyped values, suppression markers as strings | Every consumer must write their own parser; silent breakage if marker format changes. |
| D-3 | Flat structure with no separation of raw vs. derived | No way to tell which fields are upstream measurements vs. derived analytics. |
| D-4 | No computed risk signal | Coordinator's actual decision input (a single risk score) does not exist — must be hand-built each time. |
| D-5 | No tier or surge flag | Continuous prevalence values are not directly usable for a triage decision. |
| D-6 | No record-level provenance | A risk score in a memo cannot be traced back to which NSDUH release produced it. |
| D-7 | No programmatic access | Every consumer rebuilds the same CSV-cleaning pipeline. |

### 3.2 Design Improvements

| Deficiency | Improvement |
|---|---|
| D-1 | Rename to self-describing snake_case fields (`any_mi_pct`, `smi_pct`, `mde_pct`, `tx_rate_pct`). |
| D-2 | Cast all numerics to typed floats on load; suppression markers raise a clear, named error. |
| D-3 | Group fields into a four-layer schema: **Identity / Signal / Prediction / Action**, plus a provenance block. |
| D-4 | Compute `care_gap` and `risk_score` as derived fields on every request. |
| D-5 | Map `risk_score` to a categorical `risk_tier`; emit a boolean `surge_probable` flag. |
| D-6 | Attach `data_source`, `model_version`, and `survey_year` to every record. |
| D-7 | Expose the entire structure through a Flask REST API queryable by state, tier, or surge flag. |

### 3.3 Transformation Specification

| # | Transformation | Why | How |
|---|---|---|---|
| T-1 | Rename SAMHSA columns to self-describing snake_case | D-1 | Static rename in `app.py` / `mhcews_api.py` on CSV load |
| T-2 | Cast numeric strings to typed floats | D-2 | `float()` on load; suppression markers raise a clear error |
| T-3 | Group fields into four layers + provenance | D-3 | Layer assignment in the JSON response builder |
| T-4 | Compute `care_gap` | D-4 | `any_mi_pct - (any_mi_pct × tx_rate_pct / 100)` |
| T-5 | Compute `risk_score` | D-4 | Weighted formula vs. national averages — see §4.2 |
| T-6 | Assign `risk_tier` | D-5 | Threshold mapping (`106` / `94`) |
| T-7 | Set `surge_probable` flag | D-5 | `care_gap > avg AND smi_pct > avg` |
| T-8 | Attach provenance fields | D-6 | Constants set on each response |
| T-9 | Expose as REST endpoints | D-7 | Flask routes documented in §4.7 |

**Cadence transformation.** NSDUH is published annually. MHCEWS exposes a weekly-cadence-friendly API by recomputing national averages and tiers **on demand** rather than embedding them in the file. When SAMHSA publishes a new annual release, the operator drops in the new CSV and `model_version` is bumped; consumers see a freshly computed result on their next call. No interpolation is applied between releases — the system is honest about the underlying annual cadence and exposes `survey_year` so consumers can reason about staleness.

---

## 4. Improve the Existing Information Structure

### 4.1 New Information Structure

Each state record is organized into four metadata layers plus provenance.

#### Identity Layer — *who and where*

| Field | Type | Description |
|---|---|---|
| `state` | string | Full state name (e.g. "Washington") |
| `abbr` | string (2 chars) | USPS state abbreviation (e.g. "WA") |

#### Signal Layer — *the raw inputs*

| Field | Type | Description | Source column |
|---|---|---|---|
| `any_mi_pct` | float (0–100) | % adults reporting any mental illness | NSDUH `AMIPY` |
| `smi_pct` | float (0–100) | % adults reporting serious mental illness | NSDUH `SMIPY` |
| `mde_pct` | float (0–100) | % adults reporting major depressive episode | NSDUH `MDEPY` |
| `tx_rate_pct` | float (0–100) | % of those with mental illness who received treatment | NSDUH `TXRECMI` |

#### Prediction Layer — *the model output*

| Field | Type | Description |
|---|---|---|
| `care_gap` | float | Untreated-prevalence percentage points |
| `risk_score` | float | Composite weekly crisis risk score (0–150) |
| `risk_tier` | enum | `High` \| `Moderate` \| `Low` |

#### Action Layer — *what to do about it*

| Field | Type | Description |
|---|---|---|
| `surge_probable` | boolean | True if both `care_gap` and `smi_pct` exceed the national average |

#### Provenance Block

| Field | Type | Description |
|---|---|---|
| `data_source` | string | Upstream dataset identifier (e.g. `samhsa_nsduh_2023`) |
| `model_version` | string (semver) | Version of the risk model used to compute this record |
| `survey_year` | integer | NSDUH survey year |

### 4.2 Risk Score Formula

```text
care_gap   = any_mi_pct - (any_mi_pct × tx_rate_pct / 100)

risk_score = (any_mi_pct / national_avg_any_mi) × 40
           + (smi_pct    / national_avg_smi)    × 35
           + (care_gap   / national_avg_gap)    × 25
```

Each `national_avg_*` is the unweighted mean of that field across all 50 states in the current CSV release. The three weights (40 / 35 / 25) sum to 100 so a state at exactly the national average on every input scores 100.

- **Tiers:** `High ≥ 106` · `Moderate ≥ 94` · `Low < 94`
- **Surge flag:** `care_gap > national_avg_gap` AND `smi_pct > national_avg_smi`

### 4.3 Portability vs. Original Structure

MHCEWS changes the source data along **all four** portability dimensions (the rubric requires at least two).

| Dimension | Original SAMHSA CSV | MHCEWS |
|---|---|---|
| **Information** | Raw prevalence only | Adds `care_gap`, `risk_score`, `risk_tier`, `surge_probable` |
| **Structure** | Flat table | Four-layer schema + provenance |
| **Format** | Untyped CSV with codebook-dependent column names | Typed JSON, snake_case, self-describing |
| **Access** | Annual bulk download | REST API, queryable by state / tier / surge flag |

### 4.4 Requirements Traceability Matrix

| Req. # | Requirement | Implementation |
|---|---|---|
| F-1 | Aggregate prevalence + risk score per state | `GET /states` |
| F-2 | Lookup by state abbreviation | `GET /states/<abbr>` |
| F-3 | Filter by risk tier | `GET /states/risk/<tier>` |
| F-4 | National summary | `GET /summary` |
| F-5 | Surge prediction | `GET /predict/surge` |
| F-6 | Provenance on every record | `data_source` + `model_version` in every response |
| F-7 | Regenerable data file | `generate_sample_data.py` |
| P-F | Findable: composite key + schema | `abbr + survey_year` on every record |
| P-A | Accessible: HTTPS, no auth, queryable | Flask REST endpoints |
| P-I | Interoperable: snake_case JSON, USPS abbr | Response builder in `mhcews_api.py` |
| P-R | Reusable: provenance + license | Provenance block + CC BY 4.0 |

### 4.5 Repository Structure

```text
IMT542-Final-Project/
│
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
│
├── nsduh_state_mental_health_2023.csv  # Data file (NSDUH structure)
├── generate_sample_data.py             # Regenerates the CSV if needed
│
├── app.py                              # Command-line analysis tool
├── mhcews_api.py                       # Flask REST API server
├── test_api.py                         # API test script
│
├── G3.json                             # G3: Three ideas (information stories)
├── IMT542 G5.txt                       # G5: FAIR model statement
├── MHCEWS_ethics_impact.html           # G6: Ethics and impact statement
├── samhsa_reformatted.html             # G7: Data quality and security analysis
├── TESTPLAN.md                         # G9: Test plan
└── test_results.md                     # Actual measured test results + remediation
```

### 4.6 Setup and Quick Verification

Python 3.8 or higher required.

```bash
pip install -r requirements.txt
```

After installation, the system can be verified end-to-end in under one minute:

```bash
# Terminal 1 — start the API
python mhcews_api.py
# → server starts at http://localhost:5002

# Terminal 2 — run the test suite
python test_api.py
# → expected: all functional test cases pass

# Terminal 2 — sample queries
curl http://localhost:5002/states/WA
curl http://localhost:5002/predict/surge
curl http://localhost:5002/summary
```

If all three `curl` calls return JSON with the documented fields, the system is functioning as described.

### 4.7 Command-Line Analysis Tool

```bash
python app.py              # Full dashboard — all 50 states
python app.py --state WA   # Single state report
python app.py --risk       # High-risk states and surge prediction only
```

### 4.8 REST API

```bash
python mhcews_api.py
# Server starts at http://localhost:5002
```

| Endpoint | Description |
|---|---|
| `GET /` | API info |
| `GET /states` | All 50 states with risk scores |
| `GET /states/<abbr>` | Single state, e.g. `/states/WA` |
| `GET /states/risk/<tier>` | Filter by `High` / `Moderate` / `Low` |
| `GET /summary` | National summary statistics |
| `GET /predict/surge` | States flagged as surge-probable |

```bash
# Test all endpoints
python test_api.py

# Expose publicly via ngrok
ngrok http 5002
```

---

## 5. Control Quality, Performance, and Security

### 5.1 Quality and Performance Targets

| Metric | Target |
|---|---|
| API uptime (during active dev) | ≥ 99 % |
| Response time p95 | < 500 ms across all endpoints |
| Data completeness | 50 / 50 states present at load |
| Functional test pass rate | 100 % before deployment |
| Risk score range | All scores between 80 and 130 |

The full test plan — including functional, performance, data-quality, alarms, and monitoring requirements — is documented in [`TESTPLAN.md`](./TESTPLAN.md).

### 5.2 Measured Results and Remediation

Actual measured results from running the test plan against the prototype, including any gaps between target and observed performance and the corresponding **remediation plan**, are documented in [`test_results.md`](./test_results.md).

### 5.3 Security and Privacy

- **No personal data.** MHCEWS operates exclusively on state-level aggregates from a public-domain federal release; no individual-level data is collected, stored, or transmitted.
- **Public-read by design.** Aggregate scores are intended to be openly accessible to any responder, journalist, or researcher; therefore the surface is read-only and no auth is required.
- **No write endpoints.** The API exposes only `GET` routes; there is no path through which a caller can mutate state.
- **Provenance enforced.** Every response carries `data_source` and `model_version` so consumers can independently verify the upstream release.
- **Future hardening.** OAuth 2.0 and rate-limiting are listed as out-of-scope future work for any record-level operational stream (e.g. dispatch logs), should the prototype graduate.

### 5.4 Ethics and Limitations

See [`MHCEWS_ethics_impact.html`](./MHCEWS_ethics_impact.html) for the full statement.

- All data is aggregate (state-level). **No individual-level data is collected or stored.**
- Intended for public health coordinators and crisis organizations — not for clinical use.
- Risk scores are probabilistic, not deterministic, and should inform staffing decisions rather than replace local judgment.
- Outputs released under CC BY 4.0; underlying SAMHSA data is U.S. Government public-domain.

---

## Citation

Substance Abuse and Mental Health Services Administration. (2024). *2023–2024 National Survey on Drug Use and Health (NSDUH): State Prevalence Tables.* <https://www.samhsa.gov/data>

*MHCEWS-derived outputs licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*
| Data completeness | 50 / 50 states present at load |
| Functional test pass rate | 100 % before deployment |
| Risk score range | All scores between 80 and 130 |

---

## Ethics and Limitations

See [`MHCEWS_ethics_impact.html`](./MHCEWS_ethics_impact.html) for the full statement.

- All data is aggregate (state-level). **No individual-level data is collected or stored.**
- Intended for public health coordinators and crisis organizations — not for clinical use.
- Risk scores are probabilistic, not deterministic, and should inform staffing decisions rather than replace local judgment.
- Outputs released under CC BY 4.0; underlying SAMHSA data is U.S. Government public-domain.

---

## Grading Artifact Index

A direct map from each rubric criterion to the artifact in this repository.

| # | Rubric Criterion | Artifact(s) |
|---|---|---|
| 1 | **Information Story Documented** | README §[Information Story](#information-story), §[Requirements](#requirements), `G3.json` |
| 2 | **Assessment of Existing Information Structures** | README §[Assessment of the Existing Data](#assessment-of-the-existing-data), §[Transformation Specification](#transformation-specification), `samhsa_reformatted.html`, `IMT542 G5.txt` |
| 3 | **Portable Information Structure from Transformed Existing Information** | README §[Information Structure](#information-structure), §[Portability vs. Original Structure](#portability-vs-original-structure), §[Requirements Traceability Matrix](#requirements-traceability-matrix) |
| 4 | **Functional Information System** | `mhcews_api.py`, `app.py`, `test_api.py`, README §[Quick Verification](#quick-verification) |
| 5 | **Document Performance and Quality** | `TESTPLAN.md`, `test_results.md`, README §[Quality and Performance](#quality-and-performance) |

---

## Citation

Substance Abuse and Mental Health Services Administration. (2024). *2023–2024 National Survey on Drug Use and Health (NSDUH): State Prevalence Tables.* <https://www.samhsa.gov/data>

---

*MHCEWS-derived outputs licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*
