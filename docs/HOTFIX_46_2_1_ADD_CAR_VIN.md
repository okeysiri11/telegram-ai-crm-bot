# HOTFIX 46.2.1 — Auto Add Vehicle VIN Deadlock

## Root cause

File: `auto_vertical_handlers.py`  
Flow: 🚗 Добавить авто → in-memory `auto_vertical_flow` step `vin_optional`

1. `_finalize_add_car` called `_clear_flow()` **before** `CarEngineV1.create_car`.
2. `create_car` → `TenantContextService.require_tenant_id` raised `PermissionError` (not `CarEngineError`).
3. Exception was uncaught → no success message; draft already wiped → looks like ASK_VIN freeze.

Secondary: VIN asked as plain text «• Да / • Нет» without inline callbacks; text «Нет» could be fragile vs menu routing.

## Fix

- `resolve_vin_decision()` in `services/auto_add_vehicle_vin.py` (text + `addcar:vin:*` callbacks)
- VIN FSM handled **before** menu/screen routing
- Finalize only clears state on success; on error → `finalize_retry` keeps draft
- Inline buttons [✅ Да] [❌ Нет]
- Success: «Готово. Автомобиль … добавлен без VIN.»

## State machine

`WAITING_VIN_DECISION (vin_optional)`  
→ NO → `FINALIZE_VEHICLE` → `IDLE`  
→ YES → `WAITING_VIN (vin_input)` → VIN/skip → `FINALIZE` → `IDLE`
