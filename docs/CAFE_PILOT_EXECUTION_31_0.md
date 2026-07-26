# Cafe Pilot Execution — Sprint 31.0

**Version:** Platform Builder **v1.35.0** · Sprint **31.0** · **Cafe Pilot Execution**  
**Rule:** Third operational pilot on shared Enterprise Platform — no redesign, no forks of Auto/Beauty.

## Pre-implementation validation

| Capability | Exists? | Action |
|------------|---------|--------|
| Auth / RBAC / Workspace / MC / AI Team / Comms / OBS | Yes | Reuse |
| ECO payments / loyalty / POS | Yes | Reuse |
| Cafe domain Hub suite | **No** (catalog-only) | **Thin Cafe OS** `/api/enterprise-cos/v1` — additive overlay; does not fork Beauty |
| Automotive / Beauty workflows | Yes | **Unchanged** |

## Demonstrable UI

| Surface | Route |
|---------|-------|
| Cafe pilot | `/workspace/cafe` |
| Beauty (unchanged) | `/workspace/beauty` |
| Automotive (unchanged) | `/workspace/auto` |
| Pilot Dashboard | `/pilot` |

## Docs

| Doc | Path |
|-----|------|
| Integration Guide | [CAFE_INTEGRATION_31_0.md](./CAFE_INTEGRATION_31_0.md) |
| Workflow | [WORKFLOW_CAFE_31_0.md](./WORKFLOW_CAFE_31_0.md) |
| Reuse Matrix | [ECOSYSTEM_REUSE_MATRIX_31_0.md](./ECOSYSTEM_REUSE_MATRIX_31_0.md) |
| Pilot Guide | [CAFE_PILOT_GUIDE_31_0.md](./CAFE_PILOT_GUIDE_31_0.md) |
| Production Status | [PRODUCTION_STATUS_31_0.md](./PRODUCTION_STATUS_31_0.md) |
| Release Notes | [RELEASE_NOTES_31_0.md](./RELEASE_NOTES_31_0.md) |
| Sprint Report | [SPRINT_REPORT_31_0.md](./SPRINT_REPORT_31_0.md) |
