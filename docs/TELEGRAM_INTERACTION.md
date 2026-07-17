# Telegram Interaction

Patterns for Telegram bot UX: routers, FSM, keyboards, localization, and middleware.

## Stack

- **Framework:** aiogram 3 (`Router`, `FSMContext`, filters, middleware)
- **FSM storage:** Redis (preferred) or in-memory fallback (`fsm_storage.py`)
- **Keyboards:** centralized in `keyboards.py`
- **Localization:** `services/automotive_localization.py` (RU/UK)

## Handler organization

### Modular routers (`routers/`)

Focused flows with thin handlers:

- Parse Telegram update (message, callback)
- Validate access (manager check, entry-point gate)
- Call service engine
- Render response with keyboard helper

### Feature handlers (`*_handlers.py`)

Domain-specific modules included from `handlers.py` or registered directly in `startup.py`.

### Legacy (`handlers.py`)

~5000 lines — **do not extend**. New features go in dedicated routers/handlers.

## FSM state groups

Defined in `states/entry_flow_states.py`:

| Group | Used by |
|-------|---------|
| `AutoClientFlow` | Auto client buy/sell/listing/services flows |
| `AutoDealerFlow` | Dealer onboarding |

FSM data may be persisted via `VerticalOnboardingEngineV1` for recovery across restarts.

## Callback conventions

| Prefix | Action |
|--------|--------|
| `mgr:take:` | Manager takes lead |
| `mgr:status:` | Update request status |
| `mgr:req:` | Open request card |
| `pip:item:` | Pipeline board item |
| `pip:move:` | Move pipeline stage |
| `pay:confirm:` / `pay:reject:` | Payment verification |

## Keyboards

All inline and reply keyboards live in `keyboards.py`:

- `crm_menu()` — manager main menu
- `auto_vertical_menu(lang)` — automotive module
- `auto_vertical_hub_menu()` — services hub categories

Keep keyboard construction out of business logic.

## Notifications to managers

`ManagerDeliveryEngineV1`:

- `notify_auto_client_request()` — new auto client request
- `send_to_manager()` — generic manager message with action keyboard
- `request_action_keyboard()` — inline actions on request cards

## Client notifications

Payment confirmations, SLA reminders, and marketing messages use:

- Direct `bot.send_message()` from handlers (after service returns data)
- `NotificationCenter` / `pg_*` engines for persisted notifications

## Access control in handlers

```python
if not await ManagerDeliveryEngineV1.is_platform_manager(user_id):
    await callback.answer("Нет доступа", show_alert=True)
    return
```

Automotive UI access: `services/automotive_telegram_access.py`

## Layer rules for handlers

**Allowed in handlers:**

- aiogram types, filters, FSM
- Service / vertical service calls
- Keyboard and localization helpers
- Config constants

**Forbidden in handlers:**

- `from database.session import get_session`
- Direct SQLAlchemy queries
- Repository instantiation

Run `scripts/check_handler_session_access.py` in CI.

## Debugging

- `/debug_manager` — manager diagnostics (`manager_debug_router`)
- Structured logging via `logging.getLogger(__name__)`
- Audit: `log_audit()` or `PlatformAuditEngineV1.log()`
