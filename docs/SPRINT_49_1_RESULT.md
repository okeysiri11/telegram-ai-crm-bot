# SPRINT 49.1 RESULT

Operational depth for Beauty / Cafe / Crypto OTC cabinets.

## 1. Implemented

- Beauty: create appointment, cancel, create client; GET list endpoints; persistence via BOS Hub store; filters/empty CTAs
- Cafe: create order with event `order_type`, open/close shifts; GET lists; COS persistence
- Crypto: chart provider boundary, instrument workspace + timeframes, «Мои анализы» config persistence, AI specialist shells, tenant-scoped watchlist
- Shared table UX: search, status/date/responsible filters, sort, pagination, honest empty states
- Role-aware nav caps via auth permissions + role switcher (no owner hardcode as sole gate)
- Sprint 48 antifraud preserved (regression re-run)

## 2. Beauty operational flows

1. Bootstrap / load lists (customers, services, employees, appointments, branches)
2. «+ Новая запись» → form → `POST /api/enterprise-bos/v1/appointments`
3. Reload → appointment in table
4. «Отменить» → transition `cancelled`
5. «+ Клиент» → `POST /customers`

## 3. Cafe operational flows

1. Bootstrap lists (menu, tables, customers, staff, orders, shifts)
2. «+ Новый заказ» with types (Банкет, Караоке, …) → `POST /orders` with `order_type`
3. «Открыть смену» / «Закрыть» → `POST /shifts`
4. Orders/shifts appear after refresh

## 4. Crypto OTC operational flows

1. Watchlist add/remove (localStorage, tenant-scoped key)
2. Charts: symbol + 1m…1W + provider status (Null / Crypto-TA bridge)
3. «Мои анализы»: instruments, markets/regions, morning/evening/pre-trade, news/TA flags — persisted; no fake scheduled delivery
4. AI specialists: configure / «Запустить анализ» records request without claiming live model run
5. Payout confirm link → existing `/crypto-otc/payout/:dealId` (Sprint 48)

## 5. Persistence added/reused

| Data | Store |
|------|--------|
| Beauty entities | Hub in-memory `bos_*` (process lifetime) |
| Cafe entities + shifts | Hub in-memory `cos_*` + new `cos_shifts` |
| OTC watchlist / analyses / specialists | `localStorage` (`ados_otc_*_v49/v491`, optional `::tenantId`) |
| Crypto payout registry | Postgres (unchanged Sprint 48) |

No Postgres migrations this sprint for BOS/COS.

## 6. APIs/routes used

**Beauty OS** `/api/enterprise-bos/v1`:
- GET/POST `customers`, `services`, `employees`, `appointments`
- GET `branches`, `dashboard`
- POST `bootstrap`

**Cafe OS** `/api/enterprise-cos/v1`:
- GET/POST `orders`, `staff`, `customers`, `reservations`, `shifts`
- GET/POST `menu`, `tables`
- GET `dashboard`
- POST `bootstrap`

**Crypto:** `/api/crypto-enterprise/v1` markets/portfolio/dashboard; `/api/crypto-ta/v1` optional chart bridge; `/management/v1/crypto-tx` antifraud.

## 7. Database migrations

None.

## 8. Tests

| Suite | Result |
|-------|--------|
| `tests/test_sprint_49_1_ops_cabinets.py` | passed |
| `tests/test_crypto_tx_antifraud_48_0.py` + `test_crypto_payout_orchestrator_48_1.py` + `test_api_v1_freeze.py` | 46 passed (combined earlier run) |
| `tests/test_management_security.py` | run with 49.1 |
| FE `sprint_49_0` + `sprint_49_1` cabinets | 6 passed |

## 9. Regression status

- NEW REGRESSION: none observed in targeted suites
- PRE-EXISTING: `npm run lint` noise in unrelated ai-command/hercules tests (from 49.0)
- INFRASTRUCTURE: Hub BOS/COS remain in-memory (not multi-node durable)

## 10. Remaining debt

- BOS/COS not Postgres-backed
- Beauty calendar week grid
- Cafe floorplan
- Real TradingView widget when credentials exist
- Autonomous analysis delivery scheduler
- Shared DataTable column visibility

## 11. Market-data provider status

Default: **Не подключено** (`NullChartProvider`). Optional `CryptoTaChartProvider` reports `needs_config` unless TA API says connected. No fabricated live quotes.

## 12. Crypto antifraud verification

Sprint 48.x suites re-run green. Desk links to existing confirm panel; no bypass endpoint added.

## 13. Localhost URLs

| | |
|--|--|
| Frontend | http://localhost:5180 |
| Login | http://localhost:5180/login |
| Beauty | http://localhost:5180/workspace/beauty |
| Cafe | http://localhost:5180/workspace/cafe |
| Crypto | http://localhost:5180/workspace/crypto |
| Backend health | http://127.0.0.1:8080/health |

Demo: `owner@demo.corp` / `demo` (DEV `VITE_DEMO_AUTH`).

## 14. Files changed

**shared:** `BusinessCabinetShell.tsx`, `opsApi.ts`, `cabinetCapabilities.ts`  
**beauty:** `BeautyBusinessPage.tsx`, `beauty_os/api.py`, `beauty_os/facade.py`, `register.py`  
**cafe:** `CafeBusinessPage.tsx`, `cafe_os/api.py`, `cafe_os/facade.py`, `platform_cafe_os/facade.py`, `store.py` (`cos_shifts`)  
**crypto:** `CryptoOtcDeskPage.tsx`, `chartProvider.ts`, `otcPrefs.ts`  
**tests:** `tests/test_sprint_49_1_ops_cabinets.py`, FE `sprint_49_1_ops_cabinets.test.tsx`  
**docs:** `docs/SPRINT_49_1_RESULT.md`

## 15. Production-readiness assessment

Cabinets are **manual-test ready** for ops flows on a single backend process. Not production-durable for Beauty/Cafe data (in-memory Hub). OTC prefs are browser-local. Antifraud path is production-grade (Postgres). Ready for visual/manual review; not a claim of multi-tenant production cutover.
