# Platform Technical Debt Register

> Generated: 2026-07-19 13:07:17 UTC

## P0 — Blocks Certification


## P1 — Sprint 2

- Legacy pg engine dependency cycles (47)
- Handler DB direct access (4 allowlisted files)
- WorkflowEngine name collision (legacy adapter alias)
- Event bus direct crm_event_bus imports in pg engines

## Deferred with Justification

Legacy `services/pg_*` cycles are contained in compatibility layer.
Removing them requires Sprint 2 adapter extraction without business logic change.

