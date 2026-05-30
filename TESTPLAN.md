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
