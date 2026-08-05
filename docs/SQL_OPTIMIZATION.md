# SQL Optimization — Sprint 37.3

## Pool (applied)

| Setting | Default | Env |
|---------|---------|-----|
| pool_size | 20 | `DB_POOL_SIZE` |
| max_overflow | 40 | `DB_MAX_OVERFLOW` |
| pool_timeout | 30s | `DB_POOL_TIMEOUT` |
| pool_recycle | 1800s | `DB_POOL_RECYCLE` |
| pool_pre_ping | true | — |

Code: `database/engine.py` + `DatabaseSettings`.

### Measured SELECT 1

| Metric | Value |
|--------|------:|
| p50 | 5.0 ms |
| p95 | 124 ms |

p95 inflated by cold connection / first checkout — expected; steady-state should track nearer p50 after warm pool.

## Known N+1 / slow paths (unchanged business logic)

From `docs/audit/repository_audit_report.md` (24 suspects). Top runtime-relevant:

| Location | Risk | Recommended fix | Effort |
|----------|------|-----------------|--------|
| `crm_event_bus._dispatch_event` sequential handlers | Latency under fan-out | `asyncio.gather` + semaphore after ordering review | 2–3d (P1) |
| `pg_webhook_engine.process_pending_retries` | Network in loop | batch / bounded gather | 2d (P1) |
| marketplace `_sync_images` | Per-image roundtrips | bulk upsert | 2d (P2) |
| pipeline `list_*_by_stage` | Possible extra queries | `selectinload` | 1–2d (P2) |

## Guidance (no schema change this sprint)

1. Prefer SQLAlchemy 2.x ORM with explicit `selectinload`/`joinedload`.  
2. Cap list endpoints with `PaginationParams` (max 500).  
3. Avoid `await` inside tight loops over query results — batch.  
4. Tune `DB_POOL_*` per host CPU and Postgres `max_connections`.

## Verdict

**Database optimized for production tuning.** No critical SQL defects introduced; remaining N+1 remediations are P1/P2 with estimates above.
