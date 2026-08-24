# Sprint 47.x — Multi-Domain Expansion Plan (FINALIZED, pre-implementation)

Status: **PLAN FINALIZED — approved architectural decisions below. No code, migrations, or
implementation exist yet.** Separate from and does not modify the Sprint 46.x vertical-navigation
stabilization work. Stays on `develop`; nothing in this initiative has been committed or pushed.

## Source specification (as received)

1. AI specialist agents across verticals should produce: findings; prioritized recommendations;
   tasks; daily reports; weekly reports; reminders; measurable objectives; performance comparison —
   with a UX like "communicating with capable AI specialists," while each agent stays strictly bound
   to its role, permitted data, organization, vertical, and customer/project context.
2. Travel Website/Marketing Connectors: provider-neutral interfaces for website/CMS, landing pages,
   Google Analytics, Google Tag Manager, Meta Pixel, Meta Ads, other ad sources, SEO/search data, UTM
   attribution, lead/CRM reconciliation. Chain: traffic → source → campaign → website session → lead
   → CRM → conversion → customer → revenue. No CMS lock-in.
3. Port/Maritime/Freight Action Hub: preserve/expose port-logistics capabilities. Sections: Freight,
   Vessels, Vessel Tracking, Containers, Container Tracking, Cargo, Voyages, Arrivals, Departures,
   ETA/ETD, Berths, Port Operations, Logistics, Counterparties, Contracts, Documents, Tasks,
   Analytics, AI Operations Assistant.
4. Vessel/Container provider-neutral domain objects. Explicit constraint: **do not fake live
   tracking**; prepare adapters for future AIS/container providers.
5. Contract/Document Center: Contract as a first-class object; Attachments supporting future
   PDF/image/photo/scan uploads, flow: open contract → Attach → pick file or take photo/scan →
   upload → store → metadata attached → optional AI/OCR. **Critical constraint: the original
   uploaded file must always be preserved; OCR/extracted text is derivative and must never replace
   the source document.**
6. Legal Action Hub: preserve existing Legal functionality; do not invent access rules.
7. AI Agent Memory Architecture: scoped persistent memory — PLATFORM, ORGANIZATION, VERTICAL, USER,
   **CUSTOMER** (confirmed).

---

## Confirmed architectural decisions

All five open questions from the prior review round are resolved. Recorded here verbatim as the
binding decisions for every sprint below, per this repo's "document decisions at the time they're
made" convention.

### Decision 1 — AI Memory Scopes (confirmed)
Final enum: **PLATFORM / ORGANIZATION / VERTICAL / USER / CUSTOMER**.

### Decision 2 — Port domain canonicalization (confirmed)
`port_erp` is canonical. Migrate `port_enterprise`'s unique functionality into it — freight
marketplace, multimodal logistics, customs/trade, warehouse/distribution, vessel tracking, voyage
tracking, container tracking, berth/terminal operations, freight operations, documents/contracts, AI
operations capabilities. No two competing domain models. No deletion of working functionality during
migration. `port_enterprise`'s application shell is deprecated **only after** its functionality is
safely migrated and regression-tested — not before.

### Decision 3 — OCR (confirmed)
Defer OCR implementation in Sprint 47.x. Ship reliable original-file upload/storage and the
Contract/Document Center first. Design the storage/attachment boundary so a cloud OCR connector can
be added later (via the existing `platform_integrations` `ConnectorBase` pattern) without redesigning
storage. No self-hosted OCR infrastructure in this initiative. OCR must never block or gate document
storage.

### Decision 4 — Travel (confirmed, expanded)
Connectors-first: reuse `LeadEngineLead`, the CRM pipeline engines, `pg_marketing_analytics_v1`, the
existing UTM columns, and the `platform_integrations` connector framework. **Do not** build a
duplicate Travel CRM/backend merely to receive leads. **However**, the Travel *UI* must be architected
as a real first-class vertical workspace (not a stub, and not just a connectors config screen) so it
can expand later without an architectural rewrite. It must be able to expose: website/landing
management, traffic sources, campaigns, UTM attribution, leads, conversion funnel, customers, revenue,
competitor monitoring, SEO, analytics, content/production, AI marketing specialists, recommendations,
reports, and reminders/tasks — all backed by shared infrastructure underneath (the generic lead/CRM/
analytics tables, Sprint 47.2's generic specialist/findings/report/reminder/task infrastructure, and
Sprint 47.4's connector layer), not vertical-specific duplicates of any of it.

### Decision 5 — Canonical tenant identifier (confirmed)
Standardize new enforcement/scoping architecture on **`tenant_id`**. No permanent
`organization_id ↔ tenant_id` translation seam. Where legacy `organization_id`/`company_id` fields
exist (`platform_memory/models.py`, `memory_permissions.py`'s `MemoryPrincipal`), plan a controlled
migration/compatibility path toward `tenant_id` rather than adding a third parallel abstraction —
detailed under Migrations & Compatibility Risks below.

### General architectural rules (governing every sprint below)
1. One canonical implementation per domain.
2. Reuse existing shared infrastructure before creating new modules.
3. Preserve all existing working functionality, including Telegram bot capabilities.
4. No destructive migrations without compatibility and regression coverage.
5. Tenant isolation must be enforced server-side.
6. RBAC and role-specific UX must remain first-class.
7. AI memory must respect PLATFORM / ORGANIZATION / VERTICAL / USER / CUSTOMER scopes.
8. File storage must persist actual original files, not only Telegram file IDs or external
   references.
9. New vertical UX should be action-oriented, not just analytics dashboards.
10. Owner, manager, dealer/partner, employee, and customer experiences must expose only their
    permitted actions/data.
11. Avoid duplicate CRM, analytics, AI-agent, document, notification, task, and integration
    infrastructure.
12. Keep the architecture extensible for future verticals and external integrations.

---

## New findings from the decision-verification pass

Before finalizing, I checked two things the confirmation message specifically asked me to verify —
"Agro fields/maps" and "Crypto AI specialists" — since neither was covered by the original five
research agents. Both checks surfaced material new information that changes the plan's scope,
consistent with Rule 1 ("one canonical implementation per domain") and the honesty standard already
set in the prior round (I would rather report an uncomfortable finding than silently claim coverage).

### NF-1. Agro has the exact same duplication problem as Port — just not yet flagged
`applications/` contains **two parallel Agro app subtrees**, exactly mirroring the
`port_erp`/`port_enterprise` situation Decision 2 already resolved a policy for:
- **`applications/agro_enterprise/`** — `precision_agriculture/fields_gis.py` (this *is* "Agro
  fields/maps" — a real GIS/field-mapping module), `precision_agriculture/sensing.py`,
  `smart_irrigation/` (soil/water, IoT control), `crop_ai/`, `ai_agronomist/` (a real, dedicated Agro
  AI specialist module — `planning.py`, `services.py`, `facade.py`), `agro_finance/`,
  `controlled_environment/` (greenhouse/livestock), `enterprise_certification/`, `supply_chain/`.
- **`applications/agro_marketplace/`** — `crm/engine.py`, `marketplace.py`, `logistics/`,
  `product_catalog/`, `analytics/`, `export/`, `dashboards/`, `farmers/`, `harvest/`, `portal/`,
  `documents/`, `calendar/`, `partner_api/`. Complementary to `agro_enterprise`, not identical — same
  relationship as `port_enterprise`'s freight/customs modules were to `port_erp`.
- Both have `shared/store.py` (in-process `EntityStore`), are mounted live in `api/server.py`
  (`register_agro_enterprise_routes`, `register_agro_marketplace_routes`), and are undocumented in
  `docs/APPLICATIONS.md` beyond a single one-line "Agro Marketplace — `/api/agro/v1`" row that doesn't
  mention `agro_enterprise` at all.

**CONFIRMED (Decision 6).** `agro_enterprise` is canonical. Migrate all unique/useful functionality
from `agro_marketplace` into it — CRM, marketplace, logistics, trading/commercial workflows, and
anything else not already in `agro_enterprise` (product catalog, export, portal, dashboards, farmers,
harvest, calendar, partner API). No deletion of working functionality. No two competing Agro
implementations after migration. Compatibility preserved during migration; merge covered by
regression tests — same discipline as Decision 2's Port merge.

**Agro Fields/Maps workspace — confirmed required functionality** (Sprint 47.8, built on 47.5.3's
persisted `agro_enterprise.precision_agriculture.fields_gis`): farmer fields; map-based field
visualization; field coordinates/boundaries; field area/size; field cards; crop information; field
status; related tasks; documents; analytics; role-based access. This list is now binding scope for
47.8, not just a pointer to the existing `fields_gis.py` module.

### NF-2. Crypto AI specialists already exist as real code — confirmed
`applications/crypto_enterprise/` is real, mounted live in `api/server.py`
(`register_crypto_enterprise_routes`), and has a dedicated **`ai_trader/`** module (the Crypto AI
specialist), plus `market_intelligence/`, `technical_analysis/`, `strategy_engine/`,
`risk_management/`, `onchain_intelligence/`, `market_microstructure/`, `enterprise_certification/`.
Same `shared/store.py` in-memory pattern as every other app in this family. **No duplicate app** was
found for Crypto (unlike Port and Agro) — this is a single-app persistence-backfill case, not a
merge case. Test coverage for `crypto_enterprise` was not enumerated by the original audit passes;
must be inventoried before Sprint 47.5.4 starts (see Regression Gates).

### NF-3. This is now a recognized, repeating architecture pattern — six subtrees, not two
Combining the original CC-4 finding with NF-1/NF-2, the "real domain logic + real AI specialist
submodule + in-memory `EntityStore` + mounted live in `api/server.py` + zero Telegram bot wiring +
absent from CLAUDE.md/`docs/APPLICATIONS.md`" pattern recurs across **six** application subtrees:
`port_erp`, `port_enterprise`, `agro_enterprise`, `agro_marketplace`, `crypto_enterprise`,
`legal_enterprise`. This is a bigger, more valuable, and more mechanical piece of work than originally
scoped: Sprint 47.5 is not "persist two apps," it's "apply one persistence-backfill playbook four
times" (after the two merges in Decision 2 and NF-1 collapse six subtrees into four canonical ones:
`port_erp`, `agro_enterprise`, `crypto_enterprise`, `legal_enterprise`). It also means Sprint 47.2
("AI Specialist Agent UX") is substantially a *wiring* task, not a build-from-scratch task — three of
the four canonical apps already contain a real, non-trivial AI specialist implementation
(`ai_trader`, `ai_agronomist`, and Port's `executive_ai`/`ai_port_director` post-merge) that just needs
a common findings/recommendations/tasks/reports/reminders/objectives/comparison shape wrapped around
it, reusing `platform_ai_business_advisor`'s already-correct shape (per the original D2 finding) as
that common wrapper.

### NF-4. Content/production has a partial precedent
`services/pg_content_factory_engine.py` exists and is relevant to Decision 4's "content/production"
requirement for the Travel workspace — worth auditing in detail at the start of Sprint 47.4.2 rather
than building new content-generation infrastructure. No dedicated SEO-data-provider or
competitor-monitoring module was found anywhere in the repo — both are genuinely new provider
interfaces, but fit the same `platform_integrations/ConnectorBase` pattern as GA4/GTM/Meta (Sprint
47.4.1 covers all of them together, not as separate systems).

---

## Cross-cutting findings (apply to more than one sprint)

Unchanged from the prior round except where noted; CC-4 is superseded by NF-3 above.

- **CC-1 (naming).** Resolved by Decision 5: `tenant_id` is canonical going forward.
- **CC-2 (vertical registry).** `platform_registry/verticals/__init__.py`'s 12-vertical
  `VERTICAL_REGISTRY` is canonical; `container.py:97`'s independent 5-vertical hardcoded list
  (`auto, agro, realty, legal, logistics` — `realty`/`logistics` don't even exist in the registry)
  must be corrected to match in Sprint 47.0.
- **CC-3 (AI scoping is cosmetic today).** `ContextualAiChat.tsx:114` hardcodes `role: "owner"`;
  server-side `platform_ai_command` only gates at the endpoint level and never filters *data* by
  tenant/vertical. Fixed in Sprint 47.0, and is a hard prerequisite for Decision 1's memory scopes
  and Rule 5 ("tenant isolation must be enforced server-side") to mean anything in practice.
- **CC-4 → superseded by NF-3.** See above: four canonical app subtrees, not two, need the
  persistence-backfill treatment.

---

## Final dependency / order map

```
47.0 Foundation (tenant_id, vertical registry, typed AgentContext, server-side AI scoping)
  │
  ├──> 47.1 AI Memory Architecture (5 scopes)
  │
  ├──> 47.2 AI Specialist Agent UX (generic findings/recommendations/tasks/reports/
  │         reminders/objectives/comparison shape; wires existing ai_trader/ai_agronomist/
  │         executive_ai once their apps are persisted)
  │
  └──> [independent] 47.3 File storage fix + Contract/Document Center foundation
            │
            └──> 47.7 Legal Action Hub UI  ◄────────────────────────────┐
                                                                          │
[independent of 47.0] 47.4.1 Travel Marketing Connectors                │
  │                                                                      │
  └──> 47.4.2 Travel Vertical Workspace UI (needs 47.2 for specialists, │
              47.4.1 for connector data)                                │
                                                                          │
47.5 Persistence backfill playbook (needs Decision 2 + NF-1 merge      │
     decisions settled first):                                          │
  47.5.1 Port  (port_erp ⇐ port_enterprise merge, then persist) ──> 47.6 Port/Maritime Hub
  47.5.2 Legal (legal_enterprise persist)  ─────────────────────────────┘
  47.5.3 Agro  (agro_enterprise ⇐ agro_marketplace merge, then persist) ──> 47.8 Agro Fields/Maps + Workspace
  47.5.4 Crypto (crypto_enterprise persist, no merge needed) ──> 47.9 Crypto AI Specialist Wiring
```

**Reading this map:** 47.0 blocks 47.1, 47.2, and (for its server-side-scoping half) everything that
touches AI responses. 47.3 is independent of 47.0 and can start immediately — it's pure storage/data
model work with no AI-scoping dependency. 47.4.1 (connectors) is fully independent and can also start
immediately. 47.5's four sub-items depend only on their respective merge decision (Decision 2 for
Port, NF-1 for Agro — **NF-1 needs your explicit confirmation before 47.5.3 starts**; Legal and Crypto
have no merge decision pending and can start as soon as 47.5 opens). 47.6/47.7/47.8/47.9 are each
gated on their own 47.5.x sub-item plus 47.2 (for the specialist-wiring half of each Hub). 47.4.2
needs both 47.4.1 and 47.2. Everything in 47.5.x–47.9 can run **in parallel across verticals** once
their individual prerequisite lands — there's no reason Port, Legal, Agro, and Crypto backfill/Hub
work needs to be serialized against each other, only against their own dependencies.

**Recommended start order** (respecting the graph, prioritizing spec-explicit items first): 47.0 →
{47.1, 47.2, 47.3, 47.4.1} in parallel → 47.5.1 (Port) and 47.5.2 (Legal) in parallel → 47.6 and 47.7
in parallel → {47.5.3 (Agro), 47.5.4 (Crypto), 47.4.2 (Travel UI)} in parallel → {47.8, 47.9}.

---

## Migrations and compatibility risks

| Migration | Risk | Mitigation |
|---|---|---|
| `organization_id`/`company_id` → `tenant_id` rename across `platform_memory` (Decision 5) | Silent data-scope bugs if any read path still filters on the old field name after writes move to the new one | Additive migration: add `tenant_id` column alongside existing fields, backfill from `organization_id`/`company_id`, dual-write during a transition window, cut reads over only after backfill is verified row-count-equal, drop old columns in a separate later migration — never a single-step rename |
| `container.py`'s vertical list (`auto, agro, realty, legal, logistics`) → `platform_registry/verticals` (CC-2) | Anything silently relying on `container.py`'s wrong list (incl. `realty`/`logistics`, which aren't real verticals) breaks if not audited first | Grep every call site of `container.py`'s vertical list before changing it; confirm nothing depends on the phantom `realty`/`logistics` entries in production before removing them |
| `port_enterprise` → `port_erp` merge (Decision 2) | Losing freight_marketplace/multimodal_logistics/customs_trade/warehouse_distribution functionality, or breaking `port_enterprise`'s existing API consumers, during merge | Migrate module-by-module behind the existing `port_erp` route namespace, keep `port_enterprise`'s routes live and pointed at the migrated code (not deleted) until full regression parity is confirmed, only then deprecate the shell |
| `agro_marketplace` → `agro_enterprise` merge (NF-1, pending your confirmation) | Same shape of risk as above, plus this decision hasn't been explicitly confirmed yet | Do not start until you confirm NF-1's resolution, same merge discipline as Port once confirmed |
| `EntityStore` (in-memory) → Postgres for all four canonical apps (47.5.x) | Data loss on deploy (in-memory state doesn't survive a migration cutover by definition — there's no "existing data" to preserve, but there IS existing *behavior/contract* to preserve); API response-shape drift breaking existing frontend consumers (`legalWorkflow.ts` does real fetches today) | Schema-first: write the new SQLAlchemy models to exactly match `shared/models.py`'s existing dataclass shapes before touching the service layer, so the API contract doesn't change; run the existing test suites (below) against the new DB-backed services before switching `api/server.py` registration over; feature-flag the cutover per app so it can be reverted per-vertical, not all-or-nothing |
| Telegram bot wiring for Port/Agro-fields/Crypto-specialist surfaces (new, none of these are in `handlers.py`/`bot.py`/`keyboards.py` today per the original audit) | None — this is additive, no existing bot behavior touches these domains today | Standard new-router addition following `startup.py::BOT_ROUTER_PATHS` convention; no compatibility risk since nothing currently exists to break |
| `services/media_service.py::store_telegram_file` fix (47.3) | Existing call sites (`routers/realty_router.py:261` etc.) currently silently no-op (`stored: False`) inside a swallowed try/except — fixing the storage layer changes their behavior from "silently does nothing" to "actually stores a file," which could surface previously-hidden failure modes (disk space, permissions) at those call sites for the first time | Audit and test every existing call site of `store_telegram_file` before shipping the fix, not just the new Contract/Document Center's call site |

---

## Regression-test gates per sprint

A sprint is not done until its own new tests pass **and** the listed existing suite(s) stay green.

| Sprint | Must stay green |
|---|---|
| 47.0 | `tests/test_vertical_nav_46_5.py` (30/30 — do not regress Sprint 46.x work); any existing `platform_ai_command`/`platform_memory` test files (inventory exact filenames before starting — not enumerated by the original audit, close this gap first) |
| 47.1 | Same `platform_memory` suite inventory as 47.0, plus new scope-enforcement tests |
| 47.2 | `tests/test_ai_business_advisor_22_1.py` (must still pass once wired into `platform_ai_command`) |
| 47.3 | Every existing caller of `services/media_service.py::store_telegram_file` (`routers/realty_router.py` and any others found by a full grep — inventory before starting) |
| 47.4.1 | None identified yet (net-new connector code) — but confirm no existing test asserts today's UTM-only capture behavior in `services/start_payload_parser.py` in a way the new webhook path would violate |
| 47.4.2 | Sprint 42.8/46.6 vertical-workspace test suites (`sprint_42_8_vertical_workspaces.test.ts`, `sprint_46_6_onboarding_workspace_transition.test.tsx`) — the new Travel workspace must not regress the render-loop fix or the vertical catalog contract |
| 47.5.1 (Port) | `tests/test_port_erp.py`, `test_port_enterprise*.py`, `test_container_management_15_2.py`, `test_freight_marketplace_15_6.py`, `test_multimodal_logistics_15_3.py`, `test_ai_port_director_15_7.py`, `test_port_tracking.py`, `test_port_customs.py`, `test_port_finance.py`, `test_port_terminal.py` |
| 47.5.2 (Legal) | Any existing `applications/legal_enterprise` test files (inventory exact filenames — not enumerated by the original audit) plus `src/web/workspace/legal/legalWorkflow.ts`'s consuming frontend tests if any exist |
| 47.5.3 (Agro) | `tests/test_agro_enterprise_14_0.py`, `test_agro_enterprise_certification_14_8.py`, `test_agro_finance_14_6.py`, `test_ai_agronomist_14_7.py`, `test_agro_marketplace.py`, `test_agro_catalog.py`, `test_agro_crm.py`, `test_agro_analytics.py`, `test_agro_export.py`, `test_agro_portal.py`, `test_agro_release.py`, `test_agro_ai.py` |
| 47.5.4 (Crypto) | Test inventory for `applications/crypto_enterprise` not yet done — **must be completed as the first step of 47.5.4**, before any migration code is written, per Rule 4 ("no destructive migrations without compatibility and regression coverage") |
| 47.6–47.9 | Bot-side: full `pytest tests/ -q -m "not slow"` plus the security suite (`test_management_security.py`, `test_api_v1_freeze.py`, `test_admin_security.py`) per CLAUDE.md's standard sprint-close gate, since these sprints add new bot routers and management-surface endpoints |

---

## Reuse vs. modify vs. deprecate

| Module | Disposition | Sprint |
|---|---|---|
| `platform_memory/`, `memory_permissions.py`, `continuity_store.py`, `project_memory_models.py` | **Modify** — add scope enum + tenant_id migration | 47.0/47.1 |
| `platform_orchestrator/models.py` (`AgentContext`) | **Modify** — add typed tenant/vertical/customer fields | 47.0 |
| `container.py` (vertical list) | **Modify** — correct to match `platform_registry/verticals` | 47.0 |
| `platform_ai_command/api/router.py`, `ContextualAiChat.tsx` | **Modify** — real server-side scoping enforcement | 47.0 |
| `platform_ai_business_advisor/` | **Reuse as-is**, wired in rather than rebuilt | 47.2 |
| `AiCommandCenterPanel.tsx` fake agent list | **Modify** — replaced with real `platform_agents/registry.py` data | 47.2 |
| `applications/*/ai_trader`, `ai_agronomist`, `executive_ai`/`ai_port_director` | **Reuse**, wrapped in the common specialist shape from 47.2 | 47.2, 47.8, 47.9 |
| `src/platform/storage/` (`LocalStorage`/`S3Storage`) | **Modify** — actually wire `services/media_service.py` to call them | 47.3 |
| `database/models/automotive_operations.py` (`VehicleAttachment`) pattern | **Reuse as template**, generalized into a new `Attachment` model | 47.3 |
| `platform_integrations/` (`ConnectorBase`, `connector_loader`, `extended_provider_catalog`) | **Reuse as-is**, extended with new provider types | 47.4.1, and later the AIS/tracking + OCR connectors |
| `services/pg_lead_engine.py`, `pg_marketing_analytics_v1.py`, CRM pipeline engines | **Reuse as-is** (already UTM/vertical-ready) | 47.4.1 |
| `services/pg_content_factory_engine.py` | **Reuse**, audited for Travel content/production needs | 47.4.2 |
| `applications/port_erp/` | **Canonical — modify** (gains persistence + `port_enterprise`'s unique modules) | 47.5.1 |
| `applications/port_enterprise/` | **Deprecate** (app shell only, after safe migration) | 47.5.1 |
| `applications/agro_enterprise/` | **Canonical — modify** (gains persistence + `agro_marketplace`'s unique modules) — *pending your confirmation of NF-1* | 47.5.3 |
| `applications/agro_marketplace/` | **Deprecate** (app shell only, after safe migration) — *pending your confirmation of NF-1* | 47.5.3 |
| `applications/legal_enterprise/` | **Modify** — gains persistence, no merge needed | 47.5.2 |
| `applications/crypto_enterprise/` | **Modify** — gains persistence, no merge needed | 47.5.4 |
| `services/vertical_nav_service.py::_enter_legal`, existing Legal Telegram menus | **Reuse as-is** — access rules preserved verbatim per spec item 6 | 47.7 |
| `docs/APPLICATIONS.md`, CLAUDE.md's application list | **Modify** — document all four canonical app subtrees (currently missing entirely) | 47.5 (all sub-items) |

---

## Explicit verification — spec items represented in this plan

| Requested item | Where it lands |
|---|---|
| Agro fields/maps | `applications/agro_enterprise/precision_agriculture/fields_gis.py` already exists — persisted in 47.5.3, exposed via the vertical workspace in 47.8 |
| Port/Maritime | 47.5.1 (persistence, canonical `port_erp`) + 47.6 (Hub UI + bot wiring) |
| Contract/Documents | 47.3 (foundation: real file storage + generic Contract/Attachment models) + 47.7 (Legal Hub consumes it) |
| Crypto AI specialists | `applications/crypto_enterprise/ai_trader/` already exists (NF-2) — persisted in 47.5.4, wrapped in the common specialist shape and surfaced in 47.9 |
| Travel marketing/production | 47.4.1 (connectors) + 47.4.2 (first-class workspace UI, including content/production via `pg_content_factory_engine.py`) |
| Role-specific vertical workspaces | Rule 10 applies across every UI-facing sprint (47.4.2, 47.6, 47.7, 47.8, 47.9) — each reuses the existing `VerticalWorkspacePage`/persona pattern from Sprint 42.8/46.x rather than inventing new role-gating per vertical |
| AI memory architecture | 47.0 (foundation) + 47.1 (the five scopes) |

---

## What this plan deliberately does not do yet

All architectural decisions (1–6, including NF-1/Decision 6) are now confirmed. Each sprint gets its
own `docs/SPRINT_47_X_RESULT.md` on completion, recording implementation outcome, test results, and
anything discovered mid-sprint that required a call not anticipated here.

**Implementation status:** Sprint 47.0 — **complete**, see `docs/SPRINT_47_0_RESULT.md` (zero
regressions; 47.1 judged safe to start). Sprint 47.1 — **complete**, see
`docs/SPRINT_47_1_RESULT.md` (zero regressions beyond one self-inflicted, immediately-fixed
alembic-head test update; 47.2 judged safe to start). 47.2 onward not started; require explicit
approval per sprint before starting, per instruction.

**Note (added retroactively during Sprint 48.1's verification, 2026-08-10):** Sprints 48.0 and 48.1
— Crypto/OTC transaction idempotency & duplicate-payout protection — were built and are complete,
but are **not part of this plan's numbering or dependency graph**. They are an independent
initiative (security-hardening for the existing crypto/OTC deal flow), not a continuation of 47.x's
multi-domain expansion work; they neither depend on nor block 47.2+. See `docs/SPRINT_48_0_RESULT.md`
and `docs/SPRINT_48_1_RESULT.md` for their own scope, decisions, and test evidence — recorded there
rather than here because they don't fit this document's dependency map. Sprint 48.0 was originally
built without a RESULT doc, roadmap entry, or explicit per-sprint approval, unlike every sprint
above; Sprint 48.1's verification pass closed that gap retroactively. 47.2 remains not started and
still requires explicit approval before starting, unaffected by 48.0/48.1.
