# HOTFIX 46.2.2 — Auto Add Vehicle VIN FSM Runtime Routing

## ROOT CAUSE

Production path for «🚗 Добавить авто» kept FSM only in **process-local dicts**:

- `auto_vertical_handlers.auto_vertical_flow`
- `auto_vertical_handlers.auto_vertical_active`

Canonical Telegram FSM for other flows uses **aiogram FSM storage** (`fsm_storage.py` → Redis in production).

When Update N asked for VIN and Update N+1 arrived without that process memory (multi-worker, restart, or `auto_vertical_active` cleared by entry-point), the filter:

```python
auto_vertical_active.get(uid) and auto_vertical_flow.get(uid)
```

failed. Then:

| Input | Path | Result |
|-------|------|--------|
| «Нет» | `handlers.handle_text` catch-all | **silent** (no reply) |
| «Да» | Super App / AI Manager / general path | LLM reply + Score/Dept/Intent |

That matches real Telegram smoke.

## PRODUCTION HANDLER (canonical)

`routers/auto_add_vehicle_router.py` — registered **first** in `platform_legacy/adapter.py` / `startup.BOT_ROUTER_PATHS`.

VIN question call site:

```text
step_optional_costs → "Хотите добавить VIN автомобиля?" + auto_add_car_vin_inline()
```

Callbacks:

- `auto:add:vin:yes` → `handle_vin_yes`
- `auto:add:vin:no` → `handle_vin_no`

Legacy `addcar:vin:*` still accepted.

## STATE STORAGE

| Layer | Role |
|-------|------|
| aiogram FSM (`AutoAddVehicleFlow`) via Redis/MemoryStorage | **source of truth** |
| `active_flow` / `active_state` / `draft` in FSM data | persistence across updates |
| `auto_vertical_flow` dict | write-through mirror for readiness probes only |

## ROUTING RULE

```
Telegram update
      │
      ▼
AutoAddVehicleFlow active? ──YES──► durable FSM handlers (no LLM)
      │
     NO
      ▼
Super App / Intent / AI / handle_text
```

Hard guard: `assert_no_active_add_vehicle()` in:

- `telegram_super_app_router.concierge_chat`
- `handlers.handle_text`
- `auto_vertical_ai_manager_chat`

raises / returns `ACTIVE_FLOW_ROUTING_REQUIRED`.

## AFTER

```
VIN_DECISION + NO  → finalize (vin=None) → COMPLETED → FSM cleared
VIN_DECISION + YES → WAITING_VIN → "Отправьте VIN автомобиля."
```

Optional VIN/photo never blocks create.

## CLIENT METADATA

`sanitize_ai_reply_for_client` strips Score / Priority / Dept / Intent (and 📊 Score).

## TESTS

`tests/test_hotfix_46_2_2_add_car_vin_fsm.py` — separate-update persistence, AI guard, VIN yes/no, callbacks, router order.
