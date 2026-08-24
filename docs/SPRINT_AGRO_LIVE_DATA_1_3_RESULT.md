# SPRINT AGRO LIVE DATA 1.3 — RESULT

## STATUS

**COMPLETE.** Live provider health checks, ingestion, analyst pipeline, and a persisted Evening Review were executed. No next sprint started.

No second AGRO application. Crypto, Legal, Beauty, and Cafe were not changed. Prices, harvest tonnes, weather series, and trade volumes were never fabricated.

## STOP CONDITION

| Required | Evidence |
|----------|----------|
| Real provider health checks executed | Live HTTP probes on 2026-08-16 (see table below) |
| Real ingestion attempted | `refresh_all_providers` / `POST /providers/refresh-all` for org `org-agro-live-13` |
| Available providers ingested | 29 normalized observations stored (CKAN titles, Eurostat catalogue, World Bank sources) |
| Analyst pipeline executed | Stored `agents_run` **`1d17dfa0-7858-432d-b307-658a604c2253`** |
| At least one review generated | Evening Review **`db61b7f1-2f96-4986-a89b-4c491c2d2991`** |
| Restart: review + observations remain | After singleton reset + rehydrate: review yes, agents yes, **29** observations |

## DONE

- Health alias layer: `CONNECTED` / `PARTIAL` / `REQUIRES_CONFIGURATION` / `BLOCKED` / `FAILED`
- GET `/providers` without probe stays unprobed (`NOT_CONFIGURED` → UI `REQUIRES_CONFIGURATION`) — 1.0 honesty preserved
- `POST /providers/refresh-all`, `GET /providers/{id}` (source drawer: URL, adapter, raw observations)
- Normalize + fingerprint dedupe; raw excerpt on snapshots (first 2000 chars)
- 429 / timeout / 5xx / 401–403 mapped honestly (unit-tested)
- «Запустить аналитиков» persists `record_type=agents_run`
- Morning / Evening reviews persist and cite `provider_id`, `source_url`, `source_reference`, `published_at`, `ingested_at`
- UI: Обновить все, loading (`agro-intel-loading`), error (`agro-intel-error`), source drawer

## LIVE PROVIDER HEALTH (2026-08-16)

`CONNECTED` only after a real retrieval **and** structured parse. Catalog titles are ingested as-is — not invented prices or tonnes.

### CONNECTED

| Provider | Endpoint / source | Adapter | Records | Last fetch (UTC) | Limitations |
|----------|-------------------|---------|---------|------------------|-------------|
| `ua_customs_open_data` | `https://data.gov.ua/api/3/action/package_search?q=митниця&rows=8` HTTP 200 | `open_data_api` (CKAN) | 8 | 2026-08-16T12:47:35Z | Published **dataset titles** only, not export volumes |
| `ua_stat` | `https://data.gov.ua/api/3/action/package_search?q=сільське+господарство&rows=8` HTTP 200 | `open_data_api` (CKAN) | 8 | 2026-08-16T12:47:35Z | Catalog titles only, not harvest tonnes |
| `eurostat` | `https://ec.europa.eu/eurostat/api/dissemination/catalogue/toc/txt?lang=EN` HTTP 200 | `official_api` | 1 | 2026-08-16T12:47:58Z | Catalogue reachable; no price series parsed |
| `world_bank` | `https://api.worldbank.org/v2/sources?format=json` HTTP 200 | `official_api` | 12 | 2026-08-16T12:48:00Z | Source catalog names, not indicator time series |
| `manual_import` | Operator-entered / RSS | `manual` | 0 (this run) | — | Always available; no fake feed |

### PARTIAL

| Provider | Endpoint / source | Adapter | Records | Last fetch (UTC) | Limitations |
|----------|-------------------|---------|---------|------------------|-------------|
| `ua_hydromet` | `https://meteo.gov.ua/` HTTP 200 | `official_page` | 0 | 2026-08-16T12:47:36Z | Official page reachable; no structured agromet table (no scrape) |
| `usda_wasde` | Cornell JSON **HTTP 404**; fallback `https://www.usda.gov/.../wasde-report` HTTP 200 | `official_api` → page | 0 | 2026-08-16T12:47:37Z | No WASDE XML/CSV balances — no invented stocks |
| `fao` | FAOSTAT API **timeout**; fallback `https://www.fao.org/faostat/en/#data` HTTP 200 | `official_api` → page | 0 | 2026-08-16T12:47:56Z | Price series not parsed — no invented prices |
| `ec_agri` | `https://agridata.ec.europa.eu/extensions/DataPortal/agricultural_markets.html` HTTP 200 | `official_page` | 0 | 2026-08-16T12:47:56Z | HTML portal only; weekly cereal prices not parsed |
| `ua_ports` | `https://www.uspa.gov.ua/` HTTP 200 | `official_page` | 0 | 2026-08-16T12:47:59Z | Official page; no structured throughput series |
| `amis` | `https://www.amis-outlook.org/` HTTP 200 | `official_page` | 0 | 2026-08-16T12:48:00Z | Portal reachable; no structured outlook rows |

### REQUIRES_CONFIGURATION

| Provider | Endpoint / source | Adapter | Records | Last fetch | Why not automated |
|----------|-------------------|---------|---------|------------|-------------------|
| `weather_provider_secondary` | none | `licensed` | 0 | — | Reserved slot; legal secondary weather provider not selected |
| `market_prices` | none | `licensed` | 0 | — | Commercial quote feed; API key / license not configured |
| `fx_rates` | none | `licensed` | 0 | — | Official FX feed not configured; FX stays manual in calculations |
| `weather_provider` | none | `licensed` | 0 | — | Licensed weather API not selected |

### BLOCKED

| Provider | Endpoint / source | Adapter | Records | Last fetch (UTC) | Limitations |
|----------|-------------------|---------|---------|------------------|-------------|
| `ua_agro_ministry` | `https://minagro.gov.ua/` **HTTP 403** | `official_page` | 0 | attempt 2026-08-16T12:47:58Z | Access forbidden from this environment; no scrape of closed cabinets |

### FAILED

No live provider finished as **FAILED** on 2026-08-16 after fallbacks.

FAO primary URL timed out (`timeout:`, HTTP 0) — that attempt is a FAILED fetch; the official FAOSTAT page fallback made the **provider** PARTIAL.

FAILED is covered by backend tests: HTTP 429 (+ Retry-After), timeout, HTTP 500. Mapping: `probe_result=FAILED`, `health_state=FAILED`.

## GENERATED REVIEW

| Field | Value |
|-------|--------|
| Review ID | **`db61b7f1-2f96-4986-a89b-4c491c2d2991`** |
| Kind | `evening` — Вечерний обзор |
| Organization | `org-agro-live-13` |
| Observation count | 29 |
| Sources note | «…29 официальных наблюдений (названия/метаданные наборов). Цены, тонны и урожай не выдумываются.» |
| Agents run ID | **`1d17dfa0-7858-432d-b307-658a604c2253`** |

Trade section includes `ua_customs_open_data` bullets with `source_url` / `provider_id`.

## SCHEDULER (working jobs)

| Job | Cron (UTC) | Next run from live check (2026-08-16 12:48 UTC) |
|-----|------------|--------------------------------------------------|
| `agro.intel.morning` | `0 5 * * *` | **2026-08-17 05:00 UTC** (08:00 Europe/Kyiv) |
| `agro.intel.evening` | `0 15 * * *` | **2026-08-16 15:00 UTC** (18:00 Europe/Kyiv) |
| `agro.providers.daily` | `0 6 * * *` | 2026-08-17 06:00 UTC |
| `agro.providers.weather` | `0 4,10,16 * * *` | 2026-08-16 16:00 UTC |
| `agro.providers.markets` | `0 5,15 * * *` | 2026-08-16 15:00 UTC |
| `agro.alerts.evaluate` | `0 6,18 * * *` | 2026-08-16 18:00 UTC |
| `agro.calendar.reminders` | `0 5,11,17 * * *` | 2026-08-16 17:00 UTC |

Handlers already wired in `services/pg_scheduler_engine.py`.

## PERSISTENCE

Existing table `agro_ops_records` (migration `i8d901234567`). No new Alembic revision.

Local Postgres was missing VersionMixin columns (`change_id`, …) because `i8d` created the table after the 37.1 backfill (`u4o567890123`) had already run. Applied the **existing** 37.1 `ADD COLUMN IF NOT EXISTS` DDL to `agro_ops_records` so ORM inserts match the model.

After that: service singleton reset + rehydrate kept Evening Review `db61b7f1-2f96-4986-a89b-4c491c2d2991`, agents run `1d17dfa0-7858-432d-b307-658a604c2253`, and 29 observations.

## ENDPOINTS (additive on `/api/agro-ops/v1`)

- `POST /providers/refresh-all`
- `GET /providers/{provider_id}`
- `GET /agents` (stored runs); `POST /agents/run` still creates
- Existing: `POST /providers/{id}/probe`, `POST /providers/ingest`, `GET /providers/observations`, `POST /reports/generate`

Health sprint id: **`agro-1.3`**

## TESTS

Backend `tests/test_sprint_agro_live_data_1_3.py` (+ 1.0 / 1.1 / 1.2 health bump to `agro-1.3`):

provider health, fetch adapter, normalization, dedupe, raw persistence, scheduler sweep, review generation, source traceability, 429, timeout, provider failure, partial HTML, tenant isolation.

Frontend `src/web/workspace/agro/sprint_agro_live_data_1_3.test.tsx`:

provider health screen, refresh all, run analysts, morning review, evening review, source drawer, error states, loading states.

**Results:** backend 30 passed; frontend `workspace/agro` 18 passed.

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops`** (providers + intelligence mixins). No new vertical, no new table.
- **Reviews/analysts consume ingested observations only** (catalog titles / official page reachability). Never invent market numbers.
- **Health aliases** for the 1.3 UI; internal `connection_status` kept so 1.0 `NOT_CONFIGURED` listing tests stay green.
- **Same JSONB registry** for snapshots, observations, reports, `agents_run`.
- **No new migration.** Schema repair used the existing 37.1 VersionMixin DDL.

## LOCAL START / STOP

```bash
.venv/bin/python scripts/run_api_local.py          # http://127.0.0.1:8080
cd src/web && npm run dev                          # http://127.0.0.1:5180
```

Health: http://127.0.0.1:8080/api/agro-ops/v1/health

## NOT STARTED

AGRO 1.4 and later. Structured WASDE XML/CSV, FAOSTAT series, licensed weather/FX remain blocked on official machine-readable access or a contract — they are not stubbed with fake values.

**STOP AFTER AGRO LIVE DATA 1.3.**
