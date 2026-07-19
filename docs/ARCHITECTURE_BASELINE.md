# Architecture Baseline — Platform Core v1.0.0-rc1

> Frozen baseline generated 2026-07-19 12:25:41 UTC

## Scores

- **Architecture grade:** PASS
- **Architecture score:** 99.5/100
- **Quality gates:** PASS

## Graph Metrics

| Metric | Value |
|--------|------:|
| Modules | 804 |
| Dependency edges | 2620 |
| Strict governed cycles | 0 |
| Layer violations | 70 |

## Baseline Artifacts

- docs/architecture_baseline/MODULE_GRAPH.md
- docs/architecture_baseline/DEPENDENCY_GRAPH.md
- docs/architecture_baseline/IMPORT_GRAPH.md
- docs/architecture_baseline/SERVICE_GRAPH.md
- docs/architecture_baseline/graph.json

## Platform Contracts

- Management API: `/management/v1` (JWT/API key required)
- Public API: `/api/v1` (frozen contract)
- Event bus: `PlatformEventBus` + `events/crm_publisher.py` for CRM outbox
- SDK: `platform_sdk/` → public services only (no repository/database)
