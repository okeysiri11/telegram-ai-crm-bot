# Schema Validation — Sprint 37.1

**Date:** 2026-08-04  
**Database:** PostgreSQL (`ai_ecosystem`)  
**Alembic:** `u4o567890123`

---

## Validation matrix

| Area | Method | Result |
|------|--------|--------|
| Indexes | Spot-check + IF NOT EXISTS backfill indexes | OK |
| Unique constraints | Present on service/skill/campaign keys | OK |
| Foreign keys | Soft keys dominant; few hard FKs | Accepted (P1 to harden) |
| Cascade | App-level | Accepted |
| Nullable | Mixins nullable provenance fields | OK |
| JSONB | Postgres JSONB throughout 36–37 | OK |
| Enums | Mostly VARCHAR status fields (not PG ENUM) | OK / intentional |
| Audit tables | VersionMixin columns present | **PASS** |
| Soft delete | Status enums / archive flags | Feature-specific |
| Timestamps | `created_at`/`updated_at` timezone-aware | OK |
| VersionMixin | 376 tables with `version` | **PASS** |
| UUID PK | UUID columns | OK |
| Optimistic locking | Integer `version` | OK |

---

## Audit tables (Enterprise Audit C2)

| Table | `version` | `change_id` | Notes |
|-------|:---------:|:-----------:|-------|
| `audit_log` | ✅ | ✅ | Platform audit |
| `audit_events` | ✅ | ✅ | Event audit |
| `audit_engine_logs` | ✅ | ✅ | Engine audit |
| `trust_security_engine_v1_permission_audits` | ✅ | ✅ | Security |

---

## Control-plane tables (sample)

| Table | Present | VersionMixin |
|-------|:-------:|:------------:|
| `platform_registry` | ✅ | ✅ |
| `platform_sessions` | ✅ | ✅ |
| `platform_metrics` | ✅ | ✅ |
| `platform_health` | ✅ | ✅ |
| `platform_usage` | ✅ | ✅ |
| `platform_configuration` | ✅ | ✅ |
| `creative_assets` | ✅ | ✅ |
| `skills` / `skill_versions` | ✅ | ✅ (`semver` business col) |

---

## Performance notes

- Connection pool: size 20 / overflow 40 / `pool_pre_ping`  
- Backfill used set-based `ALTER … IF NOT EXISTS` (no row rewrites beyond defaults)  
- Formal load test suite not expanded this sprint (P2)  
- N+1: repository patterns unchanged; no API changes  

---

## Inconsistencies remaining

| Priority | Item |
|----------|------|
| P1 | Soft FK graph not enforced in PG |
| P2 | Historical `audit_logs` vs `audit_log` naming |
| P2 | ORM-only tables without physical DDL |
| P3 | Mixed use of PG ENUM vs VARCHAR |
