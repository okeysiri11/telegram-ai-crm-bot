# Ecosystem Reuse Matrix — Sprint 30.9

Measured by `computeReusePercentage()` in `src/web/workspace/ecosystem-template/index.ts`.

| Dimension | Source | Automotive | Beauty | Shared |
|-----------|--------|:----------:|:------:|:------:|
| authentication | ISAM + platform JWT | ✓ | ✓ | ✓ |
| authorization_rbac | ISAM / PermissionGuard | ✓ | ✓ | ✓ |
| workspace | WorkspaceLayout + store | ✓ | ✓ | ✓ |
| mission_control | PB /mission-control | ✓ | ✓ | ✓ |
| knowledge | PB knowledge / EKG | ✓ | ✓ | ✓ |
| workflow_engine | ecosystem-template | ✓ | ✓ | ✓ |
| notification_system | enterprise-comms | ✓ | ✓ | ✓ |
| telemetry | OBS + pilotMetrics | ✓ | ✓ | ✓ |
| ai_platform | Concierge + AI Team | ✓ | ✓ | ✓ |
| ui | EDS components | ✓ | ✓ | ✓ |
| dashboards | Domain + /pilot | ✓ | ✓ | ✓ |
| layouts | WorkspaceLayout | ✓ | ✓ | ✓ |
| shared_apis | comms / OBS / PB / ISAM | ✓ | ✓ | ✓ |
| shared_components | EDS + template | ✓ | ✓ | ✓ |
| shared_workflows | timedStep template | ✓ | ✓ | ✓ |
| shared_ai | Concierge + AI Team + AMO | ✓ | ✓ | ✓ |

## Reuse percentage

**100%** (16/16 shared platform dimensions).

Domain-only APIs (BOS/BWS/BCJ vs Auto CRM) remain vertical-specific Hub ownership — not counted as duplication.
