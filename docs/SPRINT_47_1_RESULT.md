# Sprint 47.1 — AI Agent Memory Architecture — RESULT

Scope: `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md`'s Sprint 47.1 only, per the confirmed
Decision 1 (PLATFORM/ORGANIZATION/VERTICAL/USER/CUSTOMER scopes). Builds on Sprint 47.0's canonical
`tenant_id` and server-side scope enforcement — nothing from 47.0 was modified or reverted. Stayed on
`develop`. No commits, no pushes, no resets, no branch switches, no dependency upgrades. Sprint 47.2
was not started.

## What was implemented

### 1. `MemoryScope` — the single source of truth (`platform_memory/scope.py`, new)

A `MemoryScope` enum (`PLATFORM`, `ORGANIZATION`, `VERTICAL`, `USER`, `CUSTOMER`) plus one function,
`resolve_memory_scope(*, tenant_id, vertical, customer_id, user_id)`, that **derives** scope from the
identifiers a record already carries rather than requiring every call site to set a redundant, separate
scope field that could drift out of sync with the record's actual identifiers. Precedence (narrowest
first): CUSTOMER → USER → VERTICAL → ORGANIZATION → PLATFORM (documented in the module docstring with
the reasoning — a customer-specific note stays CUSTOMER-scoped even if a specific user wrote it).
This is the only place scope logic lives; nothing else defines a parallel scope concept.

### 2. `scope` exposed on the records/principal that carry the right identifiers

Added a computed `.scope` property (and `vertical`/`customer_id` fields where not already present from
Sprint 47.0) to:
- `platform_memory.memory_permissions.MemoryPrincipal` — `.scope` uses `tenant_id`/`vertical`/
  `customer_id`/`owner_id`. `can_read`/`can_write`/`can_delete` are **unchanged** from Sprint 47.0 —
  scope is informational/derived, not a new enforcement axis, per the plan's explicit note that
  "level" (durability) and scope are orthogonal and must not be conflated with each other or with the
  existing tenant_id-based ACL.
- `platform_memory.continuity_store.MemoryRecord` — same pattern.
- `platform_memory.models.BusinessFact` — the clearest real-world ORGANIZATION-scoped record (has
  `tenant_id`, no `user_id`); verified it resolves to ORGANIZATION by default and VERTICAL when a
  vertical is set.
- `platform_memory.models.ProjectMemoryRecord` — gained `tenant_id`/`vertical`/`customer_id` from
  scratch (had none before this sprint).

`platform_memory.continuity_store.TimelineEvent` and `ContinuityStore.summaries` (a plain dict used by
`memory_summary.py`) were deliberately **not** given a scope property — they're audit-log/derived-cache
shapes, not primary memory content, and extending scope to them wasn't part of this sprint's mandate.
Documented as a scope boundary, not an oversight — see Remaining Technical Debt.

### 3. Database migration — `project_memory` / `user_memory` tables (Decision 5's explicit ask)

`migrations/versions/v5p678901234_memory_scope_47_1.py` (chained after Sprint 46.x's head,
`u4o567890123`) adds nullable `tenant_id` (real FK to `partner_tenant_engine_v1_tenants.id`,
`ondelete="SET NULL"`, following `ai_sales_agent.py::CustomerPreference`'s exact schema template) and
`vertical` to both `project_memory` and `user_memory`, plus `customer_id` to `user_memory` only —
**not** to `project_memory`, because `ProjectMemoryRow` already has a `client_id` column that is the
CUSTOMER identifier for that table; adding a second, parallel `customer_id` column would have been
exactly the "duplicate scope logic" the brief said not to introduce. `downgrade()` is a deliberate
no-op, matching the non-destructive-migration precedent already established by `u4o567890123`'s own
downgrade. `database/models/project_memory.py::ProjectMemoryRow` and
`database/models/user_memory.py::UserMemory` were updated to match the migration exactly.

### 4. `MemoryPrincipal` ACL wired into every real memory read/write path (the largest piece of work)

**Audit finding, not assumed:** before this sprint, `memory_permissions.py`'s `can_read`/`can_write`/
`can_delete`/`filter_readable` existed but were called from only 2 of roughly 15 write call sites
across `platform_memory` (`MemoryManager.save`/`.remove`) and from **zero** read call sites — every
other module (`working_memory.py`, `memory_search.py`, `memory_cards.py`, `long_term_memory.py`,
`conversation_memory.py`, `memory_cleanup.py`) called `continuity_store.list_for`/`.get`/`.save`/
`.remove` directly, relying only on the store's own naive `owner_id`/`company_id` pre-filter. Two
concrete, real gaps were found this way:
- `MemoryManager.pin()` never checked `can_write` at all — only `rec.owner_id != owner_id`, which is
  *narrower* than `can_write` (it silently rejected legitimate admin/owner cross-user actions that
  `can_write`'s admin/owner branch is supposed to allow).
- `MemoryManager.workspace()` read raw `continuity_store.list_for()` results without `filter_readable`.

**Fix — centralized, not duplicated:** rather than requiring every one of ~10 consumer modules to
correctly re-implement the ACL check (the original design, which is exactly how the `pin()` gap
happened), `ContinuityStore.save()`/`.get()`/`.remove()`/`.list_for()` (`continuity_store.py`) gained
an optional `principal: MemoryPrincipal | None = None` parameter. When provided, the store itself
calls `can_write`/`can_read`/`can_delete`/`filter_readable` internally — one implementation, one place.
**Omitting `principal` (the default) reproduces Sprint-47.0 behavior exactly** — every write is
unconditional, every read is the raw owner_id/company_id filter — so this is purely additive; nothing
that omits the new parameter changed at all. Then every one of the ~15 direct call sites across
`working_memory.py`, `memory_search.py`, `memory_cards.py`, `long_term_memory.py`,
`conversation_memory.py`, `memory_cleanup.py`, and `memory_manager.py` (the last is where `pin()` and
`workspace()` live) was updated to pass `principal=principal` — mechanical, low-risk changes, since
every one of these already received `principal` as its first parameter. `smart_recall.py`,
`ai_resume.py`, `memory_summary.py`, and `context_engine_v2.py` were checked and found to make no
direct `continuity_store` calls at all (they delegate to the now-fixed modules above), so nothing
there needed changing.

`memory_manager.py::pin()` was fixed to call `can_write(p, rec)` (was: only an owner-id equality
check) and `memory_manager.py::workspace()` now passes `principal=p` to its `list_for()` call.

## Files changed

New:
- `platform_memory/scope.py`
- `migrations/versions/v5p678901234_memory_scope_47_1.py`
- `tests/test_memory_scope_47_1.py` (22 tests)

Modified (backend):
- `platform_memory/continuity_store.py`, `memory_permissions.py`, `models.py`
- `platform_memory/working_memory.py`, `memory_search.py`, `memory_cards.py`, `long_term_memory.py`,
  `conversation_memory.py`, `memory_cleanup.py`, `memory_manager.py`
- `database/models/project_memory.py`, `database/models/user_memory.py`
- `tests/test_database_stabilization_37_1.py` (updated the alembic-head assertion — see Regressions)

No frontend files were touched in Sprint 47.1 (confirmed via `git status` before and after — the
`src/web` entries visible in the working tree all predate this sprint, carried over from 46.6/47.0).

## Tests and results

| Suite | Result |
|---|---|
| `tests/test_memory_scope_47_1.py` (new) | 22 passed |
| `tests/test_universal_automation_45_3.py`, `test_context_engine_36_4.py`, `test_continuous_memory_45_2.py`, `test_project_memory_36_5.py`, `test_semantic_memory.py`, `test_platform_memory.py` | 1292 passed (re-run after every incremental change — never regressed) |
| `tests/test_multi_agent_runtime_36_7.py`, `test_orchestrator.py` (47.0's touched modules) | still passing, re-verified alongside the memory suites (1329 combined) |
| `tests/test_database_stabilization_37_1.py` | 11 passed (after the expected head-revision update — see Regressions) |
| `tests/test_management_security.py`, `test_api_v1_freeze.py`, `test_admin_security.py` | 37 passed |
| Full `pytest tests/ -q -m "not slow"` | 5286 passed, 363 failed, 9 skipped — **byte-identical failure set to Sprint 47.0's documented baseline** (verified by diffing the full FAILED-line list between runs, not just comparing counts) |
| Frontend | not re-run — zero frontend files changed this sprint; Sprint 47.0's documented 515 passed / 9 failed stands unchanged |

## Regressions found/fixed

**One self-inflicted, immediately-fixed regression; zero regressions in anything else.**

Adding a new Alembic migration naturally moves the "current head" — and
`tests/test_database_stabilization_37_1.py::test_single_alembic_head` and `::test_alembic_heads_cli`
hardcode the previous head (`u4o567890123`) by design (their job is to catch *accidental* branching,
not to freeze the head forever). The first full-suite run came back at 365 failed (363 baseline + these
2). This was investigated directly, not assumed: `grep`ing the full failure list for anything
migration/schema-related surfaced exactly these two tests, confirming the cause precisely before
touching anything. Updated both assertions to the new head (`v5p678901234`, chained after
`u4o567890123` as expected) — a correct, intended consequence of adding a real migration, not a bug.
Re-ran the full suite afterward and confirmed by diffing the complete FAILED-line lists between runs
that **only** those two lines changed; all other 363 pre-existing failures are identical, file-for-file,
to Sprint 47.0's documented baseline (which was itself independently verified against `git log` and a
live version-string check in that sprint).

No other regressions: every targeted suite for every file touched this sprint passed on every run,
including several full re-runs after each incremental change (not just once at the end).

## Remaining technical debt

- **`TimelineEvent` and `ContinuityStore.summaries` have no scope/ACL model.** Timeline events already
  have an owner_id/company_id pre-filter in `list_timeline()` but no `MemoryPrincipal`-based enforcement
  (no `can_read`-equivalent exists for `TimelineEvent` at all) and `summaries` is a plain dict keyed by
  session, entirely outside the `MemoryRecord`/ACL model. Neither was in this sprint's explicit mandate
  ("memory read/write path" was interpreted as `MemoryRecord` content, consistent with where
  `memory_permissions.py` already defined its ACL functions), but both are real, adjacent gaps worth a
  deliberate look in a future sprint.
- **The three still-parallel "project memory" implementations found during the audit were not
  reconciled.** `database/models/project_memory.py` (SQLAlchemy, now scope-column-complete but has no
  live repository/service wired to it), `platform_memory/repositories/project_memory_repository.py` +
  `providers/in_memory.py` (dataclass + provider pattern, also with no live callers found), and
  `platform_memory/project_memory_engine.py` (the actually-live one, used by
  `platform_orchestrator/multi_agent_service.py::for_project_memory`) all model overlapping concepts.
  This sprint deliberately did not touch `project_memory_engine.py` or its own `MemoryRecord` (in
  `platform_memory/project_memory_models.py` — a *third*, distinct `MemoryRecord` class, not to be
  confused with `continuity_store.py`'s or `memory_permissions.py`'s) — reconciling three parallel
  memory subsystems into one canonical implementation is a real architectural decision (per Rule 1,
  "one canonical implementation per domain") that deserves its own explicit sprint and sign-off, not a
  side effect of adding scope columns. Flagging it here rather than silently leaving it undiscovered.
- **`AgentContext`'s `tenant_id`/`vertical`/`customer_id`/`user_id` (Sprint 47.0) are still only
  best-effort-populated** from `multi_agent_engine.py`'s `session.shared_context` when a caller happens
  to put them there — nothing wires `MemoryScope`/`MemoryPrincipal` into the orchestrator's own
  `AgentContext` yet. That connection (agent execution context ↔ memory ACL) is natural follow-on work
  for Sprint 47.2 ("AI Specialist Agent UX"), not this one.
- **`vertical` values are free-text strings**, not validated against `platform_registry.verticals.
  VERTICAL_REGISTRY` (CC-2's canonical registry from Sprint 47.0). Nothing stops a caller from setting
  `vertical="not_a_real_vertical"` and getting a VERTICAL-scoped record that doesn't correspond to any
  real vertical. Low risk (scope is informational, not an ACL gate, in this sprint), but worth adding
  validation before scope is used for anything higher-stakes.
- **Running `pytest tests/` regenerates `ARCHITECTURE_CERTIFICATE.md`/`ARCHITECTURE_REPORT.md` as a
  side effect** — same pre-existing issue documented in Sprint 47.0's RESULT.md, reverted again here for
  the same reason (mixes in unrelated drift, makes attribution impossible). Still unfixed, still not
  this sprint's mandate.
- **The 363 pre-existing backend failures and 9 pre-existing frontend failures** — unchanged from
  Sprint 47.0, still out of scope.

## Is 47.2 safe to start?

**Yes**, with one thing worth knowing going in: Sprint 47.2 ("AI Specialist Agent UX") is explicitly
expected to wire `AgentContext` into the memory/scope model this sprint built (see the `AgentContext`
debt item above) — that's expected, forward-looking work for 47.2, not a blocker. Everything Sprint
47.1 delivered (the scope enum, the DB migration, and the ACL wiring) is regression-tested and
non-breaking on its own.

Awaiting explicit approval before starting Sprint 47.2.
