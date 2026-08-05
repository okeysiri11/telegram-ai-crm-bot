# Enterprise Audit v1.0 — ADOS Enterprise Platform

**Date:** 2026-08-04  
**Baseline:** After Sprint **37.0** (Enterprise City Runtime)  
**Scope:** Production readiness audit — architecture, backend, database, security, performance, AI, frontend, Telegram, documentation, tests, code quality  
**Type:** Engineering audit (not a feature sprint)

---

## Executive verdict

| Question | Answer |
|----------|--------|
| Can Enterprise Freeze v1.0 begin? | **Conditional YES** — freeze the **Sprint 36.0–37.0 control plane** now; defer full-monorepo freeze until Critical/High debt below is cleared |
| Overall production readiness | **72%** |
| Sprint 36–37 runtime readiness | **91%** (tests green, SoR discipline held) |
| Full platform readiness | **72%** (legacy duplicates + DB lag + suite failures) |

---

## Scorecard

| Dimension | Score | Notes |
|-----------|------:|-------|
| Architecture | **71%** | SoR discipline for 36–37 strong; residual EventBus/workflow/memory/UI duplicates |
| Security | **62%** | City/Creative RBAC consistent; secrets/audit schema/DB lag weaken prod posture |
| Performance | **74%** | In-memory runtimes fine for pilot; ORM/async cancellation noise; no load suite for City |
| Maintainability | **68%** | ~81 `platform_*` packages; naming collisions; legacy adapters still live |
| Documentation | **88%** | Sprint 36–37 RESULT + feature docs complete; freeze checklist was missing (this audit adds it) |
| Testing | **70%** | 129/129 on 36.0–37.0; broader suite: 30 failures in first 263 collected (legacy version/doc gates) |
| **Production readiness** | **72%** | Weighted composite |

---

## Critical

| ID | Area | Finding | Evidence |
|----|------|---------|----------|
| C1 | Database | Live DB **14 revisions behind** Alembic head `t3n456789012` (stuck at `f9f234567890`). Sprint 36.5–37.0 tables absent in applied schema. | `alembic current` / `alembic heads` |
| C2 | Database | **VersionMixin** columns (`version`, …) on audit ORM models but **not** on live `audit_log` / `audit_events` / `audit_engine_logs` → runtime `UndefinedColumn` on write | ORM + prior test logs |
| C3 | Architecture | Multiple live **EventBus** implementations vs canonical `events.event_bus.PlatformEventBus` policy | `platform_events_legacy`, ecosystem/hub/finance buses, TS `src/kernel/event_bus` |
| C4 | Architecture gate | Stale `ARCHITECTURE_REPORT.md` still **Grade: FAIL** (2026-07-20) — not regenerated post 36–37 | Root report |

---

## High

| ID | Area | Finding |
|----|------|---------|
| H1 | Backend | Triple workflow stacks: `platform_workflow`, `platform_workflows`, `platform_ai/workflows` |
| H2 | Backend | Dual MemoryService: `platform_memory` + `platform_ai.memory` (soft cycle; eager edge softened in this audit) |
| H3 | Frontend | Creative dual UI: `creative-console` + `ai-production-studio` both routed |
| H4 | Frontend | City surfaces: spatial `enterprise-city`, control `platform-console`, separate `platform_console/` app |
| H5 | Backend | Parallel orchestrators/registries: `platform_orchestrator`, `platform_agents`, `platform_enterprise_ai_orchestrator`, `src/orchestrator`, `src/kernel` |
| H6 | DI | Multiple ServiceRegistry classes (`container`, service_builder, ecosystem, hub, TS kernel) |
| H7 | Security | Production secrets incomplete vs policy (`IAM_JWT_SECRET`, `API_JWT_SECRET`, `SECURITY_MASTER_KEY`); `ENVIRONMENT` often unset |
| H8 | Security | Hardcoded postgres defaults in `alembic.ini` / engine / settings |
| H9 | Tests | Broader suite fails legacy version/manifest/doc assertions (agents 19.x, ABA, AMO, AOP, APH, AI OS chrome, …) |
| H10 | Docs | No prior `docs/*FREEZE*` artifact despite freeze tests / API freeze policy |

---

## Medium

| ID | Area | Finding |
|----|------|---------|
| M1 | Data | `content_factory` still live beside `creative_factory` (different schemas; active legacy) |
| M2 | Catalog | `FOUNDATION_CATALOG` missing `svc_service_builder` / dedicated event-bus svc vs `canonical_services` |
| M3 | Frontend | 207 App routes; ~26 alias groups (short ↔ `/platform-builder/*`) |
| M4 | Telegram | Legacy `handlers.py` + 22 root `*_handlers.py` still primary; FSM + Redis OK |
| M5 | Security | Coarse RBAC (`READ_ONLY`/`ADMINISTRATOR` only) on City/Creative |
| M6 | Naming | `platform_console/` vs `src/web/src/platform-console` collision |
| M7 | Audit | Fragmented audit tables (`audit_log`, `audit_logs`, `audit_engine_logs`, `audit_events`) |
| M8 | Coupling | AI/orchestrator routers → `platform_management.permissions`; management registers routers |

---

## Low

| ID | Area | Finding |
|----|------|---------|
| L1 | Exports | `platform_ai` / `platform_orchestrator` `__init__` thin but valid |
| L2 | SoR | Forbidden packages correctly absent (`platform_city`, `platform_creative`, `platform_voice`, …) |
| L3 | Docs | Overlapping historical AUDIT/DEBT/READINESS docs (noise, not incorrect) |
| L4 | Async | `Connection._cancel` never-awaited warnings in pytest (noise) |

---

## Recommendations (priority order)

1. **Ops:** `alembic upgrade head` on every environment before Freeze.  
2. **Schema:** VersionMixin backfill migration for audit (+ remaining tables).  
3. **Secrets:** Enforce `ENVIRONMENT=production` + full `REQUIRED_PRODUCTION_SECRETS`.  
4. **Bus:** Mark non-canonical EventBuses deprecated; route publishes through `PlatformEventBus` / enterprise façade.  
5. **UI:** Redirect `/production-studio` → Creative Factory; nest City map under `/platform`.  
6. **Workflows/Memory:** Document single SoR; quarantine legacy packages.  
7. **Tests:** Quarantine or rewrite legacy version-gate tests; keep 36–37 suite as Freeze gate.  
8. **Regen** architecture gate report after boundary fixes.  
9. **Telegram:** Continue migration to `platform_sdk`; freeze new root `*_handlers.py`.  
10. Begin Freeze using `docs/ENTERPRISE_FREEZE_CHECKLIST.md`.

---

## Estimated effort (remaining to ≥90% readiness)

| Workstream | Effort |
|------------|--------|
| DB upgrade + VersionMixin audit backfill | 1–2 days |
| Secrets / env hardening | 0.5 day |
| EventBus deprecation plan + first cutover | 3–5 days |
| Workflow + memory SoR quarantine | 2–3 days |
| Frontend alias consolidation | 1–2 days |
| Legacy test quarantine / rewrite | 2–4 days |
| Architecture report regen + boundary fixes | 1–2 days |
| **Total to Freeze-ready (≥90%)** | **~2–3 weeks** (1 eng) |

---

## What was verified green (this audit)

| Check | Result |
|-------|--------|
| Alembic graph | Single head `t3n456789012`, 128 revisions, **0 broken** `down_revision` |
| Sprint 36.0–37.0 tests | **129 passed** |
| Sprint RESULT + feature docs 36.0–37.0 | **11/11 RESULT**, **12/12 feature** |
| City/Creative `require_role` coverage | Complete on handlers |
| Package exports import | OK |
| Forbidden parallel SoRs | Absent |

---

## Automatic fixes applied during audit

| Fix | Detail |
|-----|--------|
| Soft cycle break | Lazy-import `platform_memory` inside `platform_ai/memory/memory_context.py` |
| Deliverables | Created Freeze checklist + refreshed debt/readiness/audit docs |

**Not auto-fixed (manual / ops):** DB upgrade, VersionMixin migration, EventBus consolidation, legacy test failures, secret rotation.

---

## Totals

| Metric | Count |
|--------|------:|
| Issues found (C+H+M+L unique IDs) | **29** |
| Critical | **4** |
| High | **10** |
| Medium | **8** |
| Low | **4** |
| Fixed automatically | **1** code + **4** audit docs |
| Remaining manual work items | **~15** (grouped in effort table) |

---

## Freeze recommendation

**Enterprise Freeze v1.0 may begin for the Sprint 36.0–37.0 platform kernel** (Service Builder → Event Bus → Workflow → AI Runtime → Context → Memory → Voice → Multi-Agent → Skills → Creative → City Runtime), provided:

1. Staging/prod run `alembic upgrade head`  
2. Critical audit VersionMixin gap has a tracked migration ticket  
3. Freeze gate tests = the 129-passing 36–37 suite (+ smoke)  
4. Full monorepo legacy packages remain **quarantined**, not freeze-certified

See: `docs/ENTERPRISE_FREEZE_CHECKLIST.md`, `docs/PRODUCTION_READINESS.md`, `docs/TECHNICAL_DEBT_REPORT.md`.
