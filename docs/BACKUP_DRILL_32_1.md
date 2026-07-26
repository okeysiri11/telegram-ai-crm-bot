# Backup Drill Checklist — Sprint 32.1

Uses existing endpoints only — no new backup engine.

## Drill

1. Confirm ERL health: `GET /api/enterprise-erl/v1/health`
2. Optional dry-run: `POST /api/enterprise-erl/v1/disaster-recovery` (per ERL docs)
3. Optional Auto backup: `POST /api/auto/v1/ops/backups` (if Auto ops enabled)
4. Optional EMR: `POST /api/enterprise-emr/v1/backup`
5. Record timestamp, operator, and result in the ops log
6. Restore verification: follow `docs/EMR_BACKUP_RESTORE_ROLLBACK.md` / `docs/BACKUP_GUIDE.md` on a non-prod clone

## Status

Documented drill = **partial** production readiness (automation of recurring drills deferred).
