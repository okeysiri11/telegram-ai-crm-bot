# SPRINT AGRO 1.4 — RESULT

## STATUS

**COMPLETE.** End-to-end intelligence pipeline executed on live services:

**REAL SOURCE → FETCH → RAW STORE → PARSER → NORMALIZED OBSERVATION → DATABASE → ANALYST → REPORT → HISTORY → RE-OPEN.**

Minimum (2 independent real external providers) **exceeded**. Target (3–4) met: Customs **CONNECTED** plus Ukrhydromet / FAO / EU / AMIS **PARTIAL** with stored records. Also CONNECTED: Gosstat CKAN, Eurostat catalogue, World Bank sources.

No second AGRO application. Crypto, Legal, Beauty, and Cafe were not changed. Prices, harvest tonnes, weather series, and trade volumes were never fabricated. **AGRO 1.5 was not started.**

## STOP CONDITION

| Required | Evidence |
|----------|----------|
| Real source fetch | Live HTTP probes 2026-08-17 ~07:22 UTC (`POST /providers/refresh-all`, org `org-agro-live-14`) |
| Normalization + DB | 61 observations: trade 20, crop 20, market 19, price 1, weather 1; 23 raw payloads (hash-deduped) |
| Analyst pipeline | Stored run **`3fbcd556-c0c6-423e-94a1-ec7a899f98d0`** (8 specialists) |
| Persisted report | **`8026fbd2-70cf-474b-9d82-dc347e7886c9`** type `MORNING_ON_DEMAND` |
| History + reopen | `GET /reports/{id}` HTTP 200 after API still running; singleton reset + rehydrate found the same IDs |
| ≥2 CONNECTED/PARTIAL with records | Customs CONNECTED 12; Ukrhydromet PARTIAL 1; FAO PARTIAL 1; EU PARTIAL 6; AMIS PARTIAL 1 |

## PIPELINE (what shipped)

Internet provider → **RAW DATA** (`kind=provider_raw`, hash dedupe, file ref for large bodies) → Parser → **Normalized observation** (analysts never see raw HTML) → Database (`agro_ops_records`) → Analyst outputs (`kind=analyst_output` with input trace) → **AgroReviewRun** (`kind=report`) → История обзоров.

Canonical types (mapped onto existing observation kinds):

| Canonical | Stored `record_kind` |
|-----------|----------------------|
| AgroTradeObservation | `trade_observation` |
| AgroPriceObservation | `price_observation` |
| AgroWeatherObservation | `weather_observation` |
| AgroProductionObservation | `crop_observation` |
| AgroGlobalMarketObservation | `market_observation` |
| AgroIntelligenceItem | `intel_item` |

HTML pages become `page_signal` rows (title / h1–h3 only). Provider stays **PARTIAL**, not CONNECTED.

## HTTP SAFETY

`services/agro_ops/http_safety.py`: 18s timeout, max 3 redirects, 400k size cap, User-Agent `ADOS-AgroOps/1.4`, 429/5xx retry+backoff, SSRF (`url_is_safe`), HTTPS preference. No Google/Bing snippets. No aggressive crawl.

**Live bug fixed:** `resp.content.read(MAX_BYTES+1)` truncated CKAN JSON mid-`\uXXXX` escape → empty parse → PARTIAL. Switched to `await resp.text(errors="replace")` then slice. After restart: Customs **CONNECTED 12**, Gosstat **CONNECTED 11**.

## UI (`/workspace/agro` → Агро-разведка)

Provider table columns: Источник, Категория, Статус, Последнее обновление, **Записей**, Следующая проверка, Что получает система, Действия.

Actions: [Проверить] [Последние данные] [Открыть источник] [Настройки].

Buttons: Обновить все, Запустить аналитиков, Утренний / Вечерний обзор (latest or «Сформировать сейчас»), Недельный прогноз / Перспектива 1–2 месяца (honest limitation if history insufficient). **История обзоров** opens stored reports. [Источники] on conclusions.

## SCHEDULER (Europe/Kyiv, idempotent `job_key`)

| Job | Kyiv | Cron UTC | Next from 2026-08-17 07:24 UTC |
|-----|------|----------|--------------------------------|
| `agro.providers.morning` | 07:30 | `30 4 * * *` | **2026-08-18 04:30 UTC** (07:30 Kyiv) |
| `agro.review.morning` | 08:00 | `0 5 * * *` | **2026-08-18 05:00 UTC** (08:00 Kyiv) |
| `agro.providers.evening` | 18:30 | `30 15 * * *` | **2026-08-17 15:30 UTC** (18:30 Kyiv) |
| `agro.review.evening` | 19:00 | `0 16 * * *` | **2026-08-17 16:00 UTC** (19:00 Kyiv) |

Old `agro.intel.*` / `agro.providers.daily` kept. Jobs are not duplicated on restart (`ensure_default_jobs` by `job_key`).

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops` only.** No new vertical, no new Alembic revision. Same JSONB `agro_ops_records`.
- **Analysts consume normalized observations only.** Raw HTML is stored and hashed, never fed to specialists.
- **Chief confidence is calculated** (coverage, freshness, provider quality, agreement, missing categories). Not hardcoded 10. This run: **96** = source-coverage of catalogs/pages, **not** a price-forecast certainty. Report confidence **73**.
- **Fail-soft ingest:** one provider exception does not abort the rest. Minagro Cloudflare 403 → BLOCKED; review still generated with that gap listed.
- **Weekly / 1–2 month outlook:** if history insufficient (`<7` distinct dates and `<40` obs) → honest «Недостаточно накопленных данных…». No invented prediction.

## PERSISTENCE

Table `agro_ops_records` (migration `i8d901234567`). Report fields: `report_type`, `confidence`, `providers_json`, `data_gaps_json`, `analyst_runs`, `sections_json`, `period_start`/`end`.

After `reset_agro_ops_for_tests()` + rehydrate:

- report `8026fbd2-70cf-474b-9d82-dc347e7886c9` found
- agents `3fbcd556-c0c6-423e-94a1-ec7a899f98d0` found
- observations still present

Live `GET /api/agro-ops/v1/reports/8026fbd2-70cf-474b-9d82-dc347e7886c9` → HTTP 200.

## LOCAL START / STOP

```bash
.venv/bin/python scripts/run_api_local.py          # http://127.0.0.1:8080
cd src/web && npm run dev                          # http://127.0.0.1:5180
```

Health: http://127.0.0.1:8080/api/agro-ops/v1/health — sprint **`agro-1.4`**.

UI: http://127.0.0.1:5180/workspace/agro?view=intel

---

## PROVIDERS

Live refresh 2026-08-17, org `org-agro-live-14`.

### CUSTOMS_UA (`ua_customs_open_data`)

- status: **CONNECTED**
- HTTP: **200**
- records: **12**
- data: CKAN dataset titles from data.gov.ua (`package_search?q=митниця&rows=12`). Catalog metadata, **not** export/import volumes.
- last success: **2026-08-17T07:22:27Z** (10:22 Europe/Kyiv)

### UKRHYDROMET_UA (`ua_hydromet`)

- status: **PARTIAL**
- HTTP: **200**
- records: **1**
- data: Official page title only (`meteo.gov.ua`). No structured agromet table (no scrape; site has reCAPTCHA in HTML).
- last success: **2026-08-17T07:22:28Z**

### FAO_GLOBAL (`fao`)

- status: **PARTIAL**
- HTTP: primary FAOSTAT API **timed out**; fallback FAOSTAT page **200**
- records: **1**
- data: Page title «FAOSTAT». Price series not parsed — no invented prices.
- last success: **2026-08-17T07:23:27Z**

### EU_CROPS (`ec_agri`)

- status: **PARTIAL**
- HTTP: **200**
- records: **6**
- data: HTML headings from Agri-food data portal (e.g. page title / section labels). Weekly cereal prices **not** parsed.
- last success: **2026-08-17T07:23:27Z**

### AMIS_GLOBAL (`amis`)

- status: **PARTIAL**
- HTTP: **200**
- records: **1**
- data: Portal title «AMIS Agricultural Market Information System». No structured outlook rows (JS-heavy portal; no scrape).
- last success: **2026-08-17T07:23:33Z**

Also this run (not in the five-name block): `ua_stat` CONNECTED 11; `eurostat` CONNECTED 1; `world_bank` CONNECTED 12; `ua_agro_ministry` **BLOCKED** HTTP 403 Cloudflare; licensed weather/FX/prices **REQUIRES_CONFIGURATION**.

## ANALYSTS

- run ID: **`3fbcd556-c0c6-423e-94a1-ec7a899f98d0`**
- specialists executed: Ukraine, Trade, Price, Weather, Crop, Global Markets, Risk, Chief Agro Analyst
- chief conclusion: **WATCH**
- confidence: **96** (calculated from source coverage / freshness / quality / agreement / missing categories; **not** hardcoded 10; reflects catalog/page coverage, not a market-price forecast)

Each specialist stored `input_provider_ids`, `input_record_ids`, `started_at`, `finished_at`, `conclusion`, `confidence`, `data_gaps`. Chief gap: Minagro blocked.

## REPORT

- report ID: **`8026fbd2-70cf-474b-9d82-dc347e7886c9`**
- type: **MORNING_ON_DEMAND**
- generated: **2026-08-17T10:23:34+03:00** (Europe/Kyiv)
- sources used: 10 — `amis`, `ec_agri`, `eurostat`, `fao`, `ua_customs_open_data`, `ua_hydromet`, `ua_ports`, `ua_stat`, `usda_wasde`, `world_bank`
- confidence: **73**
- observations: **61**
- data gaps: Минагрополитики Украины: доступ запрещён (Cloudflare 403)
- URL/page to open:
  - UI: http://127.0.0.1:5180/workspace/agro?view=intel → История обзоров → Открыть
  - API: `GET /api/agro-ops/v1/reports/8026fbd2-70cf-474b-9d82-dc347e7886c9` (headers `X-Organization-Id: org-agro-live-14`, `X-Role: agro_director`)

## SCHEDULER

- morning: `agro.providers.morning` 07:30 Kyiv → next **2026-08-18 07:30 Kyiv**; `agro.review.morning` 08:00 Kyiv → next **2026-08-18 08:00 Kyiv**
- evening: `agro.providers.evening` 18:30 Kyiv → next **2026-08-17 18:30 Kyiv**; `agro.review.evening` 19:00 Kyiv → next **2026-08-17 19:00 Kyiv**
- next runs: as table above (UTC 04:30 / 05:00 next day; 15:30 / 16:00 today)

## TESTS

- backend: **34 passed** (`tests/test_sprint_agro_production_1_0.py` … `tests/test_sprint_agro_1_4.py`) — provider health, fetch success/fail, parse, normalize, dedupe, raw persistence, analyst inputs, report generation/persistence/history, scheduler jobs, partial outage, tenant isolation
- frontend: **23 passed** (`src/web` `workspace/agro`) — source table, latest-data drawer, run analysts, morning generate/open, history reopen
- smoke: health `agro-1.4`; live `POST /providers/refresh-all`; `POST /agents/run`; `GET /reports/8026fbd2-…` HTTP 200 after rehydrate

## NOT STARTED

**AGRO 1.5.** Structured WASDE XML/CSV, FAOSTAT time series, EU weekly prices, Ukrhydromet agromet tables, and licensed weather/FX remain blocked on official machine-readable access or a contract. They are not stubbed with fake values.

**STOP AFTER SPRINT AGRO 1.4.**
