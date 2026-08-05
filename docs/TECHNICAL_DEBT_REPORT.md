# Technical Debt Report — Enterprise Audit v1.0

**Supersedes for Freeze planning:** historical `docs/TECHNICAL_DEBT_REPORT.md` (Sprint 30.2) content is retained below as legacy reference; **active Freeze backlog is this file’s “Active debt (post-37.0)” section**.

**Date:** 2026-08-04  
**Audit:** `docs/ENTERPRISE_AUDIT_1_0.md`

---

## Active debt (post-37.0)

### P0 — Block full production freeze

| ID | Debt | Owner SoR | Action |
|----|------|-----------|--------|
| TD-E01 | DB 14 revisions behind head `t3n456789012` | Ops / DB | `alembic upgrade head` all envs |
| TD-E02 | Audit tables missing VersionMixin columns | `database` | New Alembic backfill; align ORM/DB |
| TD-E03 | Multiple EventBus implementations | `events` | Deprecate peers; single publish path |
| TD-E04 | Stale ARCHITECTURE_REPORT FAIL | Architecture | Regen after boundary fixes |

### P1 — Block “clean architecture” freeze

| ID | Debt | Action |
|----|------|--------|
| TD-E05 | Triple workflow engines | Quarantine `platform_workflows` + AI-local; canonical `platform_workflow` |
| TD-E06 | Dual MemoryService | Canonical `platform_memory`; AI package adapter only |
| TD-E07 | Creative UI dual (`ai-production-studio`) | Redirect to `/platform-builder/creative` |
| TD-E08 | City UI triad (map / console / `platform_console` app) | Document ownership; nest map under `/platform` |
| TD-E09 | Parallel orchestrators / ServiceRegistries | Document SoR; stop new registries |
| TD-E10 | Incomplete production secrets | Provision IAM/API JWT + master key; set `ENVIRONMENT=production` |
| TD-E11 | Hardcoded DB credentials in defaults | Env-only in prod; scrub docs/samples |
| TD-E12 | Legacy suite version/doc gate failures | Quarantine or update assertions |

### P2 — Cleanup / maintainability

| ID | Debt | Action |
|----|------|--------|
| TD-E13 | `content_factory` vs `creative_factory` | Deprecation banner + no new features on content_factory |
| TD-E14 | FOUNDATION_CATALOG gaps vs canonical | Add `svc_service_builder` (+ event bus svc if required) |
| TD-E15 | Route alias sprawl (207 routes) | Deprecation map; keep aliases one release |
| TD-E16 | Telegram legacy handlers | Freeze new root handlers; migrate to SDK |
| TD-E17 | Coarse City/Creative RBAC | Module-scoped permissions |
| TD-E18 | Name collision `platform_console` | Rename admin app or document clearly |
| TD-E19 | Fragmented audit table names | Single SoR write path |
| TD-E20 | Async cancel warnings in tests | Engine/session lifecycle cleanup |

---

## Debt intentionally accepted for Freeze v1.0

| Item | Rationale |
|------|-----------|
| Spatial City map separate from `/platform` control plane | By design (presentation adapter) |
| Thin `__all__` on `platform_ai` / `platform_orchestrator` | Prefer explicit submodule imports |
| Telegram polling + web dual entry | Product requirement; document deploy topology |
| Historical vertical pilots failing version docs tests | Outside 36–37 Freeze scope |

---

## Inventory notes

- **~81** top-level `platform_*` packages — high surface; Freeze must list **in-scope** packages explicitly.  
- Forbidden parallel packages (`platform_city`, `platform_creative`, `platform_voice`, `platform_multi_agent`) **correctly absent**.  
- Sprint 36–37 SoR extensions are the **preferred pattern** going forward.

---

## Resolved / improved in this audit

| Item | Change |
|------|--------|
| Eager `platform_ai.memory` → `platform_memory` import | Lazied in `memory_context.py` |
| Missing Freeze checklist | Added `docs/ENTERPRISE_FREEZE_CHECKLIST.md` |
| Missing Enterprise Audit v1.0 | Added `docs/ENTERPRISE_AUDIT_1_0.md` |

---

## Legacy reference (Sprint 30.2 excerpt)

Earlier TD-01…TD-16 (naming ecosystems, Mission Control overlap, unversioned CRM, PB header auth, Vitest gaps, etc.) remain relevant for monorepo hygiene but are **not** the Freeze v1.0 gate. See git history of this file prior to 2026-08-04 for the full Sprint 30.2 table if needed.

**Related registries:** `docs/TECH_DEBT_REGISTRY.md`, `docs/TECH_DEBT_V2.md`, `docs/TECHNICAL_DEBT_30_5.md`.
