# Platform Technical Debt Register

> Generated: 2026-07-18 13:53:32 UTC

## P0 — Blocks Certification

- Repository → Service imports (6 files)
- SDK → Repository/Database access in platform_sdk/
- 17 unauthenticated admin HTTP routes
- No GitHub Actions workflow
- README stale vs implementation

## P1 — Sprint 2

- Legacy pg engine dependency cycles (44)
- Handler DB direct access (4 allowlisted files)
- WorkflowEngine name collision (legacy adapter alias)
- Event bus direct crm_event_bus imports in pg engines

## Deferred with Justification

Legacy `services/pg_*` cycles are contained in compatibility layer.
Removing them requires Sprint 2 adapter extraction without business logic change.

