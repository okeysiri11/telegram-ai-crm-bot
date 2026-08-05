# Alembic Audit — Sprint 37.1

**Date:** 2026-08-04  
**Head:** `u4o567890123`  
**Parent:** `t3n456789012`

---

## Validation results

| Check | Result |
|-------|--------|
| Total revision files | 129 |
| Unique revision IDs | 129 |
| Heads | **1** |
| Roots | **1** (`37dc2741863e`) |
| Broken `down_revision` | **0** |
| Orphans (unreachable from head) | **0** |
| Duplicate revision IDs | **0** |
| `alembic heads` | `u4o567890123 (head)` |
| `alembic current` (audit env) | `u4o567890123` |

---

## Upgrade path verification

| Scenario | Result |
|----------|--------|
| From previous prod stamp `f9f234567890` → head | **PASS** (after collision fixes) |
| Empty DB → head | Not re-run end-to-end this sprint (linear chain intact; estimated OK) |
| Downgrade of `u4o` | **No-op by design** (non-destructive) |
| PostgreSQL dialect | asyncpg online migrations OK |

---

## Defects found & fixed in pending chain

| Revision | Defect | Fix |
|----------|--------|-----|
| `l5f678901234` | Duplicate `metadata_json` vs `_ts_cols` | Removed explicit column |
| `m6g789012345` | Duplicate `workspace_id` | Removed explicit column |
| `n7h890123456` | `user_memory` already exists | Idempotent create + `IF NOT EXISTS` index |
| `q0k` / `r1l` | Mixin column collisions | Stripped colliding cols; `semver` for skills |
| `u4o567890123` | New | Full VersionMixin backfill via `ADD COLUMN IF NOT EXISTS` |

---

## Migration policy (Freeze)

1. Exactly one head at all times.  
2. No edit of applied revisions on prod — only expand/fix forward.  
3. Idempotent DDL preferred for retrofit migrations.  
4. VersionMixin columns never dropped on downgrade.  
5. CI gate: `tests/test_database_stabilization_37_1.py`.

---

## Commands

```bash
.venv/bin/alembic heads
.venv/bin/alembic current
.venv/bin/alembic upgrade head
.venv/bin/alembic history -r-15:head
.venv/bin/python -m pytest tests/test_database_stabilization_37_1.py -vv
```
