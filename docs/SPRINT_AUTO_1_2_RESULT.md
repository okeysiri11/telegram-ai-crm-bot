# AUTO 1.2 COMPLETE

Customs / broker / import VAT / certification / registration preparation for ADOS Enterprise.

**Workspace:** Рабочее пространство → Авто → Растаможка (`/workspace/auto?view=customs`)  
**API:** `/api/auto-ops/v1` (private, org-scoped; AUTO 1.0 / 1.1 contracts kept, customs routes additive)  
**Not a public marketplace.** Frozen `/api/auto/v1` unchanged. Agro, Legal, Crypto, Beauty, Travel untouched.

---

## Completion checklist

| Gate | Result |
|------|--------|
| Customs workspace | **PASS** |
| Customs cases | **PASS** |
| Customs calculations | **PASS** |
| Import VAT | **PASS** |
| Payments | **PASS** |
| Brokers | **PASS** |
| Document checklist | **PASS** |
| Document preview | **PASS** |
| Certification | **PASS** |
| Registration preparation | **PASS** |
| Vehicle timeline | **PASS** |
| Accounting view | **PASS** |
| Multi-currency | **PASS** |
| RBAC | **PASS** |
| Audit | **PASS** |
| AUTO 1.0 regression | **PASS** |
| AUTO 1.1 regression | **PASS** |
| Tests | **34 passed / 0 failed** (backend 25 = AUTO 1.0 ×9 + AUTO 1.1 ×8 + AUTO 1.2 ×8; frontend 9 = AUTO 1.0 ×5 + AUTO 1.1 ×2 + AUTO 1.2 ×2) |
| Build | **PASS** for AUTO 1.2 files (repo `tsc -b` still reports pre-existing errors in unrelated agro/crypto/ai-command files) |

---

## Architectural decisions

1. **Extend AUTO 1.0/1.1 ops desk, do not create a second customs universe.**  
   Cases and brokers live in `services/auto_ops` + `applications/auto_enterprise`. Vehicle remains the hub: `GET /vehicles/{id}` returns a `customs` block next to `logistics`. Expenses, documents, photos, tasks, audit are reused.

2. **Mixin, not a rewrite of `AutoOpsService`.**  
   `AutoOpsCustomsMixin` in `services/auto_ops/customs.py`. Persistence still goes through `AutoOpsRepository` + memory fallback.

3. **No live Гостаможня / НБУ / official law calculator.**  
   Duty, excise and import VAT use **organization-configured rates**. FX is stored/manual, labelled «Введено вручную». UI copy: «Расчёт по ставкам организации. Это не официальный калькулятор Гостаможни и не live-курс НБУ.» Incomplete inputs return `incomplete` — values are never invented.

4. **Formula (unit-tested, org-overridable defaults):**  
   `value_uah = customs_value * fx_rate_to_uah`  
   `duty = value_uah * duty_rate` (default 10%)  
   `excise = engine_cc * per_cc[fuel] * age_coeff`  
   `vat = (value_uah + duty + excise) * vat_rate` (default 20%)  
   `grand = duty + excise + vat + broker_fee`

5. **Manager may create customs expense categories only.**  
   AUTO 1.0 test that manager cannot post `PURCHASE` stays green. Duty / excise / import VAT / broker / certification / MREO can be posted from the customs desk. Accountant still owns purchase finance.

6. **Operational screen answers eight questions** and hides API/sprint/persistence details. Technical state remains behind Настройки → admin.

7. **Demo is explicit.**  
   `POST /customs/demo` requires `confirm_demo=true`. Records are flagged `is_demo`.

Rejected: claiming live customs/NBU APIs; silent invented payments; a separate customs microservice; putting ops under frozen `/api/auto/v1`; starting AUTO 1.3.

---

## 1. Changed files

### Backend
- `services/auto_ops/customs_catalog.py` — statuses, tabs, pipeline, checklist, org rates, `calculate_customs()`
- `services/auto_ops/customs.py` — case/broker/VAT/certification mixin
- `services/auto_ops/catalog.py` — duty/excise/VAT/MREO expenses; customs catalogs merged; finance KPI group expanded
- `services/auto_ops/telegram_boundary.py` — AUTO 1.2 intents (`/customs`, `/vat`, `/broker`)
- `services/auto_ops/service.py` — hydrate, vehicle customs block, customs expenses/tasks/documents, sprint `AUTO_1.2`
- `applications/auto_enterprise/config.py` — sprint `AUTO_1.2`
- `applications/auto_enterprise/api/customs_handlers.py`
- `applications/auto_enterprise/api/register.py`
- `database/models/auto_ops.py` — `AutoOpsCustomsCase`, `AutoOpsBroker`, `AutoOpsCustomsSetting`; `customs_id` on expenses/tasks
- `repositories/auto_ops_repository.py` — `KIND_MODEL` extended
- `migrations/versions/l1g234567890_auto_ops_1_2.py`
- `tests/test_auto_ops_1_0.py` — health sprint accepts 1.2
- `tests/test_auto_ops_1_1.py` — health sprint accepts 1.2
- `tests/test_auto_ops_1_2.py`

### Frontend
- `src/web/workspace/auto/AutoCustomsDesk.tsx` — operating desk, vehicle block, settings panel
- `src/web/workspace/auto/AutoBusinessPage.tsx` — Растаможка desk + vehicle tab + settings
- `src/web/workspace/auto/autoLabels.ts`
- `src/web/workspace/auto/sprint_auto_1_2.test.tsx`

### Docs
- `docs/SPRINT_AUTO_1_2_RESULT.md`

---

## 2. Migrations

- `migrations/versions/l1g234567890_auto_ops_1_2.py` revises `k0f123456789`
- Tables: `auto_ops_customs_cases`, `auto_ops_brokers`, `auto_ops_customs_settings`
- Additive columns: `auto_ops_expenses.customs_id`, `auto_ops_tasks.customs_id`, `auto_ops_documents.broker_id`
- Local API with `ADOS_SKIP_MIGRATIONS=1` keeps the in-memory fallback until this revision is applied.

---

## 3. API endpoints

Prefix: `/api/auto-ops/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/customs` | Desk list (same as cases) |
| GET/POST | `/customs/cases` | List / create case |
| GET/POST | `/customs/cases/{case_id}` | Get / update case |
| POST | `/customs/cases/{case_id}/calculate` | Recalculate org-rate payments |
| GET/POST | `/customs/brokers` | Broker directory |
| POST | `/customs/brokers/{broker_id}` | Update broker |
| GET/POST | `/customs/settings` | Org rates (admin write) |
| POST | `/customs/demo` | Explicit DEMO BMW X5 USA→UA |

Reused AUTO 1.0: `POST /expenses` (customs categories + `customs_id`), `POST /documents`, `POST /tasks`, `GET /vehicles/{id}` now includes `customs`.

---

## 4. Routes / pages to manually inspect

- `/workspace/auto?view=customs` — operating desk (tabs, answers, checklist, brokers)
- `/workspace/auto?view=settings` — Растаможка rates + demo button
- Vehicle profile → **Таможня**
- `/workspace/auto?view=logistics` — AUTO 1.1 regression
- `/workspace/auto?view=overview` — AUTO 1.0 regression

Login: `owner@demo.corp` / `demo`. Headers: `X-Organization-Id`, `X-Role`.

---

## 5. Demo scenario results

`POST /api/auto-ops/v1/customs/demo` with `{ "confirm_demo": true }` (director):

- BMW X5, VIN labelled DEMO, status `CUSTOMS`, location Одесса таможня
- Case `PAYMENT_PENDING`, org-rate calculation complete (duty / excise / import VAT / broker)
- Documents present: invoice, title, B/L, packing list, export
- Missing: МД, broker pack, payment confirmation, certificate, МРЕО
- Paid: broker fee 8 000 UAH; planned: duty 76 775 UAH
- Flag `is_demo: true`. Without `confirm_demo` the call returns 400.

---

## 6. Unresolved problems

- Live electronic customs declaration / Гостаможня status is not connected.
- NBU FX is not connected; operators enter the rate.
- Certification lab and МРЕО are status/document panels, not government APIs.
- Telegram commands are prepared (`implemented: false`); live auth remains AUTO 1.4.
- AUTO 1.3 was **not** started.

---

## 7. Anything that requires actual external credentials / integration

None for AUTO 1.2. Future integrations that would need credentials:

- Ukrainian customs / electronic declaration systems
- NBU (or bank) FX feed
- Broker / certification-lab portals
- МРЕО / document-exchange APIs

Until those exist, every amount and date on the desk is a stored company record.

---

## 8. Technical debt

- `AutoOpsService` is now two mixins (logistics + customs); a third vertical mixin should keep sharing `_persist` / `_audit` rather than copying them.
- Org rates live in `customs_settings.payload` JSON; a typed column per coefficient can wait until finance signs off the formula.
- Document preview is a file-content link only when `file_id` was uploaded; metadata-only docs show on the checklist without a preview pane.
- Manager can post customs-category expenses (same exception as AUTO 1.1 logistics); purchase finance remains accountant/director.
- Postgres hydrate still depends on the new migration; without it the desk runs in memory for that org.

STOP AFTER AUTO 1.2. DO NOT START AUTO 1.3.
