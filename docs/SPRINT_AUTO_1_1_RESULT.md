# AUTO 1.1 COMPLETE

Vehicle logistics / containers / ports / delivery tracking for ADOS Enterprise.

**Workspace:** Рабочее пространство → Авто → Логистика (`/workspace/auto?view=logistics`)  
**API:** `/api/auto-ops/v1` (private, org-scoped; AUTO 1.0 contracts kept, logistics routes additive)  
**Not a public marketplace.** Frozen `/api/auto/v1` unchanged. Agro, Legal, Crypto, Beauty, Travel untouched.

---

## Completion checklist

| Gate | Result |
|------|--------|
| Logistics dashboard | **PASS** |
| Shipments | **PASS** |
| Carriers | **PASS** |
| Drivers | **PASS** |
| Transport | **PASS** |
| Containers | **PASS** |
| Vessels | **PASS** |
| Ports | **PASS** |
| Documents | **PASS** |
| Expenses | **PASS** |
| ETA / delays | **PASS** |
| Vehicle integration | **PASS** |
| Tasks | **PASS** |
| Notifications | **PASS** |
| RBAC | **PASS** |
| Tests | **24 passed / 0 failed** (backend 17 = AUTO 1.0 ×9 + AUTO 1.1 ×8; frontend 7 = AUTO 1.0 ×5 + AUTO 1.1 ×2) |
| Build | **PASS** for AUTO 1.1 files (repo `tsc -b` still reports pre-existing errors in unrelated agro/crypto/ai-command files) |

---

## Architectural decisions

1. **Extend AUTO 1.0 ops desk, do not create a second logistics universe.**  
   Shipment / carrier / driver / truck / container / vessel / port live in `services/auto_ops` + `applications/auto_enterprise`. Vehicle remains the hub: `GET /vehicles/{id}` returns a `logistics` block. Expenses, documents, photos, tasks, audit are reused.

2. **Mixin, not a rewrite of `AutoOpsService`.**  
   `AutoOpsLogisticsMixin` in `services/auto_ops/logistics.py` keeps the 1.0 service file from becoming a second monolith. Persistence still goes through `AutoOpsRepository` + memory fallback.

3. **No fake live tracking.**  
   ETA, vessel, container position are stored values only, labelled «Введено вручную». Map is a labelled origin → port → destination schematic. AIS / shipping-line / container APIs are an integration boundary for later sprints.

4. **Verified UN/LOCODE only.**  
   `REFERENCE_PORTS` is a catalog of known codes (USNYC, USSAV, UAODS, GEPTI, …). Org ports may omit a code; invented codes are rejected. Nothing is auto-seeded into production tables.

5. **Manager may create logistics expenses only.**  
   AUTO 1.0 test that manager cannot post `PURCHASE` stays green. Inland / sea / port / container / demurrage / UA transport can be posted from the shipment desk. Accountant still owns purchase finance.

6. **Driver PII is RBAC-gated.**  
   Passport / licence are stored but redacted on list/get unless `pii` (director / admin / platform owner).

7. **Demo is explicit.**  
   `POST /logistics/demo` requires `confirm_demo=true`. Records are flagged `is_demo`. Never mixed into production without that call.

Rejected: live AIS claims; silent GPS fabrication; auto-seeding demo cars; a separate logistics microservice; putting ops under frozen `/api/auto/v1`.

---

## 1. Changed files

### Backend
- `services/auto_ops/logistics_catalog.py` — types, statuses, tabs, pipeline, delay engine, verified ports
- `services/auto_ops/logistics.py` — shipment/container/carrier/driver/truck/vessel/port mixin
- `services/auto_ops/catalog.py` — additive expense / document / photo types; logistics catalogs merged
- `services/auto_ops/rbac.py` — `pii` permission
- `services/auto_ops/telegram_boundary.py` — AUTO 1.1 intents (`/logistics`, `/container`, `/eta`, …)
- `services/auto_ops/service.py` — hydrate, vehicle logistics block, logistics expenses, soft-delete docs, shipment-linked tasks/photos
- `applications/auto_enterprise/config.py` — sprint `AUTO_1.1`
- `applications/auto_enterprise/api/logistics_handlers.py`
- `applications/auto_enterprise/api/register.py`
- `database/models/auto_ops.py` — additive logistics models + extra columns
- `repositories/auto_ops_repository.py` — `KIND_MODEL` extended
- `migrations/versions/k0f123456789_auto_ops_1_1.py`
- `tests/test_auto_ops_1_0.py` — health sprint accepts 1.1
- `tests/test_auto_ops_1_1.py`

### Frontend
- `src/web/workspace/auto/AutoLogisticsDesk.tsx` — operating desk + vehicle logistics block + settings
- `src/web/workspace/auto/AutoBusinessPage.tsx` — Логистика is the desk, not a filtered vehicle table
- `src/web/workspace/auto/autoLabels.ts`
- `src/web/workspace/auto/sprint_auto_1_1.test.tsx`

---

## 2. Migrations

`migrations/versions/k0f123456789_auto_ops_1_1.py` revises `j9e012345678`.

Additive tables:

- `auto_ops_shipments`
- `auto_ops_carriers`
- `auto_ops_drivers`
- `auto_ops_trucks`
- `auto_ops_containers`
- `auto_ops_container_vehicles`
- `auto_ops_vessels`
- `auto_ops_ports`
- `auto_ops_logistics_events`
- `auto_ops_notifications`
- `auto_ops_logistics_settings`

Additive columns on AUTO 1.0 tables: `shipment_id` on expenses/tasks/photos; document owner ids + `archived_at`; photo `location` / `captured_at`.

In-memory fallback still works when Postgres tables are not migrated yet.

---

## 3. New API endpoints

All under `/api/auto-ops/v1` (headers `X-Organization-Id`, `X-Role`).

| Method | Path |
|--------|------|
| GET | `/logistics` |
| GET/POST | `/logistics/shipments` |
| GET/POST | `/logistics/shipments/{id}` |
| POST | `/logistics/shipments/{id}/events` |
| GET/POST | `/logistics/carriers` |
| POST | `/logistics/carriers/{id}` |
| GET/POST | `/logistics/drivers` |
| POST | `/logistics/drivers/{id}` |
| GET/POST | `/logistics/trucks` |
| POST | `/logistics/trucks/{id}` |
| GET/POST | `/logistics/containers` |
| GET/POST | `/logistics/containers/{id}` |
| POST | `/logistics/containers/{id}/vehicles` |
| GET/POST | `/logistics/vessels` |
| POST | `/logistics/vessels/{id}` |
| GET/POST | `/logistics/ports` |
| GET | `/logistics/notifications` |
| GET/POST | `/logistics/settings` |
| POST | `/logistics/demo` |
| POST | `/documents/{id}` (rename / replace / restore) |

Existing `/vehicles/{id}` now includes `logistics`. Existing `/expenses` and `/tasks` accept `shipment_id`.

---

## 4. Manual test URLs / routes

Local: API `:8080`, Vite `:5180`, demo auth `owner@demo.corp` / `demo`.

- Desk: http://localhost:5180/workspace/auto?view=logistics
- Carriers: same page → «Перевозчики»
- Containers: → «Контейнеры»
- Settings / logistics catalogs: http://localhost:5180/workspace/auto?view=settings
- Vehicle profile → Логистика: open a car from Автомобили
- Telegram intents (prepared, not live): http://localhost:5180/workspace/auto?view=telegram

---

## 5. Demo workflow

1. Настройки → «Создать демо-перевозку» **or** `POST /api/auto-ops/v1/logistics/demo` with `{ "confirm_demo": true }` as director.
2. Opens a labelled DEMO BMW X5: US auction → inland carrier → Savannah → container `DEMO1234567` → vessel → Odesa.
3. Логистика → tab «В море» shows the shipment; delay badge uses stored planned vs current ETA (manual).
4. Open the shipment: pipeline, schematic route («не live-tracking»), change stage / ETA, add event, expense, document, task, assign carrier/container/vessel.
5. Vehicle profile → Логистика and Финансы include the linked shipment and its expenses.

Do not run demo against a production org unless you intend to create `is_demo` records there.

---

## 6. Unresolved issues

- Live AIS / shipping-line / container tracking is **not** connected (by design).
- Coordinates are optional and never invented; schematic map has no geocoder unless one already exists (none reused here).
- Telegram commands are prepared intents only; private auth hardening remains AUTO 1.4.
- Desk notifications are in-app + deduped; they are not pushed through `/api/enterprise-comms/v1` yet (honest boundary).
- Customs remains a vehicle lifecycle stage; broker integrations are still a later sprint.
- Soft-deleted documents restore via `POST /documents/{id}` with `{ "restore": true }`; hard delete is the second delete.
- Postgres migration must be applied in environments that persist ops tables; tests use memory fallback when tables are absent.

---

## 7. Integrations recommended for AUTO 1.2+

- AIS / vessel provider behind the existing `position_source` / `tracking_url` fields
- Container line tracking (booking + B/L) with «Получено от источника» labels
- Geocoding for optional origin/destination coordinates
- Enterprise comms channel for delayed / port / delivery events (with the same dedupe keys)
- Customs / broker document pack as a first-class AUTO module
- Shared counterparty directory if Auto should reuse a platform CRM instead of `auto_ops_carriers`

**STOP AFTER AUTO 1.1. AUTO 1.2 was not started.**
