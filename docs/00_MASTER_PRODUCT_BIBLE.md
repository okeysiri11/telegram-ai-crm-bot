# The ADOS Product Bible

**Status:** permanent, living, single source of truth. This is the entry point for every future
sprint, feature, AI agent, and developer working on the ADOS Enterprise Platform. Read this document
first; it tells you which of the platform's other documents to read next, and why each one exists.

**A note on how this Bible was built:** it was written by reading the platform's existing deep
specifications — `ARCHITECTURE_MAP.md`, `ENTERPRISE_DESIGN_SYSTEM.md`, `ENTERPRISE_CITY.md`,
`ENTERPRISE_NAVIGATION.md`, `WORKSPACE_INTERACTIONS.md`, `AI_PRODUCTION_STUDIO.md`, the EP-series sprint
records, and `CLAUDE.md` — and connecting them, never duplicating them. One correction made along the
way: the two EP-series filenames referenced when this Bible was commissioned
(`EP_02_ENTERPRISE_LANGUAGE.md`, `EP_03_DESIGN_LANGUAGE.md`) do not exist under those exact names; the
real files are `docs/EP_02_ENTERPRISE_DESIGN_LANGUAGE.md` and `docs/EP_03_MOTION_DESIGN_LANGUAGE.md`.
This Bible references the real filenames throughout, and the mismatch itself is recorded as a
documentation gap below (§5).

**Sprint 27.7–27.9 update (real implementation landed since this Bible was first written):** an
Enterprise Desktop OS shell (`DESKTOP.md`, `WINDOW_MANAGER.md`), a restructured Enterprise City core
with a real camera engine and 12 real districts (`ENTERPRISE_CITY_CORE.md`, `CITY_ENGINE.md`,
`CITY_DISTRICTS.md`), and an AI Production Center frontend shell with a real approval-gated pipeline
(`PRODUCTION_CENTER.md`, `PRODUCTION_AUTOMATION.md`, `AI_PRODUCTION_CENTER_ARCHITECTURE.md`,
`PROMPT_LIBRARY.md`, `MEDIA_MANAGER.md`) are now real, shipped code — not vision. Three new Bible-tier
documents (`docs/ENTERPRISE_CITY_BIBLE.md`, `docs/AI_PRODUCTION_CENTER_BIBLE.md`,
`docs/AI_AGENTS_BIBLE.md`) and one cross-cutting guide (`docs/UX_GUIDELINES.md`) now sit above these —
§1's tier list and §2's dependency graph below reflect the new structure.

---

## How to read this Bible

This document has three jobs: **orient** (what is ADOS, what does this documentation set cover),
**index** (ten numbered chapters, each a short connecting summary pointing to the deep specification
it summarizes), and **close the loop** (a full document inventory, a dependency graph, honestly-stated
gaps, and recommendations). It is deliberately short on detail — every claim of substance in this
document has a home in a more detailed chapter or spec, named at the point it's made.

## The ten chapters

| Chapter | Covers | Primary deep spec(s) |
|---|---|---|
| `01_VISION.md` | What ADOS is, why it exists, who it's for, the scale ambition | `ARCHITECTURE_MAP.md`, `ENTERPRISE_CITY.md` §1, §23 |
| `02_PRODUCT_PHILOSOPHY.md` | The nine governing principles common to every system in the platform | `CLAUDE.md`, every design/product spec |
| `03_ENTERPRISE_OS.md` | The "one operating system" concept — navigation, workspace, runtime, permissions as one coherent whole | `ENTERPRISE_NAVIGATION.md`, `WORKSPACE_INTERACTIONS.md` |
| `04_ENTERPRISE_CITY.md` | The spatial visual representation of the platform, its scaling model | `ENTERPRISE_CITY.md` (full, 23 sections) |
| `05_AI_PRODUCTION.md` | The creative production center — generation, governance, publishing | `AI_PRODUCTION_STUDIO.md` (full, 28 sections) |
| `06_DESIGN_LANGUAGE.md` | Visual and motion principles — how the vocabulary is composed | `docs/EP_02_ENTERPRISE_DESIGN_LANGUAGE.md`, `docs/EP_03_MOTION_DESIGN_LANGUAGE.md`, `ENTERPRISE_DESIGN_SYSTEM.md` |
| `07_DESIGN_SYSTEM.md` | The token implementation — exact colors, type, spacing, motion values | `ENTERPRISE_DESIGN_SYSTEM.md` (full, 18 sections) |
| `08_AI_PERSONALITY.md` | The Executive Advisor voice, the AI capability ecosystem, agent governance | `docs/EP_04_AI_PERSONALITY.md`, `ARCHITECTURE_MAP.md` §5 |
| `09_ARCHITECTURE.md` | Modules, verticals, marketplace, runtime, permissions, engineering governance | `ARCHITECTURE_MAP.md`, `DEPENDENCY_MAP.md`, `MODULES.md`, `API_MAP.md`, `TECH_DEBT.md` |
| `10_ROADMAP.md` | Sequenced long-term evolution across three horizons | Synthesizes every "vision"/"designed" section platform-wide |

**None of these ten chapters duplicates its deep spec.** Each is written to be readable in a few
minutes and to send the reader to the right full document for anything beyond a summary — this Bible's
own governing rule, applied to itself.

## The required-topics map

Every topic this Bible was commissioned to cover, and where it actually lives:

| Topic | Home chapter(s) |
|---|---|
| Product philosophy | `02_PRODUCT_PHILOSOPHY.md` |
| Enterprise vision | `01_VISION.md` |
| Operating system concept | `03_ENTERPRISE_OS.md` |
| Workspace philosophy | `03_ENTERPRISE_OS.md`, `WORKSPACE_INTERACTIONS.md` |
| Enterprise City philosophy | `04_ENTERPRISE_CITY.md` |
| AI ecosystem / AI agents | `08_AI_PERSONALITY.md` |
| Production Studio | `05_AI_PRODUCTION.md` |
| Design Language | `06_DESIGN_LANGUAGE.md` |
| Design System | `07_DESIGN_SYSTEM.md` |
| Navigation principles | `03_ENTERPRISE_OS.md`, `ENTERPRISE_NAVIGATION.md` |
| Interaction rules | `WORKSPACE_INTERACTIONS.md` |
| Accessibility | `06_DESIGN_LANGUAGE.md` |
| Motion language | `06_DESIGN_LANGUAGE.md` |
| Visual language | `06_DESIGN_LANGUAGE.md`, `07_DESIGN_SYSTEM.md` |
| Enterprise UX | `06_DESIGN_LANGUAGE.md` |
| Modules / verticals / marketplace | `09_ARCHITECTURE.md` |
| Enterprise collaboration | `WORKSPACE_INTERACTIONS.md` §20–§24, `08_AI_PERSONALITY.md` |
| Permissions | `03_ENTERPRISE_OS.md`, `09_ARCHITECTURE.md` |
| Runtime | `03_ENTERPRISE_OS.md`, `09_ARCHITECTURE.md` |
| Roadmap / long-term evolution | `10_ROADMAP.md` |

---

## 1. Summary of all documents

The platform's documentation forms four tiers. This Bible and its ten chapters are Tier 1; everything
below feeds them.

### Tier 0 — This Bible
`00_MASTER_PRODUCT_BIBLE.md` — this document.

### Tier 1 — The ten connecting chapters
`01_VISION.md` · `02_PRODUCT_PHILOSOPHY.md` · `03_ENTERPRISE_OS.md` · `04_ENTERPRISE_CITY.md` ·
`05_AI_PRODUCTION.md` · `06_DESIGN_LANGUAGE.md` · `07_DESIGN_SYSTEM.md` · `08_AI_PERSONALITY.md` ·
`09_ARCHITECTURE.md` · `10_ROADMAP.md` (all described in the table above).

### Tier 1.5 — The subsystem Bibles (canonical authority for one subsystem, above its own Tier 2 specs)
- `ENTERPRISE_CITY_BIBLE.md` — canonical authority for Enterprise City; sits above
  `ENTERPRISE_CITY_ARCHITECTURE.md`, `ENTERPRISE_CITY_STATES.md`, `ENTERPRISE_CITY_ANIMATIONS.md`,
  `ENTERPRISE_CITY_UI_RULES.md`, and the real-implementation docs `ENTERPRISE_CITY_CORE.md`,
  `CITY_ENGINE.md`, `CITY_DISTRICTS.md`.
- `AI_PRODUCTION_CENTER_BIBLE.md` — canonical authority for the AI Production Center; sits above
  `PRODUCTION_CENTER.md`, `PRODUCTION_AUTOMATION.md`, `AI_PRODUCTION_CENTER_ARCHITECTURE.md`,
  `PROMPT_LIBRARY.md`, `MEDIA_MANAGER.md`, and `AI_PRODUCTION_STUDIO.md`'s full vision spec.
- `AI_AGENTS_BIBLE.md` — canonical authority for the AI agent ecosystem across every surface
  (Executive Advisor, Production Center studio agents, City building AI labels, the backend agent
  stack).
- `DESKTOP.md`, `WINDOW_MANAGER.md` — the real Enterprise Desktop OS shell this Bible's `03_
  ENTERPRISE_OS.md` chapter now describes as shipped, not aspirational (see §0's Sprint update note).
- `UX_GUIDELINES.md` — a practical, checklist-style companion to `06_DESIGN_LANGUAGE.md`/
  `07_DESIGN_SYSTEM.md` for anyone (human or AI agent) building a new Enterprise OS surface.

### Tier 2 — The deep specifications (product & design)
- `ENTERPRISE_DESIGN_SYSTEM.md` — the full token/component/motion canon (18 sections).
- `ENTERPRISE_CITY.md` — the full spatial-platform specification, 2D shipped + 3D vision (23 sections);
  now a real-implementation companion to `ENTERPRISE_CITY_BIBLE.md` rather than the sole authority.
- `ENTERPRISE_NAVIGATION.md` — the full navigation philosophy, including the two-command-palette
  finding (22 sections).
- `WORKSPACE_INTERACTIONS.md` — the full interaction pattern language (25 sections).
- `AI_PRODUCTION_STUDIO.md` — the full creative-production **vision** specification (28 sections) —
  read alongside `AI_PRODUCTION_CENTER_BIBLE.md`'s status-honest account of what's actually shipped.

### Tier 2 — The deep specifications (engineering & architecture)
- `ARCHITECTURE_MAP.md` — complete architecture map: repo tree, backend/frontend architecture,
  providers, AI runtime, MCP, voice, memory, kernel, dependencies, tech debt, duplicates, legacy,
  missing integrations, high-priority improvements.
- `DEPENDENCY_MAP.md` — the module dependency graph, direction, and cycle analysis.
- `MODULES.md` — the per-module catalog (owner, public API, dependencies, status, debt, plans).
- `API_MAP.md` — the concrete endpoint-level API inventory (REST/WS/MCP/events/internal services).
- `TECH_DEBT.md` — the living technical-debt registry (TD-01 through TD-60 as of this writing; see
  `SPRINT_CQ_30_6_ARCHITECT_REVIEW.md` for the most recent independent review and its own ranked
  `TECH_DEBT_V2.md`/`TOP_50_IMPROVEMENTS.md` snapshots — both views over this same canonical registry,
  not competing ones).

### Tier 3 — The engineering handbook
`CLAUDE.md` — the permanent engineering manual: commands, backend/frontend architecture orientation,
sprint workflow, and the engineering philosophy this Bible's `02_PRODUCT_PHILOSOPHY.md` generalizes to
product decisions.

### Tier 4 — Historical sprint records (not part of the active reading path)
`docs/EP_01_EXECUTIVE_EXPERIENCE.md` through `docs/EP_08_GA_READINESS.md`, `docs/EP_05_ENTERPRISE_
CITY.md`, `docs/ENTERPRISE_CITY_32_3_3.md`, `docs/TECHNICAL_DEBT_REPORT.md`, `docs/ARCHITECTURE_
INVENTORY.md`, and the ~950 further sprint/dashboard/audit documents under `docs/` (Sprint 1.0 through
34.2, per `docs/ARCHITECTURE_AUDIT_INDEX.md`). These are real, valuable historical records — self-
assessment scores, per-sprint change inventories, the original specs Tier 1/2 documents consolidated —
but they are **not** where a new contributor or AI agent should start. If a Tier 4 document and a Tier
1/2 document disagree, the Tier 1/2 document is current; the Tier 4 document is the historical record
of how the platform arrived there.

---

## 2. Document dependency graph

```
                         00_MASTER_PRODUCT_BIBLE.md
                                    │
        ┌─────────────┬────────────┼────────────┬─────────────┐
        ▼             ▼            ▼            ▼             ▼
  01_VISION    02_PHILOSOPHY  03_ENTERPRISE_OS  06_DESIGN_LANG  09_ARCHITECTURE
        │             │            │            │             │
        │             │            │            │             ▼
        │             │            │            │      ARCHITECTURE_MAP.md
        │             │            │            │      DEPENDENCY_MAP.md
        │             │            │            │      MODULES.md
        │             │            │            │      API_MAP.md
        │             │            │            │      TECH_DEBT.md
        │             │            │            │             │
        │             │            ▼            ▼             │
        │             │    ENTERPRISE_NAVIGATION.md            │
        │             │    WORKSPACE_INTERACTIONS.md           │
        │             │            │            │             │
        │             │            │      07_DESIGN_SYSTEM ────┤
        │             │            │            │             │
        │             │            │      ENTERPRISE_DESIGN_SYSTEM.md
        │             │            │            │             │
        ▼             ▼            ▼            ▼             ▼
  04_ENTERPRISE_CITY.md ◄──── inherits design/motion canon ────┤
        │                                                       │
        ▼                                                       │
  ENTERPRISE_CITY.md (full spec)                                │
                                                                 │
  05_AI_PRODUCTION.md ◄──── inherits design canon + AI voice ───┤
        │                                                       │
        ▼                                                       │
  AI_PRODUCTION_STUDIO.md (full spec)                           │
                                                                 │
  08_AI_PERSONALITY.md ◄──── inherits from ────────────────────┘
        │
        ▼
  docs/EP_04_AI_PERSONALITY.md

  10_ROADMAP.md ◄──── synthesizes every "vision" section above,
                       gated by CLAUDE.md's sequencing rule
```

**How to read this graph:** everything flows from `02_PRODUCT_PHILOSOPHY.md` and
`07_DESIGN_SYSTEM.md`/`06_DESIGN_LANGUAGE.md` — no Tier-2 spec defines its own visual language,
motion rule, or governance principle independently; each inherits from these two. `09_ARCHITECTURE.md`
is the one chapter whose dependencies point at engineering documents rather than product/design ones —
it is the seam between "what the product is" and "what actually runs."

---

## 3. Documentation gaps

Stated plainly, per this Bible's own principle of never blurring what exists with what's aspirational:

1. **The two EP-series filenames this Bible was commissioned to read do not exist under those names**
   (see the correction note at the top of this document) — a small but real signal that even this
   platform's own commissioning process can drift from the real filenames; no automated check catches
   a documentation reference to a file that doesn't exist.
2. **No formal Architecture Decision Record (ADR) log.** `CLAUDE.md` requires every architectural
   decision to be documented, but the only prescribed location is a sprint's own `RESULT.md` — there is
   no single, searchable decision history. The clearest example of this gap's cost:
   `ARCHITECTURE_MAP.md` §15 identifies the TypeScript kernel ecosystem's relationship to the rest of
   the platform as an unresolved, undocumented decision (`TECH_DEBT.md` TD-33) — precisely the kind of
   decision an ADR log exists to prevent from going missing.
3. **A term collision this Bible surfaced while writing itself: "Portal."** `ENTERPRISE_CITY.md` §12
   defines a Portal as a governed gateway between two organizations' cities. `src/web`'s real
   `PortalPages.tsx` (`CustomerPortalPage`/`EmployeePortalPage`/`OwnerPortalPage`) uses "portal" to mean
   a role-scoped landing area within one organization — an unrelated concept sharing one word. No
   glossary exists to catch or prevent this kind of collision platform-wide.
4. **No accessibility conformance report.** WCAG AA is stated as the platform's standard
   (`ENTERPRISE_DESIGN_SYSTEM.md` §1, `06_DESIGN_LANGUAGE.md`) but no audit document confirms actual
   conformance anywhere in the codebase — the standard is declared, not verified.
5. **No centralized internationalization/localization strategy.** Language policy is referenced
   piecemeal — City chrome in RU/UA (`ENTERPRISE_CITY.md` §4), Dashboard/Concierge in English
   (`08_AI_PERSONALITY.md`'s language-policy table) — with no single document explaining the overall
   i18n architecture, why these specific surfaces diverge, or how a new locale would be added.
6. **No deployment/runtime operations runbook.** `TECH_DEBT.md` TD-14 already tracks that the dual bot
   +API runtime has no unified deploy story (`docker-compose.yml` defines only `postgres`+`redis`); this
   Bible's `09_ARCHITECTURE.md` restates the gap but a real runbook doesn't exist to close it.
7. **No consolidated OpenAPI index.** `TECH_DEBT.md` TD-13 tracks uneven OpenAPI coverage across
   Platform Builder and the verticals; `API_MAP.md` documents real endpoints by direct code reading, but
   no generated, browsable API reference exists for external consumers.
8. **No data-privacy/consent-governance document.** `AI_PRODUCTION_STUDIO.md` §7/§6 introduces hard
   consent-record requirements for avatar/voice-likeness generation — a real, load-bearing governance
   rule with no home document describing data retention, consent-record lifecycle, or regulatory
   posture beyond the Studio spec's own brief mention.
9. **No test/QA strategy document tying UI/UX quality to this Bible's principles.** `platform_testing`/
   `platform_quality` exist as backend capability packages (`MODULES.md` §3), but nothing connects "is
   this feature accessible, calm, and on-brand" (this Bible's stated bar) to an actual test/review
   checklist a contributor or AI agent would follow before shipping — `UX_GUIDELINES.md` narrows this
   gap for interaction/visual quality specifically, but a full test-and-review process remains open.
10. **Documentation is now tracking a moving target.** Real implementation (Enterprise Desktop, City's
    12-district restructure, the Production Center shell) is landing in parallel with this
    documentation effort, sprint by sprint, from a separate development process. This Bible and its
    Tier 1.5 subsystem Bibles are current **as of this writing** — the fastest-drifting risk in this
    entire documentation set is no longer a stale filename reference (gap #1), it is this Bible's
    "shipped vs. vision" status claims falling behind real code. Re-verify status honesty against the
    actual repository before trusting any "vision, not shipped" claim in a Tier 1.5 Bible that is more
    than a few sprints old.

## 4. Recommendations for future documentation

In rough priority order, following `10_ROADMAP.md`'s own horizon logic:

1. **Write a canonical Glossary** (`docs/GLOSSARY.md`) — resolve the "Portal" collision (§3.3) and
   define every term this Bible's chapters introduce or reuse (District, Building, Enterprise, Dock,
   Studio, Director, Advisor) once, in one place, so future documents can link to a definition instead
   of re-explaining or silently diverging.
2. **Start a real ADR log** (`docs/decisions/` or a single `docs/ARCHITECTURE_DECISIONS.md`) — close
   gap §3.2, and use it immediately to record the TypeScript kernel ecosystem's intended relationship
   to the rest of the platform (`TECH_DEBT.md` TD-33), which is this platform's most consequential
   undocumented decision today.
3. **Write the i18n/localization strategy document** (gap §3.5) — before any further locale-specific
   work (e.g. Enterprise City's RU/UA chrome, §3.5) expands, so future language decisions have a
   documented rationale to extend rather than another ad hoc per-surface choice.
4. **Write the deployment/runtime runbook** (gap §3.6, `TECH_DEBT.md` TD-14) — a prerequisite for any
   serious production rollout beyond the current dev/pilot posture.
5. **Commission an accessibility conformance audit and publish its report** (gap §3.4) — turning the
   platform's stated WCAG AA standard from a claim into a verified fact.
6. **Write the data-privacy/consent-governance document** (gap §3.8) — before the Production Studio's
   avatar/voice-cloning modules (`05_AI_PRODUCTION.md`) move from vision to build, since their consent
   model needs a real governance home, not just a spec-level mention.
7. **Generate and publish a consolidated OpenAPI index** (gap §3.7, `TECH_DEBT.md` TD-13) — once the
   Publishing Center and other Horizon-2 API surfaces (`10_ROADMAP.md`) land, so external/partner
   integration has one reliable reference.
8. **Write a UI/UX test-and-review checklist** (gap §3.9) tying this Bible's principles
   (`02_PRODUCT_PHILOSOPHY.md`) directly to a pre-ship review process — the natural companion to
   `CLAUDE.md`'s existing build/lint/test sprint-closeout requirement, extended to product quality.

## Closed Beta status (Sprint 31.0)

Enterprise Web Closed Beta RC is documented in [`CLOSED_BETA.md`](./CLOSED_BETA.md),
[`FIRST_RUN.md`](./FIRST_RUN.md), [`DEPLOYMENT.md`](./DEPLOYMENT.md), [`INSTALLATION.md`](./INSTALLATION.md),
[`OPERATOR_GUIDE.md`](./OPERATOR_GUIDE.md), [`BETA_RELEASE_NOTES.md`](./BETA_RELEASE_NOTES.md), and
[`SPRINT_31_0_RESULT.md`](./SPRINT_31_0_RESULT.md). Russian UI remains the default locale
(`webConfig.defaultLocale = "ru"`). Architecture index: [`ARCHITECTURE_MAP.md`](./ARCHITECTURE_MAP.md)
(last verified **31.2** Integration Hub track; sprint ids collide with vertical pilots — see RESULT docs).

## Integration Hub & n8n (Sprint 31.2 deepen)

External connectors deepen [`INTEGRATION_HUB.md`](./INTEGRATION_HUB.md) (SPA bus + external hub section),
[`N8N_ARCHITECTURE.md`](./N8N_ARCHITECTURE.md), [`AI_PROVIDERS.md`](./AI_PROVIDERS.md),
[`PROVIDER_REGISTRY.md`](./PROVIDER_REGISTRY.md), [`WORKFLOW_LIBRARY.md`](./WORKFLOW_LIBRARY.md), and
[`SPRINT_31_2_RESULT.md`](./SPRINT_31_2_RESULT.md). **Hard rule:** Platform Runtime is the system of
record; n8n is external orchestration only — no business logic in n8n. AI calls go through APH.
(Legal Pilot also uses sprint id 31.2 — do not overwrite those docs.)

## AI Production Studio MVP (Sprint 32.0)

Operational Production Studio surfaces: [`PRODUCTION_STUDIO_V1.md`](./PRODUCTION_STUDIO_V1.md),
[`BRAND_KIT.md`](./BRAND_KIT.md), [`AI_PIPELINES.md`](./AI_PIPELINES.md),
[`SPRINT_32_0_RESULT.md`](./SPRINT_32_0_RESULT.md). Execution path is Enterprise Runtime + APH;
Workflow Builder UI does not replace [`WORKFLOW_ENGINE.md`](./WORKFLOW_ENGINE.md).
(Enterprise Web Completion also uses sprint id 32.0.)

## AgentOS (Sprint 32.1)

Unified multi-agent runtime on Enterprise Runtime: [`AGENT_OS.md`](./AGENT_OS.md),
[`AGENT_RUNTIME.md`](./AGENT_RUNTIME.md), [`AGENT_REGISTRY.md`](./AGENT_REGISTRY.md),
[`AGENT_COMMUNICATION.md`](./AGENT_COMMUNICATION.md), [`AGENT_MEMORY.md`](./AGENT_MEMORY.md),
[`AGENT_SECURITY.md`](./AGENT_SECURITY.md), [`SPRINT_32_1_RESULT.md`](./SPRINT_32_1_RESULT.md).
No isolated agents; n8n remains external-only. (External Pilot also uses sprint id 32.1; MAOS backend is Sprint 27.1.)

## Platform Core Governance (Sprint 32.2)

Composed Platform Core inventory, Architecture Governance merge gates, Pricing / USC foundations
(no UI): [`PLATFORM_CORE.md`](./PLATFORM_CORE.md), [`CORE_SERVICES.md`](./CORE_SERVICES.md),
[`ARCHITECTURE_GOVERNANCE.md`](./ARCHITECTURE_GOVERNANCE.md), [`PLATFORM_STANDARDS.md`](./PLATFORM_STANDARDS.md),
[`TECH_DEBT_REGISTRY.md`](./TECH_DEBT_REGISTRY.md), [`SPRINT_32_2_RESULT.md`](./SPRINT_32_2_RESULT.md).
(First External Pilot also uses sprint id 32.2 — Pilot docs untouched; CQ-32.2 review docs preserved.)

## Enterprise Consolidation (Sprint 32.3)

Canonical services, unified queues, secret policy, Event Bus mandate:
[`CANONICAL_SERVICES.md`](./CANONICAL_SERVICES.md), [`QUEUE_ARCHITECTURE.md`](./QUEUE_ARCHITECTURE.md),
[`EVENT_BUS.md`](./EVENT_BUS.md), [`SPRINT_32_3_RESULT.md`](./SPRINT_32_3_RESULT.md).
(UX track 32.3.1–32.3.7 docs preserved.)

## Enterprise Security Center (Sprint 32.4)

Zero Trust platform security SoR: [`SECURITY_CENTER.md`](./SECURITY_CENTER.md),
[`ZERO_TRUST.md`](./ZERO_TRUST.md), [`AI_AGENT_SECURITY.md`](./AI_AGENT_SECURITY.md),
[`ANTI_PARSING.md`](./ANTI_PARSING.md), [`SPRINT_32_4_RESULT.md`](./SPRINT_32_4_RESULT.md).
(AI OS Experience also uses sprint id 32.4 — Concierge docs untouched.)

## Closed Beta Launch (Sprint 32.5)

Launch readiness (no major new features): [`CLOSED_BETA_GUIDE.md`](./CLOSED_BETA_GUIDE.md),
[`FIRST_USER_JOURNEY.md`](./FIRST_USER_JOURNEY.md), [`RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md),
[`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md), [`SPRINT_32_5_RESULT.md`](./SPRINT_32_5_RESULT.md).
(Enterprise Intelligence also uses sprint id 32.5 — Intelligence docs untouched.)

## First Local Launch (Sprint 32.6A / 32.6B)

One-command local demo: [`LOCAL_RUN.md`](./LOCAL_RUN.md), [`FIRST_SUCCESSFUL_LOCAL_RUN.md`](./FIRST_SUCCESSFUL_LOCAL_RUN.md),
[`SPRINT_32_6B_RESULT.md`](./SPRINT_32_6B_RESULT.md). Command: `npm run dev:all`.
(AI Team Collaboration also uses sprint id 32.6 — Collab docs untouched.)

## 5. How this Bible stays alive

Per `CLAUDE.md`'s sprint-closeout rule, generalized: any sprint that changes product philosophy, ships
Horizon-1/2 roadmap work (`10_ROADMAP.md`), or resolves a documentation gap listed in §3 above should
update the relevant chapter in the same sprint, not as a follow-up. This Bible is only a single source
of truth for as long as it is kept current — a stale Bible is worse than no Bible, because it will be
trusted.
