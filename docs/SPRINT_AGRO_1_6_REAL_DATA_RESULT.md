# SPRINT AGRO 1.6 — REAL DATA RESULT

## STATUS

**COMPLETE.** Official numeric series are ingested, classified, analysed, charted, and persisted.

`REAL EXTERNAL DATA → NORMALIZED NUMERIC OBSERVATIONS → SPECIALISTS → CROSS-SOURCE VALIDATION → CHIEF ANALYST → DEEP ANALYSIS → HISTORY → CHARTS → SOURCE LINEAGE`

HTTP 200 / UI render / catalog metadata is **not** treated as market data. CONNECTED requires a finite `normalized_value`. DEMO is labelled and excluded from production analysis. MANUAL DATA is labelled and never presented as an external feed.

No second AGRO app. Crypto / Legal / Beauty / Cafe unchanged. **AGRO 1.7 was not started.**

Live org: `org-agro-live-14`. Health: **`agro-1.6 ok`**. UI: http://127.0.0.1:5180/workspace/agro?view=analytics

## STOP CONDITION

| Step | Evidence |
|------|----------|
| 1. Provider refresh | `POST /providers/refresh-all` HTTP 200, 82s |
| 2. Actual numeric records | **128** numeric observations (EC 40, Eurostat 36, World Bank 45, NBU 2, Open-Meteo 12) |
| 3. Metadata vs real | **101** metadata (CKAN titles, HTML page signals, WASDE catalog). Catalog ≠ market series |
| 4. All analysts | Run `b736a32a-24db-4f0d-b5f5-ebf0e90e7f76` — ukraine, trade, price, weather, crop, global (+ risk empty, chief) |
| 5. Chief Analyst | WATCH, confidence **96** (formula, not hardcoded 10). Numeric series used; no invented direction |
| 6. NEW operational analysis | `62ef3a22-824a-4830-9c3e-cd57134c4e08` economic_data=true, metadata_only=false |
| 7. NEW evening analysis | `9c5ac8cb-6380-450e-8df7-a0c9a3a0644e` |
| 8. Open detailed analysis | `GET /analytics/9c5ac8cb-…` HTTP 200, sections + lineage |
| 9. Charts | Dashboard/analysis `series`: price 24, production 24, yield_or_area 11, trade 12, fx 2, weather 12. UI sparklines `agro-analytics-charts` |
| 10. Source lineage | 12 providers on the analysis payload with record ids/URLs |

Persistence after `reset_agro_ops_for_tests()` + rehydrate: numeric 128, operational yes, evening yes, series intact.

## PROVIDERS ATTEMPTED

| Provider | Result | Why |
|----------|--------|-----|
| EC Agri-food cereals API | **CONNECTED** | JSON prices after redirect to `api.tech.ec.europa.eu`. 40 numeric EUR/t rows (FR, last ~10 weeks) |
| Eurostat SDMX `tag00047` | **CONNECTED** | Wheat/spelt area–production–humidity JSON. 36 numeric points |
| FAOSTAT QCL (Ukraine wheat) | **FAILED** | HTTP **521** (Cloudflare origin down / timeout). No synthetic FAO row |
| USDA WASDE structured | **PARTIAL** + FAS **NEEDS_KEY** | Cornell/ESMIS JSON 404; HTML/catalog only. `USDA_FAS_API_KEY` not set. No invented balances |
| NBU FX | **CONNECTED** | Official `NBUStatService` JSON. USD/UAH **44.6938**, EUR/UAH present (18.08.2026) |
| Open-Meteo Kyiv | **CONNECTED** | Daily Tmax + precipitation, 7-day forecast. 12 numeric points |
| World Bank WDI Ukraine | **CONNECTED** | Cereal production, yield, area, merchandise exports. 45 numeric points |
| data.gov.ua customs / Gosstat | **PARTIAL** | CKAN package **titles**, not tonnes |
| Ukrhydromet / ports / AMIS | **PARTIAL** | Official HTML titles/headings only (no scrape of JS/reCAPTCHA) |
| Minagro | **BLOCKED** | HTTP 403 |
| Licensed quotes + backup weather | **NEEDS_KEY** | Empty URL / no commercial key. Not faked |

### Counts

- Attempted (refresh loop): 13 fetchable specs (+ 3 slots not fetched: licensed quotes, backup weather, manual)
- Connected (numeric): **5** — `ec_agri`, `eurostat`, `world_bank`, `fx_rates`, `weather_provider`
- Partial (metadata/page): **6** — customs, gosstat, hydromet, USDA, ports, AMIS
- Blocked: **1** — Minagro
- Failed: **1** — FAOSTAT 521
- Needs key: **2** displayed — `market_prices`, `weather_provider_secondary` (+ USDA FAS note)

## NUMERIC vs METADATA

| Class | Count (live org after refresh) |
|-------|--------------------------------|
| Numeric observations | **128** |
| Metadata observations | **101** |
| Total normalized (non-raw) | **229** |

CONNECTED is issued only when `normalized_value` is a finite float. CKAN titles stay PARTIAL, `market_usable=false`.

## REQUIRED REAL SERIES (acceptance)

| Series | Present | Source | Sample |
|--------|---------|--------|--------|
| Commodity price | **YES** | EC Agri-food cereal prices | Durum/soft wheat FR, e.g. **220.03 EUR/t** (2026-08-03) |
| Production | **YES** | World Bank `AG.PRD.CREL.MT` + Eurostat tag00047 | Ukraine cereals **55 651 880 t (2024)** |
| Yield or area | **YES** | World Bank `AG.YLD.CREL.KG` / `AG.LND.CREL.HA` | Ukraine yield **5 147.7 kg/ha (2024)** |
| Trade | **YES** | World Bank `TX.VAL.MRCH.CD.WT` | Ukraine merchandise exports **40.37 bn USD (2025)** |
| FX | **YES** | NBU official | **USD/UAH 44.6938** |
| Weather | **YES** | Open-Meteo Kyiv | Tmax series through 2026-08-23, e.g. **26.3 °C** |

Ukraine customs still has **no numeric export tonnes** (CKAN catalog only). Trade acceptance is met via World Bank merchandise exports, labelled as such — not as grain-export tonnes.

## IMPOSSIBLE / HONEST GAPS

- **FAOSTAT production/prices:** public data API returned HTTP 521. No invented FAO tonnes or producer prices.
- **USDA WASDE balances:** public JSON catalog 404; FAS Open Data requires `USDA_FAS_API_KEY`. No invented WASDE tables.
- **Licensed CBOT/Euronext quotes:** NEEDS_KEY. EC cereal prices are official EU weekly averages, not exchange ticks.
- **Ukrhydromet observations:** official site is JS/reCAPTCHA; not scraped. Open-Meteo is the numeric weather series, labelled Open-Meteo, not Hydromet.
- **Logistics tariffs:** still internal ADOS only; section INSUFFICIENT without trip costs.
- **DEMO:** never mixed into production analysis.

## ANALYTICS SECTIONS (live evening)

Украина **DATA** · Цены **DATA** · Урожай **DATA** · Экспорт **DATA** · Погода **DATA** · Логистика **INSUFFICIENT** · Мировые рынки **DATA** · Риски (alerts/internal) · Возможности (empty unless internal) · Data gaps listed.

## SPECIALISTS

Executed: ukraine, trade, price, weather, crop, global, risk, chief.

With findings: ukraine, trade, price, weather, crop, global.

Risk agent: no internal overdue/expiry in this org (honest empty). Weather HIGH and production/price moves go to **Notifications** (see alerts).

## CHIEF ANALYST

- Bias: **WATCH**
- Confidence: **96**
- Quality: numeric coverage present; metadata not used as price direction
- Note: numeric official series + explicit MANUAL DATA only; DEMO excluded; HTML not analysed; tonnes/prices not invented

## ALERTS → EXISTING NOTIFICATIONS

`evaluate_alerts` now also reads numeric series (not only manual `market_price`).

Live notifications include:

- Price drop: MAI\|FEED FR **−5.6%**
- Production/yield changes (World Bank Ukraine cereals/yield)
- Weather risk HIGH (Open-Meteo day with Tmax ≥ 35 °C; precip row may carry the same day flag)

Cooldown 24h. Existing in-app notification channel reused.

## MANUAL DATA

Managers can enter: local price, buyer bid, seller offer, freight, warehouse, contract (`price_kind`). UI badge **MANUAL DATA**. `data_class=manual`. Never `AUTOMATIC`. DEMO rows are named DEMO and stripped from `run_analysis` / `run_agents`.

## SOURCE MANAGEMENT UI

Columns: Источник, Категория, Статус, Тип данных, Market usable, Последнее обновление, Наблюдений, Свежесть, Ошибки.

Status set used: CONNECTED, PARTIAL, STALE, BLOCKED, NEEDS_KEY, FAILED (unprobed official remains NOT_CONFIGURED / REQUIRES_CONFIGURATION until first probe).

## ARCHITECTURAL DECISIONS

- Extend `services/agro_ops` (`series_parsers.py` + existing mixins). No new `platform_*` package, no Alembic revision.
- NBU uses the same official URL as `services/market_reference_connectors.fetch_nbu_usd_eur`; agro fetch goes through `http_safety` so RAW is stored.
- Open-Meteo fills the empty `weather_provider` slot (CC BY). Ukrhydromet stays official-page PARTIAL. Licensed backup stays NEEDS_KEY.
- World Bank extra_urls (production + yield + area + merchandise exports) — one provider, four official indicator APIs, fail-soft per URL.
- CONNECTED ⇔ numeric parse. Catalog JSON without numbers = PARTIAL, `market_usable=false`.
- AnalysisRun still in the report JSONB bag (`record_type=analysis_run`). Charts consume `series` on dashboard/analysis — no fake interpolation.

Rejected: scraping meteo.gov.ua; fabricating FAO/USDA numbers after 521/404; treating CKAN titles as trade tonnes.

## TESTS

Backend: `tests/test_sprint_agro_1_6.py` plus 1.0–1.5 health bump to `agro-1.6`. **41 passed** (production 1.0 … 1.6).

Frontend: `src/web/workspace/agro/sprint_agro_1_6.test.tsx` (columns, charts, MANUAL DATA). `vitest run workspace/agro` green.

Catalog-only CKAN is now PARTIAL in 1.1/1.3/1.4 assertions (honesty, not a coverage cut).

## PRIORITY LEFT FOR LATER (not this sprint)

P1: AMIS / FAO price intelligence / COMEXT / oilseeds / Black Sea events — still page/PARTIAL; do not stall 1.6.

P2: licensed market adapters, freight providers, extra news — NEEDS_KEY.

**STOP. AGRO 1.7 not started.**
