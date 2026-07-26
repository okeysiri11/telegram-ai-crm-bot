# Ecosystem Reuse Matrix — Sprint 31.1

Measured by `computeReusePercentage()` — Automotive · Beauty · Cafe · Agriculture.

| Dimension | Auto | Beauty | Cafe | Agro | Shared |
|-----------|:----:|:------:|:----:|:----:|:------:|
| authentication … shared_permissions (17 rows) | ✓ | ✓ | ✓ | ✓ | ✓ |
| shared_commerce (ECO Beauty+Cafe; Agro marketplace) | — | ✓ | ✓ | — | ✓ (Beauty+Cafe) |

## Percentages

- **Platform reuse: 100%** (18/18 shared rows per audit rules)
- **Cross-ecosystem (all four): ~94.4%** (17/18 — commerce intentionally Beauty+Cafe; Agriculture uses grain marketplace)

## Shared APIs / components / AI / workflows / permissions / dashboards / notifications / telemetry

All map to existing ISAM, PermissionGuard, WorkspaceLayout, EDS, ecosystem-template, PB Concierge/AI Team/MC, Comms, OBS, Pilot `/pilot` — no duplicated infrastructure.
