# Enterprise Freeze Checklist v1.0

**Purpose:** Gate the ADOS Enterprise Platform Freeze after Sprint 37.0.  
**Scope of Freeze:** Sprint **36.0–37.0** control plane + documented adapters.  
**Out of scope (quarantined):** Historical vertical version-gate tests, non-canonical EventBuses, deprecated workflow/memory duplicates (until migrated).

**Related:** `docs/ENTERPRISE_AUDIT_1_0.md` · `docs/PRODUCTION_READINESS.md` · `docs/TECHNICAL_DEBT_REPORT.md`

---

## Freeze definition

When checked, the platform kernel is **frozen**:

- No new parallel SoR packages (`platform_*` for capabilities that already have a canonical owner)
- No new root Telegram `*_handlers.py`
- No new EventBus / ServiceRegistry / WorkflowEngine classes outside canonical packages
- API contracts under `/api/platform`, `/api/creative`, `/api/skills`, `/api/agents`, `/api/voice`, `/api/project-memory`, `/management/v1/*` require versioned change process
- Schema changes require Alembic only (single head)

---

## A. Architecture (required)

- [ ] Canonical ownership confirmed in `platform_architecture/canonical_services.py` for:
  - [ ] service_builder, event_bus, workflow, ai_runtime, context_engine, project_memory
  - [ ] voice_runtime, multi_agent_runtime, skills_sdk, creative_factory, enterprise_city_runtime
- [ ] No new `platform_city` / `platform_creative` / `platform_voice` / `platform_multi_agent`
- [ ] Architecture report regenerated OR tracked ticket for stale FAIL report
- [ ] EventBus publish policy documented: only `PlatformEventBus` (+ enterprise façade)

## B. Database (required)

- [ ] `alembic heads` → single head `t3n456789012` (or successor)
- [ ] `alembic current` == head on **dev / staging / prod**
- [ ] Sprint 36.5–37.0 tables present (memory, voice, agents, skills, creative, platform_*)
- [ ] VersionMixin / audit schema mismatch ticket **closed** or temporary write-path disabled
- [ ] Backup taken before upgrade

## C. Security (required)

- [ ] `ENVIRONMENT=production` (or staging equivalent) set intentionally
- [ ] `IAM_JWT_SECRET`, `API_JWT_SECRET`, `SECURITY_MASTER_KEY`, `JWT_SECRET` provisioned (no defaults)
- [ ] DB credentials not using repo defaults in prod
- [ ] Management APIs require JWT / API key (`require_role` intact on City + Creative)
- [ ] Secrets not committed (`.env` gitignored verified)

## D. Backend APIs (required)

Smoke (auth required):

- [ ] `GET /api/platform/status` → sprint `37.0`
- [ ] `GET /api/dashboard`
- [ ] `GET /api/search?q=enterprise`
- [ ] `GET /api/creative/status` → sprint `36.9`
- [ ] `GET /api/skills/status` → sprint `36.8`
- [ ] `GET /api/agents` or multi-agent status
- [ ] `GET /api/voice` or voice status
- [ ] `GET /management/v1/platform/status`

## E. Frontend (required)

- [ ] `/platform` loads Enterprise City Runtime console
- [ ] `/platform-builder/creative` loads Creative Factory
- [ ] `/enterprise-city` or `/city` map still reachable (adapter)
- [ ] Navigation entries for City Runtime + Creative present
- [ ] No broken lazy imports on Freeze surfaces

## F. AI / Agents (required)

- [ ] Provider failover path exercised (Creative or AI Runtime)
- [ ] Skills sandbox execute path green
- [ ] Multi-agent session create green
- [ ] Voice parse path green
- [ ] Project Memory remember/search green

## G. Telegram (conditional for Freeze)

- [ ] Bot starts (`main.py` polling) in staging
- [ ] FSM storage uses Redis when `REDIS_REQUIRED=true`
- [ ] No new legacy root handlers added in Freeze PR window
- [ ] Known legacy debt accepted and documented

## H. Documentation (required)

- [ ] `docs/SPRINT_36_0_RESULT.md` … `docs/SPRINT_37_0_RESULT.md` present
- [ ] Feature docs for 36.0–37.0 present
- [ ] `docs/ENTERPRISE_AUDIT_1_0.md` reviewed by owner
- [ ] `docs/PRODUCTION_READINESS.md` scores accepted
- [ ] `docs/TECHNICAL_DEBT_REPORT.md` P0 items ticketed
- [ ] This checklist signed below

## I. Tests (required gate)

```bash
.venv/bin/python -m pytest \
  tests/test_service_builder_36_0.py \
  tests/test_event_bus_36_1.py \
  tests/test_workflow_runtime_36_2.py \
  tests/test_ai_runtime_36_3.py \
  tests/test_context_engine_36_4.py \
  tests/test_project_memory_36_5.py \
  tests/test_voice_runtime_36_6.py \
  tests/test_multi_agent_runtime_36_7.py \
  tests/test_ai_skills_sdk_36_8.py \
  tests/test_creative_factory_36_9.py \
  tests/test_enterprise_city_runtime_37_0.py \
  -q
```

- [ ] **129 passed** (or successor count documented)
- [ ] CI job locks this suite as `enterprise-freeze-gate`
- [ ] Full historical suite **not** required for Freeze (quarantine list filed)

## J. Performance / ops (pilot bar)

- [ ] Smoke latency acceptable on `/api/platform/status` and `/api/dashboard`
- [ ] Health endpoint / City readiness `ready: true`
- [ ] Logging/metrics destination configured
- [ ] Rollback plan: previous Alembic revision + prior release tag

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering owner | | | |
| Security owner | | | |
| Product / Platform owner | | | |

**Freeze status:** ☐ NOT STARTED · ☐ IN PROGRESS · ☐ FROZEN v1.0

**Freeze tag (suggested):** `enterprise-freeze-v1.0`

---

## Post-freeze change policy

1. Bug fixes allowed on frozen surfaces with regression tests.  
2. New capabilities require a new sprint **outside** frozen packages or an explicit Freeze Amendment.  
3. Schema: Alembic only; bump head; update checklist section B.  
4. Any new EventBus/WorkflowEngine/ServiceRegistry → Architecture reject.

---

## Audit snapshot (pre-freeze)

| Metric | Value |
|--------|------:|
| Production readiness | 72% |
| Architecture | 71% |
| Security | 62% |
| Sprint 36–37 tests | 129 passed |
| Issues found | 29 |
| Auto-fixed in audit | 1 code + docs |
| Manual P0 remaining | DB upgrade, audit VersionMixin, secrets, EventBus policy |
