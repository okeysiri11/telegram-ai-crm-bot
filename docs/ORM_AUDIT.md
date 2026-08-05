# ORM Audit — Sprint 37.1

**Date:** 2026-08-04

---

## Inventory

| Metric | Value |
|--------|------:|
| Model modules loaded | ≥100 (`load_all_models`) |
| Tables in `Base.metadata` | ~375+ |
| Tables with VersionMixin `version` column | **375** declared |
| Live PG tables with `version` after backfill | **376** |

---

## Mixins

| Mixin | Purpose | Status |
|-------|---------|--------|
| `UUIDPrimaryKeyMixin` | UUID `id` PK | OK |
| `TimestampMixin` | `created_at` / `updated_at` | OK |
| `VersionMixin` | optimistic lock + provenance | Backfilled on live DB |

VersionMixin fields: `version`, `change_id`, `source_client`, `workspace_id`, `created_by`, `updated_by`, `metadata_json`.

---

## Consistency checks

| Check | Result |
|-------|--------|
| Duplicate `__tablename__` across models | None found (prior audit) |
| Audit ORM has VersionMixin | Yes — now matched in DB |
| UUID strategy | UUID PK via mixin |
| Optimistic locking | Integer `version` default 1 |
| JSONB usage | Widespread; Postgres-native |
| Soft delete | Not universal; feature-specific status enums (accepted) |
| Cascade rules | Mostly application-level; few hard ON DELETE CASCADE |

---

## Name collision fixed

`SkillVersionRow.version` (semver string) conflicted with `VersionMixin.version` (int).

**Fix:** business field renamed to `semver` in ORM + Alembic `r1l` / unique constraint `uq_skill_versions_skill_semver`. Same for `InstalledSkillRow.semver`.

In-memory Skills SDK service unchanged (dataclass API).

---

## Engine / sessions / UoW

| Component | Location | Status |
|-----------|----------|--------|
| AsyncEngine | `database/engine.py` | pool_size=20, max_overflow=40, pool_pre_ping |
| Sync URL | `get_sync_database_url()` | for Alembic |
| POSTGRES_ONLY | `database/__init__.py` | blocks `database_legacy` |
| Repositories | `repositories/` | PG services preferred |
| Unit of Work | session-per-request / service patterns | adequate for control plane |

---

## Remaining ORM debt

| Priority | Item |
|----------|------|
| P1 | Add selective DB FKs where string keys imply relations |
| P2 | Create missing physical tables for unused ORM modules |
| P2 | Standardize soft-delete mixin if product requires it globally |
| P3 | Expand `__all__` exports for discoverability |
