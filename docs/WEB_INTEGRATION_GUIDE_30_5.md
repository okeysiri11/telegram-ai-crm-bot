# Web Integration Guide — Sprint 30.5

## Bootstrap

`Providers` → session restore → theme apply → `WebCoreProvider` → navigation + telemetry.

Contexts exposed via `useWebCore()`:

| Context | Source |
|---------|--------|
| Organization | `workspaceStore.company` / department / project |
| User | `authStore.user` |
| Navigation | `navigationManager.forTenant` |
| Permissions | workspace permissions + roleId |
| Theme | `themeStore.mode` |
| Modules | `moduleRegistry.healthSummary` |

## Identity → API

`apiFetch` attaches `Authorization`, `X-Tenant-Id`, `X-Organization`, `X-Workspace`, `X-Role-Id`.

## Observability

`telemetry` → `/api/enterprise-obs/v1` (logs, metrics, audit, AI, healthSnapshot).

## Shared UI

Use exports from `@/ui` and inventory in `sharedUi.ts`. Do not add parallel component libraries.

## Mission Control

Live panel probes MC status + OBS + module registry. Wizard steps unchanged (29.19 aggregation).

## Pilot

`/pilot` — first internal pilot readiness dashboard.
