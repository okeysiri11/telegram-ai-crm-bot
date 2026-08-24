# SPRINT AGRO OPERATIONS 1.2 — RESULT

## STATUS

**COMPLETE** as an operational expansion of the existing AGRO vertical.

No second AGRO application. No new in-memory-only entities. New kinds live in `agro_ops_records` JSONB and survive backend/frontend restart when Postgres is available.

Demo data is loaded only by an explicit **Загрузить демо AGRO** button (director / platform owner). Nothing is auto-injected. Demo rows are marked `[DEMO]` / `is_demo`.

## DONE

### Notifications (§38)

From a notification the operator can:

- Открыть (returns linked entity, e.g. market price)
- Отметить прочитанным
- Создать задачу
- Добавить в календарь
- Отложить
- Отключить правило

API: `POST /api/agro-ops/v1/notifications/{id}/actions`

### Tasks from alerts / deliveries (§39)

`POST /tasks/from-entity` and notification action `create_task`.

Task fields: owner, deadline, priority, linked entity (`entity_type` / `entity_id`).

Example title: «Проверить поставку №15».

### Empty-state UX (§40)

| Screen | Copy |
|--------|------|
| Уведомления | «Пока нет сигналов.» + Создать правило / Создать напоминание |
| Календарь | Month grid always shown, including empty month |
| Культуры | Directory of default crops even at 0 / 0 |
| Поставки | «Поставок ещё нет.» + Добавить поставку |

### Demo (§41)

`POST /api/agro-ops/v1/bootstrap` — wheat 500 t available / 800 t demand / 300 t delivery / price rule &lt; 8500 / calendar deadline / DEMO notification.

Idempotent. Viewer cannot load demo.

### Crop book / deliveries / alerts (§42)

- `availability` + `demand` → crop balance: available, demand, gap
- `shipment` progress: `quantity_planned`, `quantity_delivered`, `progress_pct`
- Partial: `POST /deliveries/{id}/progress`
- Linked trip weight is aggregated into the same progress
- Delivery deadline creates a calendar event
- `POST /calendar/{id}/remind` + `POST /reminders/evaluate`
- `alert_rule` + `POST /alerts/evaluate` with cooldown
- Manual market price can satisfy a rule; notification links back to that price

### RBAC (§45)

| Role | Access |
|------|--------|
| `agro_director` | Full control, demo load, intel evaluate |
| `agro_accountant` | Finance, documents, calendar/tasks; read logistics/deliveries; no operational create |
| `agro_manager` | Operational CRUD; no finance |
| `agro_viewer` / `agro_observer` | Read only |

### Scheduler

- `agro.alerts.evaluate` — `0 6,18 * * *`
- `agro.calendar.reminders` — `0 5,11,17 * * *`

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops`** with `AgroOpsDeskMixin` (`desk.py`). No new vertical.
- **Same JSONB registry** — kinds: `availability`, `demand`, `alert_rule`, `alert`, `delivery_leg`.
- **`agro_viewer` added** as an explicit view-only role; `agro_observer` kept for 1.0 compatibility.
- **Beauty/Cafe bootstrap pattern** reused (`onBootstrap` + shell button). Label overridden to «Загрузить демо AGRO».
- **Alert evaluator never invents prices** — it only reads stored `market_price` rows.

## ENDPOINTS (additive)

- `GET /crops/directory` `GET /crops/{id}/balance`
- `POST /deliveries/{id}/progress`
- `POST /alerts/evaluate` `POST /reminders/evaluate`
- `POST /calendar/{id}/remind`
- `POST /notifications/{id}/actions`
- `POST /tasks/from-entity`
- `POST /bootstrap`

## TESTS

- Backend: `tests/test_sprint_agro_operations_1_2.py` plus regression `1_0` + `1_1`
- Frontend: `src/web/workspace/agro/sprint_agro_operations_1_2.test.tsx`
- Health sprint id: **`agro-1.2`**

## SCENARIO 42

Covered by `test_acceptance_crop_delivery_alert_calendar`:

Пшеница 1000 t available / 600 t demand / +400 gap → delivery 600 t + PDF → calendar + 1-day reminder → price rule &lt; 8500 → manual 8200 → evaluate → notification → open linked price → task → partial 200 t = 33.33% → second trip 100 t → aggregated 300 / 600 = 50%. Tenant isolation checked.

Persistence is the existing `agro_ops_records` store.

## PARTIAL / DEFERRED

- Manager «limited financial visibility configurable» — manager still has no finance permission (same as 1.0); no per-org finance toggle yet
- Canvas price charts — still dated observation lists from 1.1
- Telegram/email reminder delivery — in-app only unless those channels are configured

## NEXT

Stop after AGRO Operations 1.2 unless a licensed feed or WASDE XML parse is requested.
