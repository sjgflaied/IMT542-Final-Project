# Mental Health Crisis Early-Warning System (MHCEWS)

> **IMT 542 — Portable Information Structures | Final Project**
> Group 5 · University of Washington Information School

---

## Table of Contents

- [Project Overview](#project-overview)
- [Information Story](#information-story)
- [Requirements](#requirements)
- [Data Source](#data-source)
- [Assessment of the Existing Data](#assessment-of-the-existing-data)
- [Information Structure](#information-structure)
- [Risk Score Formula](#risk-score-formula)
- [Transformation Specification](#transformation-specification)
- [Portability vs. Original Structure](#portability-vs-original-structure)
- [Requirements Traceability Matrix](#requirements-traceability-matrix)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Quick Verification](#quick-verification)
- [Command-Line Analysis Tool](#command-line-analysis-tool)
- [REST API](#rest-api)
- [Quality and Performance](#quality-and-performance)
- [Ethics and Limitations](#ethics-and-limitations)
- [Grading Artifact Index](#grading-artifact-index)
- [Citation](#citation)

---

## Project Overview

The **Mental Health Crisis Early-Warning System (MHCEWS)** restructures publicly available SAMHSA mental health data into a portable, queryable information structure that predicts which U.S. states are at risk of a mental health crisis surge.

The original SAMHSA data is published as a flat, untyped CSV with no geographic identifiers below the state level, no versioning, and no access control. It exists — but it is not portable. MHCEWS transforms it into a typed JSON schema with computed fields, a REST API, and a command-line analysis tool, so that the same data can drive a real-time dashboard, an automated alert, or a staffing decision.

**Insight area: Predict.** The system predicts which states will experience a mental health crisis surge in the next 2–4 weeks based on the intersection of care gap and serious mental illness prevalence.

---

## Information Story

### Primary User

| | |
|---|---|
| **Role** | 211 crisis line coordinator / state public health analyst |
| **Organization** | A regional 211 contact center or state behavioral health agency |
| **Goal** | Allocate weekly staffing and outreach resources across regions |
| **Decision cadence** | Weekly capacity planning + ad-hoc surge response |

### Problem Statement

When the coordinator opens her week, she has no leading indicator of whether call volume will exceed capacity. The most authoritative source — the SAMHSA NSDUH State Prevalence Tables — is published once a year as a CSV that requires a separate PDF codebook to interpret. By the time she has it cleaned and joined to her own staffing roster, it is already two years stale and offers no computed risk signal. She is forced to make a high-stakes staffing decision either from intuition or from a hand-built spreadsheet.

### What MHCEWS Delivers

MHCEWS restructures the same SAMHSA data into a weekly, state-level risk signal accessible via API. A single call to `GET /predict/surge` returns a ranked list of states where care gap and serious mental illness prevalence both exceed the national average — a leading indicator of crisis line overflow. The coordinator gets a typed, machine-readable record per state with `risk_score`, `risk_tier`, and an actionable `surge_probable` flag, plus provenance fields so the underlying NSDUH release and model version are traceable.

### Motivation

Mental health crisis response in the United States is delivered by a fragmented network of state agencies, 211 / 988 lines, and community organizations, each making weekly resource decisions on local data. Making the national prevalence signal **portable** — typed, computed, queryable — lets those frontline coordinators act on the same evidence base without each rebuilding a CSV pipeline. The underlying insight already exists in public data; only the information structure prevents it from being used.

---

## Requirements

### Functional Requirements

1. Return aggregate mental-health prevalence and a computed risk score for each of the 50 U.S. states.
2. Support lookup by individual state abbreviation.
3. Support filtering by computed risk tier (`High`, `Moderate`, `Low`).
4. Return a national-summary endpoint with averages and tier counts.
5. Return a surge-prediction endpoint listing only states that meet the surge criterion.
6. Every response must include provenance fields (`data_source`, `model_version`).
7. The data file backing the API must be regenerable from a single Python script.

### Portability Requirements (FAIR)

| Principle | Requirement |
|---|---|
| **Findable** | Each record uniquely identified by `abbr + survey_year`; schema is self-describing; no PDF codebook required to interpret any field. |
| **Accessible** | Aggregate scores accessible over HTTPS with no authentication; queryable by state, tier, or surge flag; on-demand recomputation. |
| **Interoperable** | snake_case JSON fields aligned with JSON-LD practice; standard USPS state abbreviations; ISO 8601 dates where applicable; typed numeric fields. |
| **Reusable** | `data_source` and `model_version` on every record; license clearly stated; transformation logic open-source in this repository. |

### In Scope

- State-level aggregate risk prediction (50 U.S. states)
- Weekly cadence (model recomputes on demand from the latest CSV release)
- Public, no-auth read access to aggregate risk scores
- Surge prediction based on `care_gap × smi_pct`
- Provenance fields on every record
- REST API + command-line analysis tool

### Out of Scope

- Individual-level or ZIP / county-level data
- Real-time 988 / 211 call-volume integration
- Clinical diagnostic recommendations
- Cross-country or international data
- Write access, user accounts, or user-submitted data
- OAuth 2.0 / authenticated feeds (listed as future work)

---

## Data Source

**SAMHSA NSDUH 2023–2024 State Prevalence Tables**

| | |
|---|---|
| **Publisher** | Substance Abuse and Mental Health Services Administration |
| **URL** | <https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health/state-releases> |
| **Format** | CSV |
| **Coverage** | All 50 U.S. states, civilian non-institutionalized population aged 12+ |
| **Update frequency** | Annual |
| **License** | U.S. Government Open Data (public domain) |

> **Note on the included file.** `nsduh_state_mental_health_2023.csv` in this repository is a **synthetic dataset** generated by `generate_sample_data.py` that matches the schema and value ranges of the real NSDUH State Prevalence Tables. It is used for prototyping and demonstration. To run MHCEWS on the actual SAMHSA release, download the official CSV from the URL above and replace the included file — the transformation logic, API endpoints, and risk model are identical in both cases.

---

## Assessment of the Existing Data

This section evaluates the **original** SAMHSA NSDUH data **before** any transformation. It is the evidence base for why a portable restructure is needed.

### Structure

The NSDUH State Prevalence Tables are published as a single flat CSV. Each row is a state; each column is a prevalence measure. Column names use SAMHSA-internal abbreviations (e.g. `AMIPY`, `SMIPY`, `MDEPY`, `TXRECMI`) that cannot be interpreted without the accompanying PDF codebook. Values are untyped — numeric values, suppression markers, and missing flags all appear as strings in the same column.

### Original Use Case

The data is designed for **annual epidemiological reporting**, not for operational decision-making. Its intended audience is researchers writing peer-reviewed surveillance articles. It was not designed for an API consumer, a dashboard, or a weekly staffing decision.

### Access Methodology

| Aspect | Original SAMHSA |
|---|---|
| Distribution | Annual bulk CSV download from a static URL |
| Authentication | None |
| Query interface | None — file is downloaded whole |
| Programmatic filter | None — requires local processing |
| Rate limit | N/A (static file) |

### Quality

- **Completeness:** 50 / 50 states present in each annual release.
- **Suppression:** small-sample cells are suppressed; the suppression marker is a string, not a typed null, requiring downstream cleanup.
- **Documentation:** column meaning requires the separate codebook PDF; field-level metadata is not embedded in the file.
- **Staleness:** annual release cadence means up to 24 months of lag between the survey period and the published table.

### Performance

A static CSV has no runtime performance — but the operational cost is in the pipeline a consumer has to build every year: download, decode, clean suppression markers, join the codebook, and compute any derived field. There is no programmatic way to ask "which states are above the national average on serious mental illness?"; the consumer must compute it locally each time.

### FAIR Assessment — Original vs. MHCEWS

| Principle | Original SAMHSA CSV | MHCEWS |
|---|---|---|
| **Findable** | File URL is hard to locate from the SAMHSA portal; no unique record ID; PDF codebook required to interpret columns. | `abbr + survey_year` composite key; four-layer schema; every field self-describing. |
| **Accessible** | Bulk download only; annual cadence; no API; no programmatic filtering. | REST over HTTPS; queryable by state, tier, or surge flag; on-demand recomputation. |
| **Interoperable** | No schema; non-standard column abbreviations; untyped values; no controlled vocabulary. | snake_case JSON; ISO 8601 dates; standard USPS state abbreviations; typed numeric fields. |
| **Reusable** | No provenance; no version number; license stated only on the parent portal. | `data_source` and `model_version` on every record; CC BY 4.0 explicit on derived outputs. |

---

## Information Structure

Each state record is organized into four metadata layers plus provenance.

### Identity Layer — *who and where*

| Field | Type | Description |
|---|---|---|
| `state` | string | Full state name (e.g. "Washington") |
| `abbr` | string (2 chars) | USPS state abbreviation (e.g. "WA") |

### Signal Layer — *the raw inputs*

| Field | Type | Description | Source column |
|---|---|---|---|
| `any_mi_pct` | float (0–100) | % adults reporting any mental illness | NSDUH `AMIPY` |
| `smi_pct` | float (0–100) | % adults reporting serious mental illness | NSDUH `SMIPY` |
| `mde_pct` | float (0–100) | % adults reporting major depressive episode | NSDUH `MDEPY` |
| `tx_rate_pct` | float (0–100) | % of those with mental illness who received treatment | NSDUH `TXRECMI` |

### Prediction Layer — *the model output*

| Field | Type | Description |
|---|---|---|
| `care_gap` | float | Untreated-prevalence percentage points |
| `risk_score` | float | Composite weekly crisis risk score (0–150) |
| `risk_tier` | enum | `High` \| `Moderate` \| `Low` |

### Action Layer — *what to do about it*

| Field | Type | Description |
|---|---|---|
| `surge_probable` | boolean | True if both `care_gap` and `smi_pct` exceed the national average |

### Provenance

| Field | Type | Description |
|---|---|---|
| `data_source` | string | Upstream dataset identifier (e.g. `samhsa_nsduh_2023`) |
| `model_version` | string (semver) | Version of the risk model used to compute this record |
| `survey_year` | integer | NSDUH survey year |

---

## Risk Score Formula

```text
care_gap   = any_mi_pct - (any_mi_pct × tx_rate_pct / 100)

risk_score = (any_mi_pct / national_avg_any_mi) × 40
           + (smi_pct    / national_avg_smi)    × 35
           + (care_gap   / national_avg_gap)    × 25
```

Each `national_avg_*` is the unweighted mean of that field across all 50 states in the current CSV release. The three weights (40 / 35 / 25) sum to 100 so a state at exactly the national average on every input scores 100.

- **Tiers:** `High ≥ 106` · `Moderate ≥ 94` · `Low < 94`
- **Surge flag:** `care_gap > national_avg_gap` AND `smi_pct > national_avg_smi`

---

## Transformation Specification

Each transformation below addresses a specific deficiency identified in the [Assessment of the Existing Data](#assessment-of-the-existing-data).

| # | Transformation | Why | How |
|---|---|---|---|
| 1 | Rename `AMIPY`, `SMIPY`, `MDEPY`, `TXRECMI` → `any_mi_pct`, `smi_pct`, `mde_pct`, `tx_rate_pct` | Original column names are non-self-describing and require the PDF codebook. | Static rename in `app.py` / `mhcews_api.py` on CSV load. |
| 2 | Cast numeric strings to typed floats | Original values are strings; cannot be aggregated without local parsing. | `float()` on load; suppression markers raise a clear error rather than silent NaN. |
| 3 | Group fields into four layers | Original is a flat row; consumers cannot tell raw inputs from computed outputs. | Layer assignment via the JSON response builder. |
| 4 | Compute `care_gap` | Original has no untreated-prevalence measure; consumers must compute it themselves. | Formula in [Risk Score Formula](#risk-score-formula). |
| 5 | Compute `risk_score` | Original has no composite risk signal — the user's actual decision input. | Weighted formula; national_avg recomputed on each request. |
| 6 | Assign `risk_tier` | A continuous score is not directly usable for a triage decision. | Threshold mapping (106 / 94). |
| 7 | Set `surge_probable` flag | The Action layer needs a single boolean for the surge-prediction endpoint. | `care_gap > avg AND smi_pct > avg`. |
| 8 | Attach `data_source` and `model_version` | Original CSV carries no provenance; reviewers cannot trace a number back to the release. | Constants set on each response. |

**Cadence transformation.** NSDUH is published annually. MHCEWS exposes a weekly-cadence-friendly API by recomputing the national averages and tiers **on demand** rather than embedding them in the file. When SAMHSA publishes a new annual release, the operator drops in the new CSV and `model_version` is bumped; consumers see a freshly computed result on their next call. No interpolation is applied between releases — the system is honest about the underlying annual cadence and exposes `survey_year` so consumers can reason about staleness.

---

## Portability vs. Original Structure

MHCEWS changes the source data along **all four** portability dimensions (the rubric requires at least two).

| Dimension | Original SAMHSA CSV | MHCEWS |
|---|---|---|
| **Information** | Raw prevalence only | Adds `care_gap`, `risk_score`, `risk_tier`, `surge_probable` |
| **Structure** | Flat table | Four-layer schema (Identity / Signal / Prediction / Action) + provenance |
| **Format** | Untyped CSV with codebook-dependent column names | Typed JSON, snake_case, self-describing |
| **Access** | Annual bulk download | REST API, queryable by state / tier / surge flag |

Additionally:

- **Computed fields:** none → four
- **Prediction endpoint:** none → `/predict/surge`
- **Versioning:** none → `model_version` on every record

---

## Requirements Traceability Matrix

Each requirement from the [Requirements](#requirements) section is implemented by a specific field, endpoint, or piece of code.

| Req. # | Requirement | Implementation |
|---|---|---|
| F-1 | Aggregate prevalence + risk score per state | `GET /states` |
| F-2 | Lookup by state abbreviation | `GET /states/<abbr>` |
| F-3 | Filter by risk tier | `GET /states/risk/<tier>` |
| F-4 | National summary | `GET /summary` |
| F-5 | Surge prediction | `GET /predict/surge` |
| F-6 | Provenance fields on every record | `data_source` + `model_version` in every response |
| F-7 | Regenerable data file | `generate_sample_data.py` |
| P-F | Findable: composite key + schema | `abbr + survey_year` returned on every record |
| P-A | Accessible: HTTPS, no auth, queryable | Flask REST endpoints listed above |
| P-I | Interoperable: snake_case JSON, USPS abbr | Response builder in `mhcews_api.py` |
| P-R | Reusable: provenance + license | Provenance block + CC BY 4.0 on derived outputs |

---

## Repository Structure

```
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

---

## Setup

Python 3.8 or higher required.

```bash
pip install -r requirements.txt
```

---

## Quick Verification

After installation, anyone cloning the repo can verify the system end-to-end in under one minute:

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

If all three `curl` calls return JSON with the documented fields, the system is functioning as described in this README.

---

## Command-Line Analysis Tool

```bash
python app.py              # Full dashboard — all 50 states
python app.py --state WA   # Single state report
python app.py --risk       # High-risk states and surge prediction only
```

---

## REST API

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

## Quality and Performance

The full test plan — including functional, performance, data-quality, and monitoring requirements — is documented in [`TESTPLAN.md`](./TESTPLAN.md).

Actual measured results from running the test plan against the prototype, including any gaps between target and observed performance and the corresponding **remediation plan**, are documented in [`test_results.md`](./test_results.md).

### Quality Targets at a Glance

| Metric | Target |
|---|---|
| API uptime (during active dev) | ≥ 99 % |
| Response time p95 | < 500 ms across all endpoints |
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
