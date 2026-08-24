# AUTO 1.3 COMPLETE

CRM / clients / deals / reservations / sales / payments / profit / reports for ADOS Enterprise.

**Workspace:** Рабочее пространство → Авто → Клиенты / Продажи / Отчёты (`/workspace/auto?view=clients`)  
**API:** `/api/auto-ops/v1` (private, org-scoped; AUTO 1.0 / 1.1 / 1.2 contracts kept, CRM routes additive)  
**Not a public marketplace.** Frozen `/api/auto/v1` unchanged. Agro, Legal, Crypto, Beauty, Travel untouched.

---

## Completion checklist

| Gate | Result |
|------|--------|
| Clients | **PASS** |
| Leads | **PASS** |
| CRM pipeline | **PASS** |
| Reservations | **PASS** |
| Sales | **PASS** |
| Payments | **PASS** |
| Refunds | **PASS** |
| Profit / ROI / margin | **PASS** |
| Reports | **PASS** |
| Manager performance | **PASS** (factual counters only; `score` / `ranking` are null) |
| Privacy | **PASS** (backend RBAC for PII / identity documents) |
| Audit | **PASS** |
| Search | **PASS** |
| No hard delete | **PASS** (void / cancel / refund / soft cancel) |
| Notifications | **PASS** |
| Tasks | **PASS** (`deal_id` on tasks) |
| Demo | **PASS** |
| AUTO 1.0 regression | **PASS** |
| AUTO 1.1 regression | **PASS** |
| AUTO 1.2 regression | **PASS** |
| Tests | **48 passed / 0 failed** (backend 36 = AUTO 1.0 ×9 + AUTO 1.1 ×8 + AUTO 1.2 ×8 + AUTO 1.3 ×11; frontend 12 = AUTO 1.0 ×5 + AUTO 1.1 ×2 + AUTO 1.2 ×2 + AUTO 1.3 ×3) |
| Build | **PASS** for AUTO 1.3 files (repo `tsc -b` still reports pre-existing errors in unrelated agro/crypto/ai-command files) |

---

## Architectural decisions

1. **Extend AUTO 1.0–1.2 ops desk, do not create a second CRM universe.**  
   Deals, reservations, sales and receipts live in `services/auto_ops` + `applications/auto_enterprise`. Vehicle remains the hub: `GET /vehicles/{id}` now returns a `crm` block next to `logistics` and `customs`. Clients, expenses, documents, photos, tasks, audit, notifications are reused.

2. **Mixin, not a rewrite of `AutoOpsService`.**  
   `AutoOpsCrmMixin` in `services/auto_ops/crm.py`. Persistence still goes through `AutoOpsRepository` + memory fallback.

3. **Lead is a deal at stage `LEAD`.**  
   Pipeline: `LEAD → CONTACT → VEHICLE_SELECTED → RESERVED → DEPOSIT → CONTRACT → PARTIAL_PAYMENT → FINAL_PAYMENT → HANDOVER → COMPLETED` (+ `CANCELLED`, `LOST`). Stage changes persist and are audited.

4. **Reservation is one ACTIVE per vehicle.**  
   Second reserve returns 409 unless director sends `override` + reason. Expiry is computed on list/get when `expires_at` is in the past (`EXPIRED`). Sold vehicles cannot be reserved.

5. **Payments are receipts, not a second ledger.**  
   Manager may create `pending` / `planned`. Confirm requires `finance_write`. Confirmed amount cannot be edited — void / cancel / refund. Hard delete of a receipt returns 409. Confirmed expenses are soft-cancelled, not removed.

6. **Profit is only from stored records.**  
   `profit_snapshot(cost, revenue)`: profit = revenue − cost; ROI / margin are null when the divisor is 0. Never invents a sale. Cost = invested expenses; revenue = confirmed receipts.

7. **Manager performance is factual.**  
   Counters: leads assigned, contacts made, active deals, reservations, completed sales, sales revenue, outstanding tasks. `score` and `ranking` are always `null`. `employee_scoring: false`.

8. **PII is enforced in the service, not only in the UI.**  
   Passport / tax id / address require `pii` (director / admin / owner). Manager with `clients` may see phone / email. Accountant without `clients` sees contacts redacted. Identity documents (`passport`, `id_card`, `identity`, `contract`) and `owner_type=client` require `pii` on GET; access is audited.

9. **Operational screen answers nine questions in under 10 seconds:**  
   Who is the client? What car? What stage? How much? How much paid? How much owed? What documents? What is next? Who is responsible? Technical state stays in Настройки.

10. **Demo is explicit.**  
    `POST /crm/demo` requires `confirm_demo=true`. Records are flagged `is_demo`. Production is not seeded without the flag.

Rejected: employee scoring / ranking; hard delete of confirmed payments or completed sales; frontend-only hiding of passport data; putting CRM under frozen `/api/auto/v1`; starting AUTO 1.4.

---

## 1. Changed files

### Backend
- `services/auto_ops/crm_catalog.py` — stages, tabs, pipeline, receipts, reports, `profit_snapshot()`
- `services/auto_ops/crm.py` — deals / reservations / sales / receipts / search / reports mixin
- `services/auto_ops/catalog.py` — passport / contract document types; deal/receipt owners; CRM catalogs merged
- `services/auto_ops/telegram_boundary.py` — AUTO 1.3 intents (`/client`, `/deal`, `/sale`)
- `services/auto_ops/service.py` — hydrate CRM bags, vehicle `crm` block, PII on clients, soft-cancel expenses, sprint `AUTO_1.3`
- `services/auto_ops/rbac.py` — `pii` already on director / admin / owner
- `applications/auto_enterprise/config.py` — sprint `AUTO_1.3`
- `applications/auto_enterprise/api/crm_handlers.py`
- `applications/auto_enterprise/api/ops_handlers.py` — client item, search, document GET, reports query
- `applications/auto_enterprise/api/register.py` — CRM routes
- `database/models/auto_ops.py` — `AutoOpsDeal`, `AutoOpsReservation`, `AutoOpsSale`, `AutoOpsReceipt`; client PII; `deal_id` on tasks/documents
- `repositories/auto_ops_repository.py` — `KIND_MODEL` extended
- `migrations/versions/m2h345678901_auto_ops_1_3.py`
- `tests/test_auto_ops_1_0.py` / `test_auto_ops_1_1.py` / `test_auto_ops_1_2.py` — health sprint accepts 1.3
- `tests/test_auto_ops_1_3.py`

### Frontend
- `src/web/workspace/auto/AutoCrmDesk.tsx` — CRM desk, 10-second answers, reports desk, vehicle CRM block, settings panel
- `src/web/workspace/auto/AutoBusinessPage.tsx` — Клиенты / Продажи desks + Отчёты + vehicle sale tab + settings
- `src/web/workspace/auto/AutoLogisticsDesk.tsx` — return type on create submit (typecheck)
- `src/web/workspace/auto/sprint_auto_1_3.test.tsx`

### Docs
- `docs/SPRINT_AUTO_1_3_RESULT.md`

---

## 2. Migrations

- `migrations/versions/m2h345678901_auto_ops_1_3.py` revises `l1g234567890`
- Tables: `auto_ops_deals`, `auto_ops_reservations`, `auto_ops_sales`, `auto_ops_receipts`
- Additive columns: client PII (`passport_ref`, `tax_id`, `address`, `id_number`, `is_demo`); `deal_id` on tasks and documents
- Local API with `ADOS_SKIP_MIGRATIONS=1` keeps the in-memory fallback until this revision is applied.

---

## 3. API endpoints

Prefix: `/api/auto-ops/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/crm/deals` | List / create deal (lead = stage LEAD) |
| GET/POST | `/crm/deals/{deal_id}` | Get / update deal (stage, manager, price) |
| GET/POST | `/crm/reservations` | List / create reservation |
| POST | `/crm/reservations/{reservation_id}` | Cancel / expire / convert |
| GET/POST | `/crm/sales` | List / create sale |
| POST | `/crm/sales/{sale_id}` | Price / complete / cancel (no hard delete of completed) |
| GET/POST | `/crm/receipts` | Incoming payments |
| POST | `/crm/receipts/{receipt_id}` | Confirm / void / refund |
| POST | `/crm/demo` | Explicit DEMO BMW X5 + DEMO CLIENT |
| GET/POST | `/clients/{client_id}` | Get / edit client (PII gated) |
| GET | `/search?q=` | VIN, vehicle, client, phone, deal, payment reference, container, document |
| GET | `/documents/{document_id}` | Identity/contract GET requires `pii` + audit |
| GET | `/reports?report=` | sales, vehicle_profit, expenses, receipts, client_debt, managers, funnel, in_stock, in_transit |

Filters on deals/reports: `date`, `manager`, `vehicle`, `VIN`, `status`, `currency`.

Reused AUTO 1.0: `POST /clients`, `POST /expenses`, `POST /documents`, `POST /tasks` (`deal_id`), `GET /vehicles/{id}` now includes `crm`, `GET /audit`, `GET /logistics/notifications`.

---

## 4. Routes / pages to manually inspect

- `/workspace/auto?view=clients` — CRM desk (tabs: лиды / в работе / резерв / оплата / закрытые)
- `/workspace/auto?view=sales` — same desk, payment tab
- `/workspace/auto?view=reports` — Продажи, прибыль, расходы, поступления, задолженность, менеджеры, воронка, в наличии, в пути
- `/workspace/auto?view=settings` — Клиенты и продажи + демо-сделка
- Vehicle profile → **Продажа** — who / car / stage / paid / owed / next
- `/workspace/auto?view=customs` — AUTO 1.2 regression
- `/workspace/auto?view=logistics` — AUTO 1.1 regression
- `/workspace/auto?view=overview` — AUTO 1.0 regression

Login: `owner@demo.corp` / `demo`. Headers: `X-Organization-Id`, `X-Role`.

---

## 5. Demo scenario results

`POST /api/auto-ops/v1/crm/demo` with `{ "confirm_demo": true }` (director):

- Vehicle: BMW X5, VIN `WBAFR9C50DD777777`, labelled DEMO
- Client: `DEMO CLIENT`
- Process: Lead → contact → vehicle selection → reservation → deposit 5 000 → partial 10 000 → final 13 000 → handover → completed sale 28 000 USD
- CRM stage `COMPLETED`, vehicle `SOLD`
- Payments: paid 28 000, outstanding 0
- Profit: cost 18 000 (PURCHASE expense) → profit 10 000, ROI 55.56%, margin 35.71%
- Task «Выдать авто клиенту (demo)» with `deal_id`
- Document `demo-contract.pdf`
- Search finds VIN and payment reference `DEMO-DEP-1`
- Flag `is_demo: true`. Without `confirm_demo` the call returns 400.

---

## 6. Unresolved problems

- Telegram commands `/client`, `/deal`, `/sale` are prepared (`implemented: false`); live authorization remains AUTO 1.4.
- No live CRM / messenger / telephony integrations.
- Manager role has no `reports` permission (director / accountant see reports). Deal amounts on the CRM desk are visible to managers via `clients`.
- Identity-document preview still requires an uploaded `file_id`; metadata-only docs are listed without a file pane.
- AUTO 1.4 was **not** started.

---

## 7. Anything that requires actual external credentials / integration

None for AUTO 1.3. Future work that would need credentials:

- Live Telegram bot authorization (AUTO 1.4)
- Bank / acquiring payment confirmation
- External KYC / document-scan providers

Until those exist, every amount, stage and document on the desk is a stored company record.

---

## 8. Technical debt

- `AutoOpsService` is now three mixins (logistics + customs + CRM); keep sharing `_persist` / `_audit` rather than copying them.
- CRM in-app notifications write the logistics notifications bag (deduped); they are not a second comms product.
- Outstanding amount treats a receipt whose status became `refunded` as no longer paid; a separate `kind=REFUND` line nets against confirmed receipts.
- Postgres hydrate still depends on migration `m2h345678901`; without it the desk runs in memory for that org.
- Search matches deal id plus VIN / client name extras; it is org-scoped Auto ops search, not the public marketplace index.

STOP AFTER AUTO 1.3. DO NOT START AUTO 1.4.
