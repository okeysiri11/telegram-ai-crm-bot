# Sprint AGRO 2.2 — Grain operation lifecycle

## Result

**SPRINT AGRO 2.2 COMPLETE**

Do **not** start AGRO 2.3.

One Agro desk. Existing `/workspace/agro` + `/api/agro-ops/v1`. No second Agro subsystem. No fake GPS / weighbridge / lab / bank / Telegram / WhatsApp integrations.

## Architectural decisions

- **Extend `services/agro_ops`, do not replace.** Mixin `AgroOpsLifecycleMixin` (`services/agro_ops/operations.py`) on `AgroOpsService`. Storage remains the generic Postgres `agro_ops_records` registry. New kinds `agro_operation`, `weighing`, `quality_test`, `stock_movement`, `expense`, `ops_exception`, `truck_run` need **no SQL migration**.
- **Ledger inventory.** Current lot stock = sum of `stock_movement`. Lot `quantity` is a cache. Grain receive does **not** call 1.1 `warehouse_operation` (that path still mutates lot qty for existing warehouse UI). Transfer writes TRANSFER out + RECEIPT in so stock is not double-counted.
- **FIFO is a suggestion.** `fifo-suggest` returns `auto: false`. Sales require explicit lot allocation. Over-allocation is blocked (`available = physical − unshipped reservations`).
- **Health stays AGRO 2.0.** `sprint: agro-2.0`, `ux_version: AGRO_2_0`, `command_center: AGRO_2_0`, `crm_version: AGRO_2_1`. Additive `ops_version: AGRO_2_2`.
- **Same API for web and mobile.** `GET /operations/{id}` is Operation 360; UI only changes layout (desktop sections vs compact mobile cards).
- **Honest P&L.** Actual cost only from purchase + posted expenses with source records. Missing data → «Недостаточно данных для расчёта фактической прибыли». Plan never replaces actual.

Rejected: a new Agro package, auto FIFO allocation, silent stage skips, accusing carrier/supplier on weight loss, invented GPS/scale/lab hardware.

## Acceptance

| Gate | Status |
| --- | --- |
| Operation 360 | **PASS** |
| Purchase | **PASS** |
| Logistics | **PASS** |
| Truck runs | **PASS** |
| Weighing | **PASS** (NET = GROSS − TARE; inconsistent net rejected) |
| Weight discrepancies | **PASS** (exception for review; not an accusation) |
| Quality | **PASS** (profiles, PASS/WARNING/FAIL, decision + discount audit) |
| Warehouse receipt | **PASS** (actual accepted qty only) |
| Inventory ledger | **PASS** |
| Lots | **PASS** (`LOT-{year}-{CROP}-{seq}`) |
| Transfers | **PASS** |
| Processing/losses | **PASS** (drying/cleaning/write-off separated) |
| Sales allocation | **PASS** |
| Negative stock protection | **PASS** |
| Expenses | **PASS** |
| Cost basis | **PASS** |
| Actual P&L | **PASS** (only when sold qty + revenue + cost/t exist) |
| Planned vs actual | **PASS** |
| Document chain | **PASS** (one file, linked to operation; camera = real `capture` input) |
| Exception center | **PASS** |
| Director Today | **PASS** (clickable `grain_today` metrics) |
| Director stock | **PASS** (`available = physical − reservations`) |
| Mobile home | **PASS** (ОПЕРАЦИИ СЕГОДНЯ) |
| Mobile Operation 360 | **PASS** (compact cards, not 11 desktop tabs) |
| Mobile quick action | **PASS** (context-aware inside operation) |
| Mobile camera | **PASS** (`input capture="environment"` + gallery/files) |
| Search | **PASS** (operation #, plate, driver, lot, deal) |
| Traceability | **PASS** (`trace_forward` / `trace_back`) |
| Audit | **PASS** (`_activity` old/new) |
| RBAC backend | **PASS** (director / manager / logistics / warehouse / quality / accountant / viewer) |
| Idempotency | **PASS** (weighing, receipt, expense, truck status) |
| Tenant isolation | **PASS** |
| Critical numeric | **PASS** (500 → 492 received → 4 process loss → 488 usable → sold 300 remaining **188** → sold 100 remaining **88** → 100 blocked) |
| Desktop regression | **PASS** (2.0 command center + 2.1 CRM still green) |
| Cross-vertical | **PASS** (no shared APIs moved into Agro duplicates) |
| Public HTTPS | **PASS** |
| Tests | **PASS** |

## Tests

- backend **96 passed / 0 failed** (`test_sprint_agro_2_2` + 2.1 + 2.0 + command center + production 1.0 + operations 1.1–1.2 + 1.4–1.9 + live-data 1.3 + weather)
- frontend **61 passed / 0 failed** (`src/web` `workspace/agro`)

## Migrations

None. Same `agro_ops_records`. No sqlite.

## New endpoints

Registered **before** `/{alias}` catch-all:

- `GET/POST /api/agro-ops/v1/operations`
- `GET /api/agro-ops/v1/operations/today`
- `GET /api/agro-ops/v1/operations/stock`
- `POST /api/agro-ops/v1/operations/fifo-suggest`
- `GET /api/agro-ops/v1/operations/{id}`
- `POST /api/agro-ops/v1/operations/{id}/status`
- `POST /api/agro-ops/v1/operations/{id}/weighing`
- `POST /api/agro-ops/v1/operations/{id}/quality`
- `POST /api/agro-ops/v1/operations/{id}/quality-decision`
- `POST /api/agro-ops/v1/operations/{id}/receive`
- `POST /api/agro-ops/v1/operations/{id}/process`
- `POST /api/agro-ops/v1/operations/{id}/allocate`
- `POST /api/agro-ops/v1/operations/{id}/sale`
- `POST /api/agro-ops/v1/operations/{id}/expense`
- `POST /api/agro-ops/v1/operations/{id}/truck`
- `POST /api/agro-ops/v1/operations/{id}/transfer`
- `POST /api/agro-ops/v1/operations/truck/{id}/status`
- `POST /api/agro-ops/v1/operations/exceptions/{id}`

## URLs

- **DESKTOP URL:** http://127.0.0.1:5180/workspace/agro
- **MOBILE PUBLIC HTTPS URL:** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

Deep link: `/workspace/agro?view=operations&id=<uuid>`

Temporary Cloudflare tunnel to Vite `:5180` (API `:8080`). Laptop must stay on.

Live probe (this session): public page **200**, public health `ops_version=AGRO_2_2` / `sprint=agro-2.0`. Dashboard includes 10 `grain_today` metrics + `grain_stock`.

## What shipped

1. `AgroOperation` spine (`AG-{year}-{n:06d}`) linking purchase deal, sales, trucks, weighings, quality, lots, movements, expenses, documents, tasks, exceptions, timeline.
2. Operation 360 desktop header + sections; mobile compact KPIs + section buttons.
3. Status matrix (Черновик → … → Закрыто) plus Проблема / Заблокировано / Отменено; impossible jumps rejected.
4. Purchase block: planned qty/price is **not** actual cost. Custom commodity string allowed (directory crops still exist).
5. Truck runs reuse vehicle by plate. Mobile driver card: call, maps link, load/depart/arrive/unload, photo/doc, problem (RBAC).
6. Two-scale weighing + configurable kg/% tolerance → exception, not blame.
7. Commodity quality profiles; discount shows original / adjustment / final and audits the purchase deal `accepted_price` (does not silently rewrite `price`).
8. Warehouse receipt of **actual** net; lots; ledger movements RECEIPT/TRANSFER/SALE/WRITE_OFF/ADJUSTMENT/RETURN/PROCESSING.
9. Processing loss kinds kept separate. Sale allocates lots; FIFO suggestion only.
10. Cost basis from source records; P&L when calculable; PLAN | ACTUAL.
11. Director Today grain metrics (click → filtered operations). Stock by crop/warehouse/lot.
12. Search finds operation number, truck plate, driver, lot, deal `operation_number`.

## Modified files

- `services/agro_ops/operations.py` (new mixin)
- `services/agro_ops/service.py`
- `services/agro_ops/rbac.py`
- `services/agro_ops/command_center.py`
- `services/agro_ops/files.py`
- `applications/agro_enterprise/api/ops_handlers.py`
- `applications/agro_enterprise/api/register.py`
- `src/web/workspace/agro/AgroOperationsList.tsx` (new)
- `src/web/workspace/agro/AgroOperation360.tsx` (new)
- `src/web/workspace/agro/AgroBusinessPage.tsx`
- `src/web/workspace/agro/AgroCommandCenter.tsx`
- `src/web/workspace/agro/AgroQuickCreateSheet.tsx`
- `src/web/workspace/agro/AgroGlobalSearch.tsx`
- `src/web/workspace/agro/agroOpsNav.ts`
- `src/web/workspace/agro/agroLabels.ts`
- `tests/test_sprint_agro_2_2.py` (new)
- `src/web/workspace/agro/sprint_agro_2_2.test.tsx` (new)

## Unresolved real issues

1. **Hardware adapters** (GPS, weighbridge, laboratory instruments, bank, Telegram, WhatsApp) are not connected. Records are operator-entered. Architecture can host adapters later.
2. **1.1 warehouse_operation** still mutates lot `quantity` directly for the legacy warehouse panel. Grain 2.2 receipts use the ledger. Mixed use of both paths on the same lot can diverge until 1.1 is ledger-backed.
3. **Physical Android 412×915 tap-through** of the full Home → Operation 360 → weighing → sale path was not driven on a device in this session. Layout is `useIsMobile` + public HTTPS loads the same app; buttons are `min-h-11`.
4. Storage expense is calculated only when an expense row with category `storage` is posted from configured terms — there is no silent daily accrual without that record.

**STOP. Do not start AGRO 2.3.**
