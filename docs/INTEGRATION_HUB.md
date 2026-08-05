# Enterprise Integration Hub

**Sprint:** 28.0  
**Package:** `src/web/src/integration-hub/`  
**Constraint:** Extend existing stores — no redesign, no second platform.

## Purpose

Connect Desktop · Dashboard · Workspace · City · Production · Command Center · CRM · Settings into **one SPA operating system** with shared context, search, notifications, events, deep links, session restore, and runtime health.

## Architecture

```
Providers
  └── IntegrationHubBridge (useIntegrationBoot)
        ├── sessionCoordinator.restoreAll()
        ├── registerIntegrationSearch()
        ├── enterpriseEventBus.connectLiveBridge()
        └── useIntegrationContext.syncFromRoute(path)

Shared stores (existing)
  authStore · workspaceStore · workspaceManager · desktopStore
  liveDashboardStore · productionStore · notificationStore
  liveUpdates · searchIndex · contextEngine · useRuntimeHealth
```

## Capabilities

| Capability | Module |
|------------|--------|
| Shared context | `integrationContextStore.ts` |
| Event bus | `enterpriseEventBus.ts` → `liveUpdates` |
| Session restore | `sessionCoordinator.ts` |
| Universal search | `searchRegistration.ts` → `searchIndex` |
| Deep links | `types.ts` `OS_DEEP_LINKS` / `buildDeepLink` / `parseDeepLink` |
| Runtime health | `useIntegrationRuntimeHealth` (45s shared poll) |
| Notifications | Same `notificationStore` everywhere |

## Deep links

| Surface | Path |
|---------|------|
| Desktop | `/desktop` |
| Dashboard | `/dashboard` |
| Workspace | `/workspace` |
| City | `/enterprise-city?building=` |
| Production | `/production-studio?studio=` / `?tab=` |
| Command Center | `/command-center` |
| CRM | `/crm` |
| Settings | `/settings` |

All navigation is React Router SPA — **no full reloads**.

## Events

`navigate` · `open_module` · `open_city_building` · `open_production` · `ai_request` · `job_update` · `runtime_update` · `notification` · `context_changed` · `session_restored`

## Session keys (coordinated, not duplicated)

`ews_desktop_session_v1` · `ews_workspace_session_v1` · `ews_live_dashboard_v1` · `ews_ai_production_v1` · `ews_city_viewport_v1` · `ews_last_module_v1` · `ewp_session_v1`

---

## External Integration Hub (Sprint 33.1 + 31.2 deepen)

SPA OS bus above is **not** the external connector layer. External integrations live in:

| Layer | Path |
|---|---|
| UI Hub | `src/web/src/enterprise-integrations/` · `/integrations` |
| Provider registry | `providerRegistry.ts` + `platform_integrations/extended_provider_catalog.py` |
| n8n bridge | `n8nBridge.ts` + `platform_integrations/n8n_bridge.py` |
| Webhooks / queue / retry | `platform_integrations/` |
| Credentials | Enterprise Secrets Hub (`/api/enterprise-esh/v1`) |
| AI gateway | AI Provider Hub (`/api/enterprise-aph/v1`) |

**Hard rule:** Platform Runtime = system of record. n8n = external orchestration only — **no business logic in n8n**.

See also: `N8N_ARCHITECTURE.md`, `AI_PROVIDERS.md`, `PROVIDER_REGISTRY.md`, `WORKFLOW_LIBRARY.md`, `ENTERPRISE_INTEGRATION_HUB_33_1.md`, `SPRINT_31_2_RESULT.md`.

