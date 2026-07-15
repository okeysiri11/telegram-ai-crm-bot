# Events

## Existing production buses (unchanged)

| Module | Role |
|--------|------|
| `events.py` | Legacy unified in-memory/registry bus |
| `services/crm_event_bus.py` | PostgreSQL-backed CRM event bus |

## New scaffold (`src/events`)

Domain events (dataclass):

- `LeadCreated`
- `LeadAssigned`
- `LeadClosed`
- `ClientCreated`
- `ManagerAssigned`
- `PhotoUploaded`

Dispatcher:

```python
from src.events import get_dispatcher, LeadCreated

dispatcher = get_dispatcher()

async def on_lead(event: LeadCreated):
    ...

dispatcher.subscribe_type(LeadCreated, on_lead)
await dispatcher.dispatch(LeadCreated(lead_id="...", request_number="AUTO-0001"))
```

## Why `src/events` instead of root `events/`?

Root already has `events.py`. A package named `events/` would shadow/break legacy imports.  
Scaffold lives under `src/events` until a controlled rename/cutover.

## Migration path

1. Emit domain events from new facades (alongside existing bus publish).
2. Dual-write period with parity checks.
3. Retire duplicate subscribers.
4. Optionally rename packages.
