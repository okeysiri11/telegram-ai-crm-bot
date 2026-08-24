# Sprint 47.0 — Foundation (Multi-Domain Expansion) — RESULT

Scope: `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md`'s Sprint 47.0 only. Stayed on `develop`. No
commits, no pushes, no resets, no branch switches, no dependency upgrades. Nothing beyond 47.0 was
started.

## What was implemented

1. **CC-2 — vertical registry reconciliation.** `container.py`'s DI vertical-service loop now derives
   from `platform_registry.verticals.VERTICAL_REGISTRY` (the canonical 12-vertical registry) instead
   of an independent, drifted, hardcoded 5-item tuple. The two pre-existing entries that have no
   canonical-registry counterpart (`realty`, `logistics` — confirmed to have real
   `src/verticals/<code>/service.py` backing but no business-vertical identity anywhere else in the
   platform) are kept registered under a clearly-commented "legacy strangler-layer" block so nothing
   that could previously resolve them stops resolving — additive, not destructive.
2. **AgentContext typed scope fields.** `platform_orchestrator/models.py`'s `AgentContext` gained
   optional `tenant_id`/`vertical`/`customer_id`/`user_id` fields (default `None`, additive — every
   existing caller that only sets the dict-shaped context fields is unaffected).
   `multi_agent_engine.py`'s `run_task` now best-effort-populates them from the session's
   `shared_context` when a caller actually supplied them there; nothing upstream fabricates values.
3. **Decision 5 — `tenant_id` canonicalization (additive).** `platform_memory/models.py`
   (`BusinessFact`, `ContextAssemblyRequest`), `platform_memory/continuity_store.py` (`MemoryRecord`,
   `TimelineEvent`), and `platform_memory/memory_permissions.py` (`MemoryPrincipal`) all gained a
   `tenant_id` field that mirrors the legacy `organization_id`/`company_id` field via `__post_init__`
   when not explicitly supplied. The ACL functions in `memory_permissions.py`
   (`can_read`/`can_write`/`can_delete`) now compare on `tenant_id` — behaviorally identical to the
   prior `company_id` comparison for every existing caller, since the two always match unless a caller
   explicitly diverges them. No destructive rename; `organization_id`/`company_id` remain and keep
   working. `platform_ai_command/core/models.py`'s `CommandMessage` got the same treatment
   (`tenant_id` mirrors `organization_id`, previously a dead, always-`None` field).
4. **CC-3 — server-side AI-command scoping.** This was the highest-value fix in this sprint.
   `platform_ai_command/api/router.py::cmd_chat` previously trusted whatever `role`/`vertical` the
   client sent in the request body (defaulting to `"owner"` if absent), and the web frontend
   (`ContextualAiChat.tsx`) hardcoded `role: "owner"` on every request regardless of the signed-in
   user's actual role or vertical. `cmd_chat` now calls a new `_resolve_server_side_scope()` helper
   that resolves the caller's **real** `active_vertical`/`active_persona`/`authenticated_role` from
   `services.vertical_role_registry` (the same in-process session store the Telegram bot already uses
   — reachable because the bot and the aiohttp API server run in the same process per
   `startup.py::run_startup()`) and a real `tenant_id` from `services.tenant_context.
   TenantContextService`, using the authenticated `actor_telegram_id` already resolved by the existing
   `require_role` JWT/API-key decorator. These server-resolved values now **override** the
   client-declared `role`/`vertical` for both tool-availability filtering
   (`filter_tools_for_role`) and the vertical/persona context passed to `AiCommandCenter.handle()`
   (which already accepted `active_vertical`/`active_persona`/`authenticated_role` parameters —
   they existed but were never wired from the HTTP layer before this sprint). Falls back to the
   client-declared value only when there is no authenticated Telegram identity to resolve a session
   for (e.g. a pure API-key caller with no bot-side session), and is wrapped in try/except so a
   lookup failure degrades to "no server-side scope" rather than breaking chat.

   `AiCommandCenter.handle()` gained a `tenant_id` parameter, threaded into `CommandMessage.tenant_id`
   (see point 3), so the resolved tenant is now actually available on the message object for future
   Sprint 47.1 memory-scoping work — previously nothing populated it.

   On the frontend, `ContextualAiChat.tsx` no longer hardcodes `role: "owner"`; it now sends the
   user's real `activeRoleId` (from `useRoleSwitcher`) and `verticalId` (already read from
   `useVerticalWorkspaceStore`) as a best-effort hint/fallback — the server no longer trusts this
   value as authoritative when a real session exists, but it's no longer an outright lie either.

## Files changed

Backend:
- `container.py`
- `platform_orchestrator/models.py`
- `platform_orchestrator/multi_agent_engine.py`
- `platform_memory/models.py`
- `platform_memory/continuity_store.py`
- `platform_memory/memory_permissions.py`
- `platform_ai_command/core/models.py`
- `platform_ai_command/core/command_center.py`
- `platform_ai_command/api/router.py`

Frontend:
- `src/web/src/owner-experience/ContextualAiChat.tsx`

Tests (new):
- `tests/test_ai_command_scoping_47_0.py` — 5 new tests covering `_resolve_server_side_scope`
  (no-telegram-identity fallback, real-session resolution, tenant resolution, graceful degradation on
  lookup failure) and one full HTTP-level integration test proving `cmd_chat` uses the server-resolved
  role/vertical/persona and ignores a conflicting client-declared `role`/`vertical` in the request
  body.

Docs:
- `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md` — status line updated to point at this file.
- This file.

Everything else showing as modified/untracked in `git status` (`handlers.py`, `keyboards.py`,
`platform_registry/menus/`, `platform_registry/verticals/`, `services/vertical_nav_service.py`,
several `src/web` vertical-workspace/unified-intent files, `tests/test_vertical_nav_46_5.py`,
`docs/SPRINT_46_5_FINAL_REPORT.md`, `docs/SPRINT_46_6_...md`,
`src/web/.../sprint_46_6_onboarding_workspace_transition.test.tsx`,
`src/web/.../verticalWorkspaceStore.test.ts`) predates this sprint — carried over from the Sprint
46.5/46.6 work already in the tree, untouched by Sprint 47.0.

Note: running the full `pytest tests/` suite triggers an architecture-governance test that
regenerates `ARCHITECTURE_CERTIFICATE.md`/`ARCHITECTURE_REPORT.md` as a side effect. That regeneration
mixed in 4+ days of pre-existing, already-uncommitted drift unrelated to this sprint (the last
committed baseline was 2026-08-05; today is 2026-08-09) and made it impossible to cleanly attribute
which of the reported boundary-violation deltas were pre-existing versus new. I reverted that
incidental regeneration (`git checkout -- ARCHITECTURE_CERTIFICATE.md ARCHITECTURE_REPORT.md`) rather
than ship an unreviewed, hard-to-attribute diff, and instead directly audited this sprint's actual new
imports (below) by hand.

## Tests and results

Targeted suites, run before and after each change (all passed after, matching pre-change baselines —
zero regressions in anything this sprint touched):

| Suite | Result |
|---|---|
| `tests/unit/test_container_scaffold.py` | 2 passed |
| `tests/test_multi_agent_runtime_36_7.py`, `test_orchestrator.py`, `test_integration_verification_37_4.py`, `test_enterprise_city_runtime_37_0.py` | 55 passed |
| `tests/test_universal_automation_45_3.py`, `test_context_engine_36_4.py`, `test_continuous_memory_45_2.py`, `test_project_memory_36_5.py`, `test_semantic_memory.py`, `test_platform_memory.py` | 1292 passed |
| `tests/test_ai_command_center_44_0.py`, `test_dual_experience_45_1.py`, `test_command_center_26_6.py`, `test_vertical_nav_46_5.py`, `test_drone_cloud.py` | 619 passed (includes the Sprint 46.6-fixed 30/30 vertical-nav suite) |
| `tests/test_ai_command_scoping_47_0.py` (new) | 5 passed |
| `tests/test_management_security.py`, `test_api_v1_freeze.py`, `test_admin_security.py` (CLAUDE.md's standard security gate) | 37 passed |
| Full `pytest tests/ -q -m "not slow"` | 5264 passed, 363 failed, 9 skipped — see Regressions below |
| Frontend `npm run test` (full) | 515 passed, 9 failed — identical to the Sprint 46.6 baseline, byte-for-byte |
| Frontend `npx tsc -b --pretty false` | No new errors; same 7 pre-existing errors as the Sprint 46.6 baseline (`src/ai-command/`, `src/hercules/` — untouched by this sprint) |

## Regressions found/fixed

**None caused by Sprint 47.0.** The full backend run's 363 failures were investigated directly, not
assumed: they are a pre-existing, repo-wide pattern of `test_version_<X>_ready` /
`test_api_<X>` / `test_docs_and_regression_<X>` tests across dozens of unrelated
`applications/enterprise_hub`-based sprint modules (predictive_intelligence, process_mining,
product_intelligence, quality_assurance, security_hardening, simulation_lab, tenancy, workflow, etc.)
that each hardcode the exact `application_version` string that was current when that sprint's test was
written. Confirmed directly: `tests/test_tenancy_20_0.py` asserts
`health["application_version"] == "9.0.4"`; the actual live value (verified by calling
`enterprise_hub.health()` directly) is `"9.4.0"` — a single shared global version that every older
sprint's test independently pinned and never updated. None of the 363 failures reference
`container.py`, `platform_memory`, `platform_orchestrator`, `platform_ai_command`, or any other file
this sprint touched (checked by grepping the full failure list for those module names — zero matches).
The `develop` branch's full test suite already has substantial pre-existing debt independent of this
work; out of scope for Sprint 47.0 to fix.

The 9 frontend failures are the identical, already-documented pre-existing set from
`docs/SPRINT_46_6_VERTICAL_NAV_STABILIZATION_REPORT.md` (dock-layout persistence, palette-section
catalog drift, ecosystem-template i18n, role-home route drift) — confirmed identical file-for-file,
test-for-test.

## Remaining technical debt

- **363 pre-existing backend test failures** (version-string drift, described above) — not part of
  this sprint's mandate, but worth its own cleanup sprint given the scale; CI on `develop` is very
  likely already red because of this, independent of any Sprint 47/46 work.
- **9 pre-existing frontend test failures** — already tracked in the Sprint 46.6 report.
- **Architecture governance baseline is stale and already failing** (`ARCHITECTURE_CERTIFICATE.md`
  last regenerated 2026-08-05, `Result: FAIL`, Architecture Score 73.85/100 even in its committed
  state) — regenerating it is a deliberate Sprint-workflow documentation step per CLAUDE.md, not
  something that should happen as a side effect of running `pytest tests/`; that the architecture test
  mutates a committed file as a side effect is itself worth fixing separately.
- **`platform_ai_command/api/router.py`'s new `services.vertical_role_registry` /
  `services.tenant_context` imports** are, by the architecture validator's own layer model, an
  "AI services importing business modules" direction — the same `reverse_layer_dependency` pattern
  already present in numerous other `platform_*` packages today (`platform_ai_marketing_os/facade.py`,
  `platform_quality/facade.py`, `platform_operations/activity_service.py`, and others — all visible in
  the existing, already-failing baseline). I judged this the correct tradeoff rather than a defect to
  route around: `services/vertical_role_registry.py` and `services/tenant_context.py` are the
  platform's actual, canonical, single sources of truth for this data (the same ones
  `middleware/tenant_middleware.py` itself uses), and inventing a duplicate/parallel path to reach the
  same data purely to satisfy the layer checker would itself violate "avoid duplicate infrastructure"
  far more seriously. Documenting this here per CLAUDE.md's "every architectural decision must be
  documented" — worth a deliberate look (relaxing the layer rule for this known-legitimate case, or
  moving `vertical_role_registry`/`tenant_context` to a lower layer) in a future sprint, not blocking
  this one.
- **`realty`/`logistics` in `container.py`** are legacy strangler-layer entries with no real business
  identity anywhere else in the platform (confirmed via grep — they appear nowhere in
  `platform_registry`, `vertical_role_registry`, bot menus, or the frontend catalog). Kept registered
  for backward compatibility since nothing calls `container.vertical(code)` in production today
  (verified — zero call sites outside the DI scaffold's own tests), but they're dead weight worth a
  deliberate removal decision in a future sprint rather than a silent one now.
- **`multi_agent_engine.py`'s tenant_id/vertical/customer_id population is best-effort only** — it
  reads from `session.shared_context` if a caller already put them there, but nothing upstream of it
  yet does. This is intentional (Sprint 47.0's job was to make the typed fields exist and be
  populate-able, not to invent new upstream plumbing that isn't part of this sprint's scope) but means
  the fields are not yet populated in most real call paths — Sprint 47.1/47.2 will need to actually
  wire a caller that knows the real values into this path.

## Is 47.1 safe to start?

**Yes.** Sprint 47.1 (AI Memory Architecture — the five scopes) depends on Sprint 47.0 delivering: a
canonical `tenant_id` field across `platform_memory` (done, additive, tested), a corrected vertical
registry source of truth (done), and real server-side scope resolution for AI requests (done, tested
end-to-end). All three are in place and regression-tested against their existing suites with zero
new failures. The one open item worth flagging before 47.1 begins: 47.1 will need to decide whether
its new `MemoryScope` enum lives alongside the `tenant_id` fields added here in
`platform_memory/models.py`/`continuity_store.py`/`memory_permissions.py`, or in a new module — not a
blocker, just a design choice for that sprint to make explicitly per its own "document decisions"
duty.

Awaiting explicit approval before starting Sprint 47.1.
