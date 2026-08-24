# SPRINT AGRO OPERATIONS 1.1 — RESULT

## STATUS

**COMPLETE** as an operational expansion of the existing AGRO vertical.

No second AGRO application was created. Crypto, Legal, Beauty, and Cafe were not changed except the shared cabinet shell: a section with **no columns** no longer renders a generic empty table (panel-owned screens).

Real data only. Prices, harvest, weather, trade volumes, companies, vehicles, and warehouses are never fabricated. `CONNECTED` is set only after a successful retrieval/parse.

## AUDIT (before this sprint)

| Screen | Finding |
|--------|---------|
| Агро-разведка → Источники | Catalog listed; almost all «Требуется подключение источника» because 1.0 never probed |
| Логистика | Empty generic table |
| Цены и рынки | Empty generic table |
| Склады | Entity existed; no inventory operations, lots, or valuation |

## DONE

### Providers

- Provider architecture: `provider_id`, name, category, country/region, source_type, official, connection_status, last_success_at, last_attempt_at, next_check_at, freshness, error, url, license notes, priority
- Statuses: `CONNECTED` / `DEGRADED` / `STALE` / `NOT_CONFIGURED` / `UNAVAILABLE` / `ERROR`
- Probe results for reporting: `CONNECTED` / `PARTIAL` / `NOT_CONFIGURED` / `BLOCKED` / `UNAVAILABLE`
- Health UI: Агро-разведка → Источники (Источник / Категория / Статус / Последнее обновление / Следующая проверка / Что получает / [Проверить сейчас])
- GET `/providers` without probe stays `NOT_CONFIGURED` (1.0 honesty preserved)
- Ingestion entities: `AgroMarketObservation`, `AgroTradeObservation`, `AgroWeatherObservation`, `AgroCropObservation`, `AgroPriceObservation`, `AgroProviderSnapshot` (JSONB kinds + fingerprint dedupe)
- Scheduler (existing engine): `agro.providers.daily`, `agro.providers.weather`, `agro.providers.markets`
- Retry / timeout / backoff via aiohttp timeout 18s; licensed slots stay `NOT_CONFIGURED`

### Logistics

Operational registry: Обзор, Перевозчики, Автомобили, Прицепы, Водители, Рейсы, Маршруты, Документы, Расходы, История.

Entities: `AgroCarrier` (link to existing counterparty), `AgroVehicle`, `AgroTrailer`, `AgroDriver`, `AgroTrip`.

Trip economics: total cost, per tonne, per km. Dashboard cards: active trips, vehicles in trip, free vehicles, loadings/unloadings today, overdue, cost today/month.

Trip → shipment → deal → warehouse. Delivered trip does **not** change inventory. Explicit: [Принять на склад] / [Подтвердить расход].

### Markets

Subsections: Обзор рынка, Мои рынки, Котировки, Прайс-листы, История цен, Сравнение, Импорт/Экспорт, Настройки.

`AgroMarket` + `AgroMarketPrice`. Manual prices always work; history never overwrites. Source badges: АВТО / РУЧНАЯ / КОНТРАГЕНТ / ДОГОВОР.

History spans 7D / 30D / 3M / 6M / 1Y — only real observations (dated list, no synthetic series).

Landed cost: purchase + storage + transport + other → delivered cost → margin; [Создать расчёт] opens existing Расчёты.

### Warehouses

Subsections: Обзор, Склады, Остатки, Приход, Расход, Перемещения, Партии, Инвентаризация, Документы, История.

`AgroWarehouse`, `AgroStorageUnit` (architecture-ready), `AgroInventoryLot`, `AgroWarehouseOperation` (RECEIPT / ISSUE / TRANSFER / ADJUSTMENT / INVENTORY_CORRECTION).

Negative inventory blocked unless director + `allow_negative`. Transfer = linked ISSUE + RECEIPT. Market valuation is analytical only.

### UI

- Operational empty CTAs (not «Пока нет записей»)
- Right-side drawers with Обзор / Документы / История / Архивировать
- Paperclip 📎 on vehicles, trailers, drivers, carriers, trips, warehouses, lots, markets, prices
- Sensitive docs (`driver_license`, `passport`, `id_document`, `medical`): director / platform_owner only
- Search / filters / sort / pagination remain on table-backed sections; panel-owned modules use their own lists

## PROVIDER PROBE REPORT (live, 2026-08-16)

Attempted official retrieval. `CONNECTED` only if data was actually retrieved/parsed.

| Provider | Result | Reason |
|----------|--------|--------|
| Ukraine Customs (`data.gov.ua` CKAN) | **CONNECTED** | HTTP 200, 8 published dataset titles ingested (catalog metadata, not invented volumes) |
| Ukraine Statistics (`data.gov.ua` CKAN) | **CONNECTED** | HTTP 200, 8 published dataset titles |
| Ukrhydromet (`meteo.gov.ua`) | **PARTIAL** | Official page reachable; no structured agromet table parsed |
| WeatherProviderSecondary | **NOT_CONFIGURED** | Reserved slot; legal secondary provider not selected |
| USDA WASDE | **PARTIAL** | Cornell JSON HTTP 404. Official USDA WASDE page HTTP 200; structured XML/CSV balances not parsed — no invented stocks |
| FAO / FAOSTAT | **PARTIAL** | FAOSTAT API unreachable (HTTP 0). Official FAOSTAT page HTTP 200; price series not parsed — no invented prices |
| European Commission Agri-food portal | **PARTIAL** | Official page HTTP 200; structured weekly prices not parsed |
| Eurostat catalogue | **CONNECTED** | HTTP 200, catalogue reachable (1 catalog observation, not invented prices) |
| Minagro | **BLOCKED** | HTTP 403 |
| UA ports | **PARTIAL** | Official page reachable; no structured series |
| AMIS | **PARTIAL** | Official page reachable; no structured series |
| World Bank Open Data | **CONNECTED** | HTTP 200, 12 source catalog rows |
| Licensed market prices | **NOT_CONFIGURED** | No commercial key |
| FX rates | **NOT_CONFIGURED** | Manual FX in calculations until official feed |
| Licensed weather API | **NOT_CONFIGURED** | Not selected |
| Manual import | **CONNECTED** | Operator-entered; always available |

CKAN / World Bank / Eurostat observations are **published catalog titles**, not fabricated export tonnes or prices.

## PARTIAL / DEFERRED

- WASDE XML/CSV commodity balances (production/imports/exports/stocks) — Cornell machine-readable catalog 404; no silent fake balances
- FAOSTAT price series — API unreachable here; no silent fallback numbers
- EC weekly cereal price tables — HTML portal only
- Hydromet structured precipitation/soil — official page adapter only, no aggressive scrape
- Price history is a dated observation list (real points only), not a canvas chart
- Filter persistence per user — uses existing cabinet table controls where a table exists
- Map / GIS / satellite — out of scope (same as 1.0)

## DATABASE / MIGRATIONS

Existing only: `migrations/versions/i8d901234567_agro_ops_1_0.py` → `agro_ops_records`.

No new migration. New kinds live in the same JSONB registry.

## ENDPOINTS (additive on `/api/agro-ops/v1`)

- `POST /providers/{id}/probe` `POST /providers/ingest` `GET /providers/observations`
- `GET /logistics/dashboard`
- `GET /markets/dashboard` `GET /markets/history` `POST /markets/compare` `POST /markets/landed-cost`
- `GET /warehouses/dashboard` `POST /warehouses/operations` `POST /warehouses/receive` `POST /warehouses/issue`
- Aliases: `/carriers` `/vehicles` `/trailers` `/drivers` `/trips` `/market-prices` `/lots` `/warehouse-operations`

## SCHEDULER JOBS

| Job | Cron (UTC) | Policy |
|-----|------------|--------|
| `agro.intel.morning` | `0 5 * * *` | 1.0 reports |
| `agro.intel.evening` | `0 15 * * *` | 1.0 reports |
| `agro.providers.daily` | `0 6 * * *` | customs / stat / WASDE check |
| `agro.providers.weather` | `0 4,10,16 * * *` | hydromet page check |
| `agro.providers.markets` | `0 5,15 * * *` | prices / EU / trade cadence |

Ingest is idempotent by fingerprint. WASDE is checked daily; a new observation is stored only when the published reference changes.

## SCENARIO 34

Covered by backend tests (same graph, no fabricated market data):

1–6. Counterparty «ООО Тест Агро» (supplier+carrier), vehicle AA0001AA, trailer, driver, sensitive license attachment (RBAC)
7–10. Warehouse «Одесский склад» 1000 t; market «Одесса — ручной рынок»; manual wheat price; history kept
11–17. Wheat deal 100 t; trip; receipt 100 t; issue 20 t → balance 80 t; deal↔trip related
18–19. Price history two points; landed cost uses market + transport and can open Расчёты
20–21. Persistence is the existing `agro_ops_records` store (survives process restart when Postgres is up)

## TESTS

- Backend `tests/test_sprint_agro_operations_1_1.py` + `tests/test_sprint_agro_production_1_0.py`
- Frontend `workspace/agro/sprint_agro_operations_1_1.test.tsx` + `sprint_agro_production_1_0.test.tsx`
- Health sprint id: **`agro-1.1`**

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops`** with mixins (`Provider`, `Logistics`, `Markets`, `Warehouse`) instead of a new vertical.
- **Same JSONB registry** — no parallel typed tables for 1.1.
- **Probe-only CONNECTED** — listing providers never implies a live feed.
- **No silent inventory** on trip DELIVERED.
- **Sensitive driver/ID docs** restricted to director / owner.
- **Cabinet shell**: empty-column sections are panel-owned (avoids duplicate «Пока нет записей»).

## LOCAL START / STOP

```bash
.venv/bin/python scripts/run_api_local.py          # http://127.0.0.1:8080
cd src/web && npm run dev                          # http://127.0.0.1:5180
```

Health: http://127.0.0.1:8080/api/agro-ops/v1/health

## NEXT RECOMMENDED SPRINT

**AGRO 1.2** — structured WASDE XML/CSV parse when a stable official file URL is available; FAOSTAT series when the API is reachable; licensed weather/FX if a contract exists. Do not invent series in the meantime.

STOP AFTER AGRO OPERATIONS 1.1.
