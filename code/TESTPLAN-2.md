# Mental Health Crisis Early-Warning System – Test Plan

## Purpose

This document outlines the testing strategy for the MHCEWS API and data pipeline, built on real CDC PLACES ZCTA data. It serves as a living reference to guide development and ongoing maintenance, and to assure users that data quality and API access are reliable.

---

## System Overview

- **Data Source**: CDC PLACES ZCTA Data 2024 Release — `https://data.cdc.gov/resource/qnzd-25i4.json`
- **Local file**: `cdc_places_zcta_mh.csv` (downloaded via `download_cdc_places.py`)
- **Backend**: Flask API (`mhcews_api.py`), port 5002
- **Exposure**: ngrok tunnel (development) / cloud endpoint (production)
- **Mental health measures used**:
  - `MHLTH` — Frequent mental distress among adults
  - `DEPRESSION` — Depression prevalence
  - `EMOTIONSPT` — Lack of social/emotional support
  - `LONELINESS` — Loneliness prevalence

**Endpoints:**
- `GET /` — API info
- `GET /zipcodes` — All ZIP codes with risk scores
- `GET /zipcodes/<zip>` — Single ZIP code lookup
- `GET /zipcodes/risk/<tier>` — Filter by High / Moderate / Low
- `GET /summary` — National summary statistics
- `GET /predict/surge` — Surge-probable ZIP codes
- `GET /refresh` — Re-load data from CSV

---

## Test Objectives

- Ensure all API endpoints return correct data and HTTP status codes
- Verify risk score and care gap calculations match expected formulas
- Confirm CDC PLACES data is correctly pivoted from measure-per-row to ZIP-per-record
- Confirm the API handles invalid inputs gracefully
- Measure response time under normal and concurrent load
- Detect and respond to data quality issues in the source CSV
- Provide audit traceability through model_version and data_source fields

---

## Functional Tests

| Test Case | Description | Method | Expected Result |
|-----------|-------------|--------|-----------------|
| API root | `GET /` returns API metadata | curl or requests.get | 200, JSON with endpoint list and zip_codes_loaded count |
| Data load | CSV loads correctly on server start | Check console log | Log shows N ZIP codes loaded |
| ZIP lookup — valid | `GET /zipcodes/98118` returns Rainier Valley data | Direct request | 200, all 4 MH measure fields present |
| ZIP lookup — invalid | `GET /zipcodes/00000` returns error | Direct request | 404, error message |
| All ZIPs | `GET /zipcodes` returns all records | Check count field | 200, count matches zip_codes_loaded |
| Sort by distress | `GET /zipcodes?sort=frequent_mental_distress_pct` | Check first record | 200, first record has highest distress value |
| Limit param | `GET /zipcodes?limit=5` | Check count | 200, exactly 5 records returned |
| Risk tier — High | `GET /zipcodes/risk/High` returns only High records | Check all risk_tier fields | 200, all records have risk_tier = "High" |
| Risk tier — invalid | `GET /zipcodes/risk/Critical` | Direct request | 400, error message |
| Summary fields | `GET /summary` has all expected fields | Check keys | 200, 11 expected fields present |
| Surge criteria | `GET /predict/surge` — all records meet criteria | Verify each record | All have distress > national avg AND depression > national avg |
| Care gap formula | care_gap = distress_pct × (lack_support / 100) | Unit test per ZIP | Matches formula to 2 decimal places |
| Risk score formula | risk_score = weighted composite of 3 measures | Unit test per ZIP | Consistent with national avg normalization |
| model_version field | Every record contains model_version | Check sample records | model_version = "mhcews-v2.0.0" |
| Refresh endpoint | `GET /refresh` re-loads data | Direct request | 200, zip_codes_loaded matches file |

---

## Performance Tests

| Test Case | Description | Tool | Target |
|-----------|-------------|------|--------|
| Cold start | Server start + first request | Browser or curl | < 2s |
| ZIP lookup | `GET /zipcodes/98118` response time | requests + timer | < 150ms |
| All ZIPs | `GET /zipcodes` full dataset | requests + timer | < 500ms |
| Surge endpoint | `GET /predict/surge` filter time | requests + timer | < 300ms |
| Concurrent — 10 users | 10 simultaneous requests to `/zipcodes` | Locust or manual | No errors, < 1.5s |
| Concurrent — 50 users | 50 simultaneous requests | Locust | No 500 errors, < 3s p95 |
| Large dataset | Full CDC PLACES download (~32,000 ZIPs) | Load test | Server starts and responds within 5s |

---

## Data Quality Tests

| Test | Check | Trigger | Action |
|------|-------|---------|--------|
| CSV row count | File has rows for all 4 measure IDs | On server start | Warn if any measure is missing |
| Measure coverage | All 4 MH measures present per ZIP | On load | Log ZIPs missing any measure |
| Float values | All data_value fields parseable as float | On ingest | Skip row, log warning |
| Value ranges | Percentages between 0 and 100 | On ingest | Flag record if outside range |
| No duplicate ZIPs | Each ZIP code appears once in output | Post-pivot | Log warning if duplicates detected |
| care_gap non-negative | care_gap >= 0 for all records | Post-calculation | Alert if any negative value |
| Risk tier coverage | At least one ZIP in each tier | Post-enrichment | Log warning if any tier is empty |
| Confidence intervals | low_ci < data_value < high_ci | On ingest | Log data quality warning |
| geolocation format | Valid JSON with coordinates array | On ingest | Skip geo fields if malformed |
| model_version present | Every output record has model_version | On output | Raise error if field missing |

---

## Alarms & Monitoring

| Alarm | Trigger | Action |
|-------|---------|--------|
| Server down | No response from `/` for 60 seconds | UptimeRobot email alert |
| High latency | Any endpoint response > 3s | Log incident, investigate data size |
| 500 error spike | More than 3 server errors in 1 minute | Write to error log, notify maintainer |
| CSV missing | `cdc_places_zcta_mh.csv` not found on startup | Server refuses to start, clear error message |
| Zero ZIPs loaded | Load returns 0 records | Halt startup, alert — file may be empty or corrupt |
| Surge count zero | `/predict/surge` returns 0 | Log warning — may indicate threshold misconfiguration |
| Score anomaly | Any risk_score outside 50–200 range | Flag record in response, log warning |
| CDC API unreachable | `download_cdc_places.py` fails to connect | Log error, retain last good CSV, alert maintainer |

Planned monitoring tools:
- [UptimeRobot](https://uptimerobot.com/) — endpoint availability ping every 5 minutes
- Flask built-in logging — all requests and errors written to `mhcews.log`
- GitHub Actions — run functional tests on every push to main branch

---

## Continuous Testing & Maintenance

- Run `python test_api.py` after every code change (smoke test)
- Re-download CDC PLACES data annually when new release is published (typically October)
- Re-run `download_cdc_places.py` and verify ZIP count matches prior year ± 5%
- Review risk score thresholds annually against updated national averages
- Log all test failures with timestamp, endpoint, and error message
- Update this test plan whenever new endpoints are added or schema changes

---

## Quality Metrics

| Metric | Goal |
|--------|------|
| API uptime | 99% during active development |
| Response time p95 | < 500ms for all endpoints |
| Data completeness | All 4 MH measures present for every ZIP |
| Functional test pass rate | 100% before any deployment |
| Risk score accuracy | Matches formula to 2 decimal places |
| Zero 500 errors | No unhandled server errors in normal use |
| CDC data freshness | Updated within 90 days of each annual CDC release |

---

## Status Summary

| Area | Status |
|------|--------|
| Functional tests | ✅ Implemented via `test_api.py` (8 test cases) |
| Data quality checks | ✅ Validated on server start via load/enrich pipeline |
| Performance tests | ⚠️ Manual timing complete; Locust scripting planned |
| Alarms / monitoring | 🔜 UptimeRobot to be configured post-deployment |
| CI/CD integration | 🔜 GitHub Actions workflow planned |
| CDC data refresh | 🔜 Automated annual refresh script planned |
| Error logging | ✅ Flask built-in logging active |

---

## Data Source Reference

| Field | Value |
|-------|-------|
| Dataset | CDC PLACES: Local Data for Better Health, ZCTA Data 2024 Release |
| API endpoint | `https://data.cdc.gov/resource/qnzd-25i4.json` |
| Format | JSON via Socrata SODA API |
| Authentication | None required (public) |
| License | U.S. Government work (public domain) |
| Update frequency | Annual (typically October) |
| Geographic unit | ZIP Code Tabulation Area (ZCTA) |
| Coverage | 32,520 ZCTAs across all 50 U.S. states + DC |
