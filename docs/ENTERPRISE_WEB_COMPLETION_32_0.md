# Enterprise Web Completion — Sprint 32.0

## Scope

Audit and strengthen existing web surfaces for seven ecosystems. **No new Business Ecosystems.**

## Workspace audit

| Route | Page | Nav | Loading | Empty | Error | Forms/Tables | Dashboard link |
|-------|------|-----|---------|-------|-------|--------------|----------------|
| `/workspace/auto` | AutomotiveLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/beauty` | BeautyLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/cafe` | CafeLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/agro` | AgricultureLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/legal` | LegalLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/crypto` | BidexLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |
| `/workspace/drone` | DroneLiveWorkflowPage | OK | busy | EmptyState | EmptyState | Table | MC + Pilot |

Shared: `WorkspaceLayout` → `FullLayout` (responsive), Sidebar mobile drawer, `PermissionGuard` / `ProtectedRoute`, EDS `EmptyState` / `Table` / `Badge`.

## Mission Control

- Live panel probes MC status + OBS + **per-ecosystem domain `/health`**
- Links: Pilot Dashboard, Production Readiness
- Sprint badge tracks Platform Builder sprint

## Production surface

- Route: `/pilot/production`
- Hub prefix: `/api/enterprise-epd/v1`
- Probes: workspace health, EPD health/dashboard/gate, EPR, ISAM, OBS, MC
- Checklist + pilot ops steps + shared UI inventory

## Explicit non-goals

- No 8th ecosystem
- No duplicated APIs / AI / services / routing
- No LiveWorkflow shell refactor (documented debt only)
- No pilot invitation product in 32.0
