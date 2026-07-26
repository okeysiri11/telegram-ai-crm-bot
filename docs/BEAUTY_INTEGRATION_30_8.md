# Beauty Integration Guide — Sprint 30.8

Beauty connects to existing Hub + Platform Builder surfaces. It does **not** invent parallel CRM, auth, or AI stacks.

## Domain APIs (already mounted)

| Suite | Prefix | Role |
|-------|--------|------|
| Beauty OS (Salon CRM) | `/api/enterprise-bos/v1` | Company, employees, services, customers, appointments, owner dashboard |
| Beauty Workspace | `/api/enterprise-bws/v1` | Calendar/schedule, reception dashboard, notifications, assistant |
| Beauty Client Journey | `/api/enterprise-bcj/v1` | Availability, smart book, journey, waitlist, loyalty, booking assistant |
| AI Marketing OS | `/api/enterprise-amo/v1` | Shared marketing bootstrap (not Beauty-only) |

## Shared platform (required)

| Capability | Source |
|------------|--------|
| Authentication | ISAM + platform JWT (`/login`, identityApi) |
| Authorization / RBAC | ISAM roles · PermissionGuard |
| Workspace | WorkspaceLayout · workspaceStore · moduleRegistry |
| Mission Control | PB `/mission-control` |
| Knowledge | PB knowledge / EKG |
| Workflow engine | `workspace/ecosystem-template` timed steps |
| Notifications | enterprise-comms `/center` |
| Telemetry | OBS + pilotMetrics |
| AI | PB Concierge sessions (same as Automotive) |

## Web wiring

- Config: `webConfig.beautyOsPrefix` / `beautyWorkspacePrefix` / `beautyClientJourneyPrefix` / `aiMarketingOsPrefix`
- Hub: `hubIntegrations.beautyOs` (+ bws/bcj/amo)
- Route: `/workspace/beauty` → `BeautyLiveWorkflowPage`
- Registry: `moduleRegistry.beauty` with apiHint for BOS/BWS/BCJ

## Do not

- Fork Automotive modules  
- Duplicate Concierge / Comms / OBS endpoints  
- Add Beauty-only auth  
- Redesign Mission Control  
