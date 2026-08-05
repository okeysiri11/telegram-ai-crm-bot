# Core Services Layer

**Sprint:** 32.2 · Executable map: `platform_architecture/core_inventory.py`

## Inventory

| Service | Canonical | Vertical adapters (not SoR) |
|---|---|---|
| Event Bus | `events.event_bus.PlatformEventBus` | domain buses (TD-20) |
| Workflow Runtime | `platform_workflow/` | TS kernel workflow, web `workflowRuntime` (TD-22/48) |
| Notification Service | `platform_communications_hub` + `services/notification_center.py` | Auto `notifications/` (TD-53) |
| Search Service | `services/search_service.py` | Auto `search/` |
| Permission Engine | `platform_security/permission_engine/` | Auto auth; web spatial/asset scopes (TD-52) |
| Catalog Engine | marketplace / `business_ecosystem/catalogs.py` | vertical catalogs |
| Pricing Foundation | `services/pricing_engine.py` + `services/pricing_foundation.py` | Auto `pricing/` (TD-61) |
| Identity | `platform_identity/` | Auto `authentication/` |
| AI Provider Hub | `platform_enterprise_ai_provider_hub` | — |
| Agent Runtime (web) | `src/web/src/enterprise-runtime/` | — |

## Rules

1. New platform capability → extend the row above or add to inventory with an owner path.
2. Verticals call Core via bridges/APIs — no copy-paste of engines into Auto.
3. Duplicate scan / ownership checks: `scripts/architecture_sprint_review.py`.

## Auto boundary

```
applications/auto_marketplace/
  integrations/platform_bridge.py   # allowed bridge
  authentication/ notifications/ search/ pricing/   # adapters only until migrated
```

Forbidden: second Event Bus, Permission Engine, Notification Center, or Pricing Engine as system of record.
