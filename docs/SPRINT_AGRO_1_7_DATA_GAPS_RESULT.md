# SPRINT AGRO 1.7 — DATA GAPS RESULT

## STATUS

**COMPLETE. STOP after AGRO 1.7.** AGRO 1.8 was not started.

Public sources are requested, parsed, normalized, stored, analysed, reported, and shown with source lineage. Demo data is never used as a silent substitute. Gaps that remain are license, API key, blocked access, or a public dataset that is actually down.

Live org: `org-agro-live-14`. Health: **`agro-1.7 ok`**. UI: http://127.0.0.1:5180/workspace/agro?view=intel

Coverage card (after `POST /providers/refresh-all`, 17 Aug 2026):

```
Источников подключено: 6
Реальных наблюдений: 248
Метаданных: 101
Данные за последние 24 часа: 14
Coverage:
100%
Confidence:
96%
Unresolved gaps:
6
```

No second AGRO app. Crypto / Legal / Beauty / Cafe unchanged.

---

## PIPELINE

`PUBLIC SOURCE → REQUEST → PARSE → NORMALIZE → STORE → ANALYZE → REPORT → HISTORY → SOURCE LINEAGE`

| Step | Evidence |
|------|----------|
| Request | `POST /api/agro-ops/v1/providers/refresh-all` HTTP 200, **20.1 s**, org `org-agro-live-14` |
| Parse / normalize | CONNECTED only when `normalized_value` is a finite float |
| Store | Generic JSONB `agro_ops_records` (no new Alembic revision) |
| Analyze | Operational run `99d8c425-512c-472b-aa66-19fec219570b` — economic_data=true, 200+ numeric, DEMO 9999 excluded |
| Report | New **morning** + **evening** after refresh: `sources_count=6`, 248 numeric observations |
| History | Latest morning/evening `2026-08-17T16:14:14Z` at top of `/reports` |
| Lineage | Chart points keep `source`, `source_url`, `series_id` |

---

## PROVIDER TABLE

| Provider | Attempted | Connected | Numeric observations | Metadata | Status | Reason | Needs key | Needs license |
|----------|-----------|-----------|----------------------|----------|--------|--------|-----------|---------------|
| `ec_agri` EC Agri-food cereals | yes | yes | 40 | 0 | **CONNECTED** | Official JSON EUR/t after redirect to `api.tech.ec.europa.eu` | no | no |
| `eurostat` SDMX `tag00047` | yes | yes | 36 | 0 | **CONNECTED** | Wheat/spelt area–production JSON | no | no |
| `fao` FAOSTAT / FAO FPI | yes | yes (FPI) | 48 | 0 | **CONNECTED** | Official FAO Food Price Index CSV (Cereals). Latest **113.8 (2026-07)** from worldfoodsituation library. QCL tonnes API still down | no | no |
| `world_bank` WDI Ukraine | yes | yes | 57 | 0 | **CONNECTED** | Production, yield, area, **merchandise exports + imports** (`TX.` / `TM.VAL.MRCH.CD.WT`) | no | no |
| `fx_rates` NBU | yes | yes | 2 | 0 | **CONNECTED** | Official `NBUStatService` JSON. USD/UAH **44.6938**, EUR/UAH **51.8082** (18.08.2026) | no | no |
| `weather_provider` Open-Meteo Kyiv | yes | yes | 12 | 0 | **CONNECTED** | Daily Tmax + precipitation. Freshness **менее часа**, not «нет данных» | no | no |
| `ua_customs_open_data` | yes | metadata only | 0 | CKAN titles | **PARTIAL** | data.gov.ua package titles, not grain tonnes | no | no |
| `ua_stat` Gosstat CKAN | yes | metadata only | 0 | CKAN titles | **PARTIAL** | Catalog titles, not statistical series | no | no |
| `ua_hydromet` | yes | metadata only | 0 | HTML titles | **PARTIAL** | Official page; JS/reCAPTCHA not scraped | no | no |
| `ua_ports` | yes | metadata only | 0 | HTML titles | **PARTIAL** | Portal headings only | no | no |
| `amis` | yes | metadata only | 0 | HTML titles | **PARTIAL** | AMIS Outlook HTML, no numeric extract | no | no |
| `usda_wasde` | yes | metadata only | 0 | catalog/HTML | **PARTIAL** | Cornell/ESMIS JSON 404. No invented balances | **USDA_FAS_API_KEY** | no (FAS key) |
| `ua_agro_ministry` Minagro | yes | no | 0 | 0 | **BLOCKED** | HTTP **403** | no | no |
| `market_prices` licensed quotes | skipped (empty URL) | no | 0 | 0 | **NEEDS_KEY** | Commercial feed not configured | yes | **yes** |
| `weather_provider_secondary` | skipped | no | 0 | 0 | **NEEDS_KEY** | Backup weather key not set | yes | no |
| `manual_import` | n/a | operator | 0 | 0 | **CONNECTED** | Manual / RSS only; not an external numeric feed | no | no |

FAOSTAT QCL JSON (`fenixservices.fao.org` timeout / HTTP 521, `www.fao.org/faostat/api` 404, bulk CSV 403) is **not** faked. Numeric FAO series is the official **Food Price Index (Cereals)** CSV from FAO worldfoodsituation, same FPI family published on FAOSTAT.

---

## ACCEPTANCE (manual, live)

After Agro → Агро-разведка → **Обновить все**:

| Check | Result |
|-------|--------|
| Open-Meteo does not show «нет данных» | **PASS** — freshness `Open-Meteo: менее часа` |
| ≥1 Eurostat numeric series | **PASS** — 36 points, `tag00047` |
| ≥1 FAOSTAT numeric series | **PASS** — FPI Cereals, latest **113.8 (2026-07)** |
| NBU FX exists | **PASS** — USD/UAH 44.6938, EUR/UAH 51.8082 |
| Export/import data exists | **PASS** — World Bank merchandise exports **40.37 bn USD (2025)** and imports **83.57 bn USD (2025)**. Customs still titles only |
| Morning/Evening no longer «0 источников» | **PASS** — `sources_count=6`, note cites 248 numeric observations |
| Analytics uses current source data | **PASS** — coverage 100% / confidence 96; charts include FAO, Eurostat, NBU, WB trade, Open-Meteo |
| History contains newly generated report | **PASS** — morning + evening `2026-08-17T16:14:14Z` |
| Gaps only where blocked/licensed/keyed | **PASS** — six unresolved gaps listed below |

---

## RESOLVED GAPS (this sprint)

- Open-Meteo freshness showed «нет данных» even with numeric weather — freshness now uses `last_success_at` **or** stored observations; CONNECTED + numeric never prints «нет данных».
- Morning/Evening `sources_count` counted metadata providers / stale 0-source reports — now counts **numeric** providers; refresh-all generates new morning+evening; stale 0-source latest is regenerated.
- Coverage card missing on Агро-разведка / Аналитика — card prints connected / numeric / metadata / 24h / Coverage% / Confidence% / Unresolved gaps.
- FAOSTAT had zero numeric rows (API 521) — official FAO FPI CSV connected (Cereals index). QCL **tonnes** remain a remaining gap.
- Trade was exports-only — World Bank **imports** `TM.VAL.MRCH.CD.WT` added.
- Demo could look like production data — «Загрузить демо AGRO» still exists; DEMO banner is mandatory; demo rows stay `[DEMO]` / `is_demo` and are excluded from analysis and reports. No silent demo fallback when real series are missing (INSUFFICIENT, not demo).

---

## REMAINING GAPS (honest)

1. **FAOSTAT QCL production tonnes (Ukraine wheat)** — `fenixservices.fao.org` timeout / HTTP 521; `www.fao.org/faostat/api` 404; fenix bulk CSV AccessDenied. Public JSON QCL is down. FPI index is **not** tonnes.
2. **USDA WASDE numeric balance** — Cornell/ESMIS JSON 404; FAS Open Data needs `USDA_FAS_API_KEY`.
3. **Licensed exchange quotes** (CBOT / Euronext ticks) — empty URL, `NEEDS_KEY` + license.
4. **Backup weather provider** — `NEEDS_KEY`.
5. **Minagro** — HTTP 403 blocked.
6. **Ukraine customs / Gosstat grain tonnes** — CKAN catalogs only; no numeric export/import tonnes from data.gov.ua in this sprint.
7. **Ukrhydromet official observations** — JS/reCAPTCHA; Open-Meteo is labelled Open-Meteo, not Hydromet.
8. **Logistics tariffs** — no priced trips in this org (internal INSUFFICIENT).

Annual World Bank / Eurostat / FPI points are **not** counted as “stale 24h feed failure”. 24h count (14) is NBU + Open-Meteo (and any other sub-daily series).

---

## REQUIRED CREDENTIALS

| Env / license | Why |
|---------------|-----|
| `USDA_FAS_API_KEY` | USDA FAS Open Data numeric WASDE / PSD |
| Licensed market-data contract + key | `market_prices` exchange ticks |
| Backup weather API key | `weather_provider_secondary` |

No key is required for Open-Meteo, NBU, Eurostat, EC Agri-food, World Bank WDI, or FAO FPI CSV.

---

## RECOMMENDED NEXT INTEGRATIONS (not started)

Do not treat these as AGRO 1.8 work in this sprint.

- FAOSTAT QCL when fenix origin recovers (keep current FPI).
- USDA FAS with a real key (WASDE tonnes).
- data.gov.ua `datastore_search` on a **published resource with numeric columns** for grain export tonnes (today’s package_search does not yield that).
- Licensed quotes only with a signed contract — never scrape.
- Ukrhydromet if they publish a public JSON/CSV without reCAPTCHA.

---

## NO DEMO FALLBACK

- Production analysis / reports / charts strip `is_demo` and `data_class=demo`.
- Button **«Загрузить демо AGRO»** remains. After click: settings `demo_loaded`, dashboard `demo_mode`, red **РЕЖИМ DEMO** banner. Titles stay `[DEMO]`.
- Missing real series → INSUFFICIENT / explicit gap. Demo is not substituted.

---

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops`** (providers, parsers, analytics, intelligence, desk). No new `platform_*` package, no second AGRO app, no new Alembic revision.
- **FAO numeric via official FPI CSV**, not World Bank rebranded as FAOSTAT, and not invented QCL tonnes.
- **Coverage %** = share of six required series present (price, production, yield/area, trade, fx, weather). **Confidence %** = last chief/analysis confidence when present, else coverage.
- **24h freshness** uses observation timestamps; annual series are not treated as a broken live feed.

Rejected: silent demo seed when public APIs fail; disguising WB cereal production as FAOSTAT QCL; scraping licensed or reCAPTCHA sites.

---

## TESTS

Backend: `tests/test_sprint_agro_1_7.py` plus 1.0–1.6 health bump to `agro-1.7`. **44 passed** (production 1.0 … 1.7).

Frontend: `src/web/workspace/agro/sprint_agro_1_7.test.tsx` + existing agro vitest. **31 passed**.

---

## STOP

AGRO 1.7 is complete. Unresolved dependencies are listed above and shown in the UI gaps list. **Do not start another sprint from this document.**
