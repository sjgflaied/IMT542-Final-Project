# IMT542-G8
G8 Improve access methodology of existing information
# Mental Health Crisis Early-Warning System (MHCEWS)

**Group 5 — IMT 542**
*Portable Information Structure Documentation*

> **Note on scope:** MHCEWS is a *proposed* information structure designed for this assignment. It is not a deployed service. The example in this document demonstrates how MHCEWS records can be assembled from **real, publicly accessible APIs** — primarily the [CDC PLACES](https://www.cdc.gov/places/) Socrata Open Data API and the [SAMHSA FindTreatment.gov](https://findtreatment.gov/) locator — so that the structure can be implemented today using existing federal open-data infrastructure.

---

## About

The Mental Health Crisis Early-Warning System (MHCEWS) is a portable information structure for publishing ZIP-code-level weekly mental-health risk records in the United States. The intended audience includes **public-health agencies, 988/crisis-line operators, community mental-health organizations, and academic researchers** who need an early signal to guide outreach, staffing, and resource allocation. Aggregate risk scores are designed to be openly available without authentication so that any responder, journalist, or researcher can act on them, while record-level operational data (such as real-time dispatch logs) would be gated behind OAuth 2.0 for privacy reasons. Every record is uniquely identified by the composite key `zip_code + week_start_date` (ISO 8601) and is described through a four-layer metadata structure — **Identity, Signal, Prediction, Action** — so downstream systems can consume the data without additional context.

---

## Methodology

- **Inputs are drawn from real federal open-data services**, including:
  - **CDC PLACES** (`data.cdc.gov`) — ZCTA-level prevalence estimates for *frequent mental distress*, *social isolation*, *lack of social and emotional support*, and other health-related social needs, derived from BRFSS and ACS.
  - **SAMHSA FindTreatment.gov locator** — list of nearby licensed mental-health and crisis-treatment facilities by ZIP code.
  - **988 Suicide & Crisis Lifeline** aggregate call data (where state agencies publish it; not yet uniformly available as an API).
- **A composite risk model** combines these inputs into a 0–100 weekly risk score per ZCTA and assigns a categorical `risk_tier` (low / moderate / elevated / high).
- **Each record carries its own provenance block** capturing `data_source` (with the upstream dataset ID), `model_version`, and `data_freshness` timestamps for every contributing input, so every score is fully traceable back to the upstream federal release.
- **The schema follows FAIR principles**: Findable (composite key + four-layer metadata), Accessible (REST over HTTPS, OAuth 2.0 only where needed), Interoperable (snake_case JSON-LD, Census FIPS and ZCTA ZIP standards), Reusable (CC BY 4.0 license, full provenance).
- **Field names use snake_case** aligned with JSON-LD practice; geographic identifiers use the same ZCTA codes used by CDC PLACES and Census Bureau vocabularies (FIPS, ZCTA).
- **Both human-readable labels and machine-readable typed values** are emitted for every field so analysts and automated pipelines can read the same payload.
- **The model would be re-trained on each CDC PLACES annual release**; `model_version` is bumped on every retrain and old versions remain queryable for reproducibility.
- **Data freshness is monitored** because PLACES updates annually while SAMHSA locator data updates weekly — the `data_freshness` block surfaces each input's last-updated timestamp rather than silently mixing stale and fresh data.
- **Public outputs are released under Creative Commons Attribution 4.0**, consistent with the open-data licensing of the underlying federal sources.

---

## Access

Until MHCEWS is deployed as a standalone API, users can access its underlying inputs directly through the real federal endpoints listed below. The intended workflow is:

1. **Read the CDC PLACES documentation** at <https://www.cdc.gov/places/tools/data-portal.html> and the SAMHSA FindTreatment developer guide at <https://findtreatment.gov/assets/FindTreatment-Developer-Guide.pdf>.
2. **Decide which tier of data is needed.** Aggregate health-prevalence estimates from CDC PLACES are fully open (no auth). Treatment-facility lookups from SAMHSA are also open. Any future record-level operational stream (e.g. dispatch logs) would require OAuth 2.0.
3. **Query the CDC PLACES ZCTA dataset** via the Socrata Open Data API (SODA). The resource ID for the current ZCTA release is `qnzd-25i4`; the JSON endpoint is:
   `https://data.cdc.gov/resource/qnzd-25i4.json`
4. **Filter by ZCTA and measure** using SoQL query parameters, for example:
   `?locationname=98101&measureid=MHLTH`
   (`MHLTH` = *frequent mental distress among adults*).
5. **Query the SAMHSA FindTreatment.gov locator** for nearby crisis-care resources to populate the Action layer.
6. **Parse the JSON response** and map it into the MHCEWS four-layer schema (Identity, Signal, Prediction, Action) plus provenance block.
7. **Cite the data** using the upstream `data_source` IDs (e.g. `cdc_places_zcta_qnzd-25i4`) and `model_version`. Reuse falls under CC BY 4.0 for MHCEWS-derived outputs; upstream sources retain their own licenses (CDC PLACES is U.S. Government work; SAMHSA locator is public-domain).

---

## Structure

Every record is a JSON object organized into four metadata layers plus provenance. The composite primary key is `zip_code + week_start_date`.

### Identity layer — *who and where*

| Field | Type | Description |
|---|---|---|
| `zip_code` | string (ZCTA, 5-digit) | U.S. Census ZCTA ZIP code (matches CDC PLACES `locationname`) |
| `state_fips` | string (2-digit) | Census state FIPS code |
| `county_fips` | string (5-digit) | Census county FIPS code |
| `week_start_date` | string (ISO 8601 date) | Monday of the ISO week |

### Signal layer — *the raw inputs*

| Field | Type | Description | Upstream source |
|---|---|---|---|
| `frequent_mental_distress_pct` | float (0–100) | % adults reporting frequent mental distress | CDC PLACES `MHLTH` |
| `social_isolation_pct` | float (0–100) | % adults reporting feeling socially isolated | CDC PLACES `ISOLATION` |
| `lack_emotional_support_pct` | float (0–100) | % adults lacking social and emotional support | CDC PLACES `EMOTIONSPT` |
| `nearby_treatment_facility_count` | integer | Count of SAMHSA-listed mental-health facilities within the ZIP | SAMHSA FindTreatment.gov |

### Prediction layer — *the model output*

| Field | Type | Description |
|---|---|---|
| `risk_score` | float (0–100) | Composite weekly crisis risk score |
| `risk_tier` | enum | `low` \| `moderate` \| `elevated` \| `high` |
| `confidence_interval` | object `{lower: float, upper: float}` | 95% CI on the risk score |
| `trend_4wk` | enum | `rising` \| `stable` \| `falling` |

### Action layer — *what to do about it*

| Field | Type | Description |
|---|---|---|
| `recommended_action` | string | Human-readable suggested response |
| `priority` | enum | `routine` \| `watch` \| `urgent` |
| `suggested_resources` | array of strings | URIs of relevant local resources (e.g. 988, SAMHSA facility pages) |

### Provenance block

| Field | Type | Description |
|---|---|---|
| `data_source` | array of strings | Identifiers of contributing inputs (e.g. `cdc_places_zcta_qnzd-25i4`) |
| `model_version` | string (semver) | Version of the risk model used |
| `data_freshness` | object `{source: timestamp}` | Last-updated timestamp per input |
| `license` | string | `CC-BY-4.0` for MHCEWS-derived outputs |

---

## Example

### Use case
A King County public-health analyst wants this week's mental-health crisis risk for ZIP code 98101 (downtown Seattle) so she can decide whether to surge mobile crisis team coverage. The MHCEWS Signal layer is populated by a live call to the real CDC PLACES API.

### Request to CDC PLACES (Signal-layer input — real, executable)

```http
GET /resource/qnzd-25i4.json?locationname=98101&measureid=MHLTH HTTP/1.1
Host: data.cdc.gov
Accept: application/json
```

No authentication header is required — CDC PLACES is fully open via the Socrata SODA API.

### Response from CDC PLACES (truncated, illustrative)

```json
[
  {
    "year": "2024",
    "locationname": "98101",
    "datasource": "BRFSS",
    "category": "Health Status",
    "measure": "Frequent mental distress among adults",
    "measureid": "MHLTH",
    "data_value_type": "Crude prevalence",
    "data_value": "16.8",
    "low_confidence_limit": "15.4",
    "high_confidence_limit": "18.3",
    "totalpopulation": "13095",
    "geolocation": { "type": "Point", "coordinates": [-122.3331, 47.6097] }
  }
]
```

### Assembled MHCEWS record (what MHCEWS would return downstream)

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

### Interpretation
The analyst sees `risk_tier: "elevated"` with a `rising` 4-week trend and an `urgent` recommended priority. She uses the `recommended_action` text directly in her staffing memo, cites the upstream `data_source` IDs (so a reviewer can re-pull the exact CDC PLACES row), and routes the suggested SAMHSA and 988 links to her communications team.

---

## Real APIs referenced in this document

| Service | Base URL | Auth | License |
|---|---|---|---|
| CDC PLACES ZCTA dataset (Socrata SODA) | `https://data.cdc.gov/resource/qnzd-25i4.json` | None (public) | U.S. Government work |
| CDC PLACES portal | <https://www.cdc.gov/places/> | n/a | n/a |
| SAMHSA FindTreatment.gov | <https://findtreatment.gov/> | API key on request | Public-domain |
| 988 Suicide & Crisis Lifeline | <https://988lifeline.org/> | n/a | n/a |

*License for MHCEWS-derived outputs: CC BY 4.0 — see `provenance.license` on every record.*

# Mental Health Crisis Early-Warning System – Test Plan

## Purpose

This document outlines the testing strategy for ensuring the quality, accuracy, and performance of the MHCEWS API and data pipeline. It serves as a living reference to guide development, deployment, and ongoing maintenance, and to assure users that the quality of data and information structure access is reliable.

---

## System Overview

- **Data Source**: SAMHSA NSDUH 2023–2024 State Prevalence Tables (CSV)
- **Backend**: Flask API (`mhcews_api.py`), hosted locally or via cloud deployment
- **Exposure**: ngrok tunnel (development) / cloud endpoint (production)
- **Endpoints**:
  - `GET /` — API info
  - `GET /states` — All 50 states with risk scores
  - `GET /states/<abbr>` — Single state lookup (e.g. `/states/WA`)
  - `GET /states/risk/<tier>` — Filter by risk tier: High / Moderate / Low
  - `GET /summary` — National summary statistics
  - `GET /predict/surge` — States flagged as surge-probable

---

## Test Objectives

- Ensure all API endpoints return correct data and status codes
- Verify risk score and care gap calculations are accurate and consistent
- Confirm the API handles invalid inputs gracefully without crashing
- Measure response time under normal and high load conditions
- Detect and respond to data quality issues in source CSV
- Provide clear traceability for any failures through logs and alarms

---

## Functional Testing

| Test Case | Description | Method | Expected Result |
|-----------|-------------|--------|-----------------|
| API root | `GET /` returns API metadata | curl or requests.get | 200, JSON with endpoint list |
| All states | `GET /states` returns 50 records | Automated check `len(data) == 50` | 200, count = 50 |
| Valid state lookup | `GET /states/WA` returns Washington data | Manual or pytest | 200, `state = "Washington"`, `risk_tier` present |
| Invalid state | `GET /states/XX` returns error | Direct request | 404, error message returned |
| Risk tier filter — High | `GET /states/risk/High` returns only High records | Check all `risk_tier == "High"` | 200, all records match tier |
| Risk tier filter — invalid | `GET /states/risk/Critical` | Direct request | 400, error message |
| Summary stats | `GET /summary` returns national averages | Check key fields present | 200, all 7 expected fields present |
| Surge prediction | `GET /predict/surge` returns surge-probable states | Verify criteria match | 200, all records have `care_gap > avg` AND `smi_pct > avg` |
| Sort parameter | `GET /states?sort=care_gap` returns sorted list | Check first record has highest care_gap | 200, descending order confirmed |
| Risk score range | All risk scores within expected range | Automated check | All scores between 80 and 130 |
| Care gap calculation | `care_gap = any_mi_pct - (any_mi_pct * tx_rate / 100)` | Unit test per state | Matches manual calculation to 2 decimal places |
| Data completeness | All 50 states present in CSV | Row count check on load | Exactly 50 records loaded |
| No null fields | No missing values in any record | Check all fields on load | Zero null or empty string values |

---

## Performance Testing

| Test Case | Description | Tool | Target |
|-----------|-------------|------|--------|
| Cold start | Load server after idle, first request | Browser or Postman | < 1.5s |
| Single request | `GET /states/WA` response time | Postman or time in Python | < 200ms |
| Full dataset | `GET /states` returns all 50 records | Postman | < 500ms |
| Concurrent users | 20 simultaneous requests to `/states` | Locust or Artillery.io | API remains stable, < 2s |
| High load | 100 requests in 10 seconds | Locust | No 500 errors, < 3s p95 |
| Summary endpoint | `GET /summary` compute time | requests + timer | < 300ms |
| Surge endpoint | `GET /predict/surge` filter time | requests + timer | < 300ms |

---

## Data Quality Tests

| Test | Check | Trigger | Action |
|------|-------|---------|--------|
| Row count | CSV has exactly 50 rows | On server start | Raise error, halt server start |
| Field types | All `_pct` fields are valid floats | On ingest | Log error, skip malformed row |
| Value ranges | `any_mi_pct` between 0–100 | On ingest | Flag row, exclude from scoring |
| State abbr | All abbreviations are 2-character uppercase | On ingest | Log warning |
| No duplicates | No duplicate `abbr` values | On ingest | Log error, keep first occurrence |
| Care gap logic | `care_gap` >= 0 for all records | Post-calculation | Alert if any negative care gap found |
| Risk tier coverage | At least one state in each tier | Post-calculation | Log warning if any tier is empty |

---

## Alarms & Monitoring

| Alarm | Trigger | Action |
|-------|---------|--------|
| Server down | No response from `/` for 60 seconds | Alert via UptimeRobot email notification |
| High latency | Response time > 3s for any endpoint | Log incident, investigate data load time |
| 500 error spike | More than 3 server errors in 1 minute | Write to error log, notify maintainer |
| Data load failure | CSV missing or malformed on startup | Server refuses to start, log clear error message |
| Score anomaly | Any `risk_score` outside 50–150 range | Flag record in response, log warning |
| Surge count zero | `predict/surge` returns 0 states | Log warning — may indicate threshold misconfiguration |

Planned monitoring tools:
- [UptimeRobot](https://uptimerobot.com/) — endpoint availability ping every 5 minutes
- Flask built-in logging — all requests and errors written to `mhcews.log`
- GitHub Actions — run functional tests on every push to main branch

---

## Continuous Testing & Maintenance

- Manual smoke test (`python3 test_api.py`) after every code change
- GitHub Actions workflow to run functional tests on each push
- CSV source reviewed against SAMHSA release page quarterly for updated data
- Risk score thresholds reviewed annually when new NSDUH data is published
- All test failures logged with timestamp, endpoint, and error message
- Test plan updated whenever new endpoints are added or data schema changes

---

## Quality Metrics

| Metric | Goal |
|--------|------|
| API uptime | 99% during active development |
| Response time (p95) | < 500ms for all endpoints |
| Data completeness | 50/50 states present at all times |
| Functional test pass rate | 100% before any production deployment |
| Risk score accuracy | Matches manual calculation to 2 decimal places |
| Zero 500 errors | No unhandled server errors in normal operation |

---

## Status Summary

| Area | Status |
|------|--------|
| Functional tests | ✅ Implemented via `test_api.py` (7 test cases) |
| Data quality checks | ✅ Validated on server start |
| Performance tests | ⚠️ Manual timing complete; Locust scripting planned |
| Alarms / monitoring | 🔜 UptimeRobot to be configured post-deployment |
| CI/CD integration | 🔜 GitHub Actions workflow planned |
| Error logging | ✅ Flask built-in logging active |

---

## Team Responsibilities

| Task | Owner |
|------|-------|
| API endpoint testing | Individual developer |
| Data quality validation | Data pipeline lead |
| Performance benchmarking | Backend developer |
| Monitoring setup | DevOps / deployment lead |
| Quarterly data refresh | Data maintainer |
| Test plan updates | All team members |

---

## Future Additions

- Pytest framework for automated backend endpoint validation
- JSON schema validation on all API responses
- Automated data freshness check against SAMHSA release calendar
- Dashboard for real-time API health metrics
- Expanded surge prediction model with additional leading indicators (unemployment claims, 211 call volume)

