# Verticals

Business verticals are registered in `src/verticals/__init__.py` and exposed via vertical services.

## Registry

| Code | Title | Maturity | Manager role | Domain package |
|------|-------|----------|--------------|----------------|
| `auto` | Automotive | **production** | `AUTO_MANAGER` | `src.domains.automotive` |
| `agro` | Agro | **partial** | `AGRO_MANAGER` | `src.domains.crm` |
| `realty` | Realty | scaffold | — | `src.domains.crm` |
| `legal` | Legal | scaffold | — | `src.domains.legal` |
| `logistics` | Logistics | scaffold | — | `src.domains.logistics` |

## Capabilities by vertical

### auto (production)

- Client requests (buy/sell/listing/services/callback)
- Dealer onboarding and portal
- Inventory, VIN decode, marketing campaigns
- Commercial billing and partner hub
- Manager CRM and pipeline boards

### agro (partial)

- Deep-link lead ingest via `LeadEngineV1`
- CRM pipeline boards (shared with auto infrastructure)
- Deal lifecycle extensions in handlers

### realty, legal, logistics (scaffold)

- Entry links and hub categories
- Lead ingest API via `*VerticalService.ingest_lead()`
- Domain facades in `src/domains/{legal,logistics}/`

## Vertical service API

Each vertical exposes a service class under `src/verticals/<code>/service.py`:

```python
from src.verticals.auto.service import AutoVerticalService

health = await AutoVerticalService.health()
request = await AutoVerticalService.get_client_request("AUTO-0001")
```

Via DI container:

```python
from container import get_container

auto = get_container().vertical("auto")
```

## Routing

Vertical selection happens at:

1. `/start` deep links — `services/tenant_routing.py`, `ENTRY_LINK_REGISTRY`
2. Lead engine ingest — `services/pg_lead_engine.py`
3. Manager subscriptions — `services/pg_vertical_routing_engine.py`
4. Pipeline boards — `CRM_PIPELINE_VERTICALS` in pipeline models

See [ROUTING.md](ROUTING.md) for entry-point details.

## Adding a new vertical

1. Add `VerticalDefinition` to `src/verticals/__init__.py`
2. Create `src/verticals/<code>/service.py` and `repository.py`
3. Register in `container.py` vertical loop
4. Add enum value to `services/system_roles.py` → `Vertical`
5. Add entry link in `services/tenant_routing.py`
6. Add Alembic migration for vertical-specific tables if needed
7. Create thin Telegram router — **do not** extend `handlers.py`

## Strangler migration path

```
Phase 1 (current): vertical service → legacy pg_* engine → repository
Phase 2: implement domain service in src/domains/<name>/services/
Phase 3: redirect vertical service to domain service
Phase 4: retire legacy engine when tests pass
```
