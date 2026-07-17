# Routing

How users enter the platform and get routed to the correct vertical, role, and flow.

## Entry points

| Source | Handler / router | Engine |
|--------|------------------|--------|
| `/start` | `start_routing_handlers.py` | `EntryPointEngineV1`, `VerticalOnboardingEngineV1` |
| Deep links | `vertical_onboarding_handlers.py` | `LeadEngineV1.ingest_from_deep_link` |
| Auto client menu | `routers/auto_client_router.py` | `AutoClientFlow` FSM |
| Auto dealer | `routers/auto_dealer_router.py` | `AutoDealerFlow` FSM |
| Auto hub services | `routers/auto_hub_router.py` | Category routing (insurance, legal, logistics) |
| Tenant guard | `tenant_guard_handlers.py` | Tenant/module access |

## Entry link registry

Configured in `services/tenant_routing.py` → `ENTRY_LINK_REGISTRY`:

| Link code | Vertical | Role preset |
|-----------|----------|-------------|
| `auto_client` | auto | CLIENT |
| `auto_dealer` | auto | dealer flow |
| `agro` / `agro_farmer` / `agro_supplier` | agro | varies |
| `legal` | legal | CLIENT |
| `drones` | agro | — |

Legacy links (`finance`, `crypto`, `cafe`, `beauty`) remain for backward compatibility.

## Router registration order

Defined in `startup.py` — order matters for handler precedence:

1. `routers/auto_client_router`
2. `routers/auto_dealer_router`
3. `routers/client_history_router`
4. `routers/manager_crm_router`
5. `routers/manager_debug_router`
6. `routers/auto_hub_router`
7. `auto_vertical_handlers`
8. `handlers` (legacy mega-router)

## Flow context

`EntryPointEngineV1` persists active flow per user:

- Blocks cross-flow navigation (middleware restores FSM state)
- Tracks `source_link`, vertical, language
- Used by auto client router for entry gating

## Manager vertical routing

`VerticalRoutingEngineV1.resolve_manager_for_vertical(vertical)`:

1. Check manager vertical subscriptions
2. Fall back to role defaults (`ROLE_DEFAULT_VERTICALS`)
3. Fall back to configured default manager IDs

## Middleware

| Middleware | Purpose |
|------------|---------|
| `entry_point_middleware` | Prevent accidental flow switches; restore Auto Client FSM |
| `tenant_middleware` | Scope requests to tenant context |

## HTTP API routing

- Health: `/health`, `/ready`, `/metrics`
- CRM REST: `api/handlers.py` (deals, documents, notifications)
- Gateway v1: `api/v1/` (scaffold, 501 routes)

## Adding a route

**Telegram (preferred):**

1. Create `routers/<feature>_router.py` or `*_handlers.py`
2. Register in `startup.py` **before** legacy `handlers`
3. Call vertical service or `pg_*` engine — never open DB session

**HTTP:**

1. Add handler in `api/handlers.py` or `api/v1/`
2. Delegate to service engine
3. Register route in `api/server.py`
