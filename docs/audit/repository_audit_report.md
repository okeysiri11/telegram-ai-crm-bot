# Repository Audit Report

**Date:** 2026-07-15  
**Scope:** Full static audit of TelegramBotCourse  
**Mode:** Analysis + recommended fixes only (no feature expansion)

---

## Executive summary

The product core (Auto Client → manager delivery → CRM pipeline) works, but the repository has accumulated **layers of parallel engines** (RBAC ×3, inventory ×3, events ×3, notifications ×2, storage ×2). Rough scale:

| Metric | Value |
|--------|------:|
| Python LOC (approx, excl. venv) | ~73k+ |
| `database/models` classes | ~530 |
| `services/*.py` | ~204 |
| `repositories` | ~99 |
| Root `*handlers.py` | 24 |
| Modular `routers/` | 6 active |

**Recommendation:** stop Mega Tasks 1–10 feature expansion until P0–P2 hygiene below is done. Scaffold for domains/API already exists under `src/` — migrate behind it incrementally.

---

## 1. Dead / unused code

### 1.1 Models never referenced outside defining file (23)

Examples (static name scan — may still be used only via Alembic/metadata):

| Class | File |
|-------|------|
| `AiAgent`, `AiDialog`, `AiAgentMemory`, `AiAgentSetting` | `database/models/ai_agents.py` |
| `CommissionRule` | `database/models/commissions.py` |
| `DealAgroExt`, `DealAutoExt`, `DealDroneExt`, … | `database/models/deals.py` |
| `DealEngineDeal` | `database/models/deal.py` |
| `FinanceAccount` | `database/models/finance.py` |
| `PartnerKpi` | `database/models/partners.py` |
| `AutomotivePartnerPayout` | `database/models/automotive_revenue_engine.py` |

**Fix:** mark `# LEGACY — candidate for archive` for one sprint; delete only after Alembic + mapper audit confirms no FK dependents.

### 1.2 Handlers with weak registration

| Module | External refs | Status |
|--------|--------------:|--------|
| `automotive_treasury_handlers.py` | **0** | Likely **dead router** (engine used elsewhere; handler router unused) |
| Most other `*_handlers.py` | 1–6 | Pulled via `handlers.py` includes |
| `handlers.py` | 61 | Live mega-router |

**Fix:** either `include_router(automotive_treasury_router)` where intended, or delete/archive the empty router file.

### 1.3 Routers (`routers/`)

All 6 feature routers are registered in `startup.py` ✅

### 1.4 Scaffold duplication (intentional for now)

`src/platform/{storage,notifications}` duplicates `services/storage` and `services/notification_center`. Acceptable during strangler phase; **do not grow both**.

---

## 2. Duplication (high cost)

| Concern | Live copies | Risk |
|---------|-------------|------|
| RBAC | `permission_engine_*`, `rbac_v2_*`, `database/models/permissions.py`, hierarchical RBAC | Mapper conflicts, wrong grants |
| Events | `events.py`, `crm_event_bus.py`, `src/events/` | Missed subscribers |
| Notifications | `notification_center.py`, `src/platform/notifications`, legacy `notifications.py` | Split delivery |
| Storage | `services/storage`, `src/platform/storage` | Config drift |
| Inventory | automotive vehicles / `inventory` / `marketplace_listings` / lead marketplace | Confused product semantics |
| SLA | `pg_sla_tracking_v1` vs `pg_lead_sla_engine` | Split metrics |
| Audit | `audit_engine_logs` vs `audit_log` | Incomplete trail |
| Class name collisions | `Permission`, `RolePermission`, `Partner`, `Notification`, `SettlementStatus`, `MarketplaceListingStatus`, … | SQLAlchemy / import bugs |

### Critical naming collision

`services/pg_automotive_revenue_engine.py` defines **`class LeadEngineV1`** and **`class DealEngineV1`**, colliding with:

- `services/pg_lead_engine.py::LeadEngineV1`
- `services/pg_deal_engine_v1.py::DealEngineV1`

Any careless `from services.pg_automotive_revenue_engine import LeadEngineV1` silently binds the wrong type.

**Fix (P0):** rename to `AutomotiveRevenueLeadRecorder` / `AutomotiveRevenueDealRecorder` (or nest under `AutomotiveRevenueEngineV1`).

---

## 3. Cyclic / fragile dependencies

| Pair | Issue |
|------|--------|
| `routers.auto_client_router` ↔ `routers.auto_hub_router` | Cross-router imports |
| `handlers.py` → many routers → services → lazy imports back | Opaque graph |
| Widespread `from services.X import Y` inside methods | Hides cycles; hard to refactor |
| Root `events.py` vs package `events/` | Name clash → scaffold correctly placed in `src/events/` |

**Fix:** extract shared Auto Client navigation helpers to `services/auto_client_navigation.py` (no router→router imports).

---

## 4. Unused imports

Not exhaustively auto-fixed (would require ruff). Recommended:

```bash
.venv/bin/pip install ruff
.venv/bin/ruff check . --select F401,F841 --output-format=concise
```

Expect heavy noise in `handlers.py`, `database_legacy.py`, test suites.

---

## 5. Race conditions / in-memory state

Global mutable dicts (lost on restart, unsafe with multiple workers):

| Location | State |
|----------|--------|
| `auto_vertical_handlers.py` | `auto_vertical_flow`, `auto_vertical_active`, `auto_billing_flow`, `auto_vertical_section` |
| `lead_engine_handlers.py` | `lead_assign_flow` |
| `cart_engine_handlers.py` | `cart_sessions`, `pending_checkout` |
| `payment_engine_state.py` | `pending_payment_upload` |
| `automotive_partner_handlers.py` | `partner_lead_flow` |
| `owner_*_handlers.py` | edit flows |
| `services/tenant_context.py` | `_active_tenant_by_user` |

**Also:** escalation background loop + multi-process bot would double-fire without distributed lock.

**Fix:** move flows to Redis FSM / Redis hashes; use Redis lock for escalation (`SET escalation:lock NX EX 55`).

---

## 6. Blocking operations inside async

Automated `time.sleep` / `requests.*` in `async def` scan: **0 hits** (good).

Remaining latency risks (async but **blocking UX**):

| Area | Issue |
|------|--------|
| `pg_ai_manager_engine` → OpenRouter on lead finish | Can stall request confirmation seconds–tens of seconds |
| New Bot session per manager notify | Session churn |
| Escalation / SLA notify loops | Sequential Telegram sends |

**Fix:** queue AI qualification + optional notifies via scheduler/worker; share Bot instance.

---

## 7. SQL indexes / N+1

### Indexes (CRM path)

`client_requests`, `auto_client_requests_v1`, `inventory`, `lead_sla_records` — **indexed** on primary filters ✅

Gaps / watch list:

| Risk | Note |
|------|------|
| Composite filters on inventory search | brand+model+price+status may need composite later |
| `lead_sla_records` scan for escalation | filter `closed_at IS NULL AND first_response_at IS NULL` — consider partial index |
| JSONB `photo_file_ids` | no GIN (usually OK) |

### Await-in-loop suspects (24)

Notably:

- `services/crm_event_bus.py::_dispatch_event`
- `services/pg_webhook_engine.py::process_pending_retries`
- `services/pg_automotive_marketplace_engine.py::_sync_images`
- Several repository seed helpers (acceptable at boot)

**Fix:** batch webhook retries; gather with concurrency limit; prefer bulk inserts for seeds.

---

## 8. Secrets / security

| Finding | Severity |
|---------|----------|
| `.env` gitignored ✅ | OK |
| Real `BOT_TOKEN` + `OPENROUTER_API_KEY` present in local `.env` | Expected locally |
| Duplicate `BOT_TOKEN` / key lines in `.env` | Confusing; last wins via dotenv |
| `JWT_SECRET` default `change-me-in-production` | API auth weak if enabled |
| `REDIS_REQUIRED=false` | Silent FSM loss on Redis down |
| Secrets appeared in agent tooling context | **Rotate Telegram bot token and OpenRouter key** if this workspace is shared / logged |

**Do not commit** `.env`, `.env.production` with real tokens. Prefer secrets manager in prod.

---

## 9. FSM state loss risks

| Risk | Mechanism |
|------|-----------|
| MemoryStorage fallback | `fsm_storage.py` when Redis unavailable |
| `REDIS_REQUIRED=false` | Restart → mid-flow users drop to menu / wrong state |
| Auto-client pending restore | Relies on `onboarding_step` + `AUTO_CLIENT_PENDING_RESTORE` — better than pure memory, but incomplete for multi-step field bag |
| In-memory vertical VIN flows | Lost on restart mid-VIN |
| Photo album collector in-process | Media group buffer lost on process restart |

**Fix:** `REDIS_REQUIRED=true` in prod; persist draft payload JSON with pending key; persist vertical flows in Redis.

---

## 10. God classes / coupling

| File | Lines | Action |
|------|------:|--------|
| `database_legacy.py` | ~11142 | Freeze; quarantine |
| `handlers.py` | ~5080 | Split by include already started — continue extraction |
| `keyboards.py` | ~2019 | Split per vertical |
| `auto_vertical_handlers.py` | ~1256 | FSM → Redis; split screens |
| Large `pg_*` engines | 700–1050 | One concern per module |

---

## 11. Mega Tasks 1–10 vs reality

Much of Mega Tasks **already partially exists** as parallel implementations:

| Mega task | Already present (partial) | Gap |
|-----------|---------------------------|-----|
| Tests | Several `*_test.py` / regression scripts | No unified 70% coverage / pytest |
| OpenAPI | `api/crm_api.py` + `api/v1` scaffold | Not full RBAC gateway |
| Marketplace | `inventory` + listing + recommend | Product polish |
| Multi-tenant | `multi_tenant_foundation`, partner tenant | Not enforced on Auto Client CRM rows |
| Financial | revenue / commission engines | Naming collisions, incomplete P&L UX |
| AI qualification | `pg_ai_manager_engine` | No manager recommendation / probability |
| Recommendations | marketplace + `pg_recommendation_engine` | Two systems |
| Monitoring | `/metrics`, prometheus compose | Loki not present |
| Deploy | `docker-compose.prod.yml`, nginx, backups | Needs ops hardening |
| Docs | `docs/*` | Diagram generators not automated |

**Do not stack another parallel mega-engine.** Extend the surviving one.

---

## Proposed fix plan (ordered)

### P0 — Safety (this week)

1. **Rotate** Telegram `BOT_TOKEN` and OpenRouter key (exposed in tooling).
2. Clean `.env` duplicates; set `REDIS_REQUIRED=true` for prod intent.
3. Rename colliding `LeadEngineV1` / `DealEngineV1` inside `pg_automotive_revenue_engine.py`.
4. Confirm `automotive_treasury_handlers` delete or register.

### P1 — Stability (1–2 weeks)

5. Move `auto_vertical_flow*` and sibling dict flows → Redis.
6. Escalation distributed lock.
7. Time-box / background AI qualification on lead submit.
8. Extract `auto_client_navigation` to break router cycle.
9. Run `ruff` F401 sweep on `routers/` + new services only.

### P2 — Consolidation (2–4 weeks)

10. Single notification + storage import path (prefer `services/*`, re-export from `src` or vice versa).
11. Single RBAC system of record = `permission_engine_*`.
12. Dual-write domain events (`src.events`) from CRM submit; retire duplicates later.
13. Add partial index for open SLA rows; concurrency limit on webhook retries.
14. Freeze `database_legacy.py` / stop new features there.

### P3 — Platform (after hygiene)

15. Wire `api/v1` to **existing** engines (not new ones).
16. Tenant columns on `client_requests` + query filters.
17. Unified pytest suite with coverage gate — target 70% on **crm/marketplace** packages only first (not whole 73k LOC).

---

## Suggested immediate patches (smallest diff)

```text
1) Rename revenue engine inner classes (avoid LeadEngineV1 collision)
2) Register or delete automotive_treasury_router
3) .env hygiene + REDIS_REQUIRED
4) auto_client shared navigation module (breaks cycle)
```

No FSM behavior change required for (1)–(3).

---

## Verification commands

```bash
# duplicate class names / quick health
PYTHONPATH=. python -c "from services.pg_lead_engine import LeadEngineV1; print(LeadEngineV1)"
PYTHONPATH=. python -c "import services.pg_automotive_revenue_engine as m; print(m.LeadEngineV1)"

# unused imports (install ruff)
ruff check routers services/pg_auto_client_request_engine.py services/pg_client_request_crm_engine.py --select F401

# FSM storage mode
grep REDIS_ .env
```

---

## Conclusion

The honest next step is **hygiene and consolidation**, not Mega Tasks 1–10. The architecture scaffold (`src/domains`, `container.py`, docs) already provides a strangler path. Use it to absorb living systems; delete ghosts (`unused models`, empty treasury router, duplicate class names) before adding another marketplace/financial/AI layer.
