# Ecosystem Reuse Matrix — Sprint 30.8

Automotive is the reference implementation. Beauty configures domain APIs on the same platform capabilities.

| Capability | Source | Automotive | Beauty |
|------------|--------|:----------:|:------:|
| Authentication | ISAM + platform JWT | ✓ | ✓ |
| Authorization / RBAC | ISAM roles / PermissionGuard | ✓ | ✓ |
| Workspace | WorkspaceLayout + workspaceStore | ✓ | ✓ |
| Mission Control | PB `/mission-control` | ✓ | ✓ |
| Knowledge | PB knowledge / EKG | ✓ | ✓ |
| Workflow engine | ecosystem-template timed steps | ✓ | ✓ |
| Notification system | enterprise-comms `/center` | ✓ | ✓ |
| Telemetry | OBS + pilotMetrics | ✓ | ✓ |
| AI platform | PB Concierge sessions | ✓ | ✓ |
| UI | EDS Button/Card/Table/Input | ✓ | ✓ |
| Dashboards | Domain + Pilot `/pilot` | ✓ | ✓ |

## Domain-only (configured, not duplicated)

| Domain | Automotive | Beauty |
|--------|------------|--------|
| CRM / leads | `/api/auto/v1` CRM | BOS customers + BCJ journey |
| Appointments / calendar | N/A (tasks/timeline) | BOS appointments + BWS schedule |
| Portal auth | Auto portal register/login | Staff session + CRM client record |
| Marketing | — | Shared AMO health/bootstrap |

## Reuse percentage

Shared platform rows: **11/11** for both ecosystems.  
Domain surfaces remain vertical-specific APIs already owned by Enterprise Hub — no new stacks.

Code mirror: `ECOSYSTEM_REUSE_MATRIX` in `src/web/workspace/ecosystem-template/index.ts`.
