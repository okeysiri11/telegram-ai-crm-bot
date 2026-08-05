# Architecture Decisions Backlog

**Status:** permanent, living backlog. Documentation only — no source code and no existing architecture
document has been modified to produce this file. `TECH_DEBT.md` is deliberately **not** touched by this
pass — it remains the living registry for code-level debt (TD-01 through TD-46); this backlog is a
different, complementary artifact: every **recommendation** scattered across
`PRODUCT_ARCHITECTURE_REVIEW.md`, `00_MASTER_PRODUCT_BIBLE.md` §4, `ENTERPRISE_AI_OS.md` §14,
`AI_PRODUCTION_CENTER_BIBLE.md` §10, `ENTERPRISE_CITY_ARCHITECTURE.md` §24, and `10_ROADMAP.md`,
collected into one place and given a consistent, sprint-ready shape. Where an item here also has a
`TD-##` code in `TECH_DEBT.md`, that code is cited so the two documents stay linked without duplicating
each other's content — this backlog answers "what should we decide/build and in what order," `TECH_
DEBT.md` answers "what's currently wrong with the code."

**How to use this backlog:** each item has seven fields — Problem, Impact, Proposed solution, Affected
modules, Implementation priority, Estimated complexity, Dependencies. Priority follows `TECH_DEBT.md`'s
existing vocabulary (P0 blocks/critical, P1 real risk, P2 worth doing, P3 cosmetic); complexity follows
its existing vocabulary (S <1 day, M 1–3 days, L 1–2 weeks, XL multi-sprint/needs an architectural
decision first). Items marked **ADR** are decisions to *write down*, not code to ship — they should be
resolved before their dependent items are scheduled.

---

## Index (priority order)

| ID | Title | Priority | Complexity |
|---|---|---|---|
| ADB-23 | Consent-record infrastructure before any avatar/voice provider | **P0** | M |
| ADB-01 | ADR: TS kernel ecosystem's relationship to the Python backend | P0 | M (decision only) |
| ADB-03 | ADR: City navigation hierarchy — resolve the Architecture/Bible disagreement | P0 | S (decision only) |
| ADB-48 | Promote sprint-self-admitted remaining-work items into `TECH_DEBT.md` | P0 | S |
| ADB-02 | ADR: Unify or formally separate the three "memory" stacks | P1 | M (decision only) |
| ADB-06 | ADR: Resolve the shared `/api/ai-os/v1` prefix collision | P1 | S (decision only) |
| ADB-38 | Canonical Glossary | P1 | M |
| ADB-07 | Wire frontend Runtime Engine to `platform_ai_os` Executive Dashboard | P1 | L |
| ADB-20 | Real Content Factory HTTP route | P1 | M |
| ADB-21 | Real Cross-Posting publish trigger + new channels | P1 | L |
| ADB-04 | ADR: Job-execution backend division of labor | P1 | S (decision only) |
| ADB-28 | Enterprise City building-catalog completeness audit | P1 | M |
| ADB-29 | Accessible List View as first-class parallel surface | P1 | L |
| ADB-39 | Formal ADR log | P1 | S |
| ADB-05 | ADR: Disambiguate the "Production" district | P1 | S (decision only) |
| ADB-22 | One real generation provider (single modality) | P2 | L |
| ADB-16 | Wire real Multi-Agent OS Collaboration protocol to a frontend consumer | P2 | L |
| ADB-17 | Wire real Task Orchestrator to a frontend consumer | P2 | L |
| ADB-24 | Real Brand Library data model | P2 | M |
| ADB-26 | Prompt Library / Creative Knowledge Base backed by real `/memory-layers` | P2 | M |
| ADB-30 | Role-aware building visibility (RBAC-scoped City buildings) | P2 | M |
| ADB-35 | Marketing / Production Manager / Designer Dashboard profiles | P2 | S |
| ADB-08 | Wire frontend Runtime Engine to `platform_jobs` | P2 | M |
| ADB-09 | Wire frontend Runtime Engine to `platform_observability` | P2 | M |
| ADB-10 | WebSocket-backed notification push into `notificationStore` | P2 | M |
| ADB-11 | Single health-poller singleton, fully driven through every consumer | P2 | S |
| ADB-13 | Backend integration-hub status endpoint | P2 | M |
| ADB-14 | Live building occupancy/presence from real job queues | P2 | M |
| ADB-15 | City camera URL sync (`?x=&y=&zoom=`) | P2 | S |
| ADB-42 | Accessibility conformance audit | P2 | L |
| ADB-43 | Data-privacy/consent-governance document | P2 | M |
| ADB-45 | UI/UX test-and-review checklist | P2 | S |
| ADB-46 | Write `VOICE_FIRST_ENTERPRISE.md` | P2 | M (docs only) |
| ADB-47 | Write `FUTURE_RUNTIME.md` | P2 | M (docs only) |
| ADB-18 | AI Director + Creative Brief/Brand Compliance/Publishing Agents | P2 | XL |
| ADB-25 | Style Presets gallery | P3 | M |
| ADB-27 | Rendering Farm compute-cost tracking dimension | P3 | M |
| ADB-12 | Cross-window `postMessage` for Desktop iframe embeds | P3 | S |
| ADB-31 | Government / Cloud District / Innovation District | P3 | XL |
| ADB-32 | Departments / Enterprises / Portals structural concepts | P3 | XL |
| ADB-33 | 3D City mode (camera, lighting, fog, materials, walking) | P3 | XL |
| ADB-34 | Multiplayer / presence / cursor-sharing / meetings | P3 | XL |
| ADB-36 | Partner and Investor real journeys | P3 | XL |
| ADB-37 | First-run/onboarding journey design | P3 | M |
| ADB-19 | Voice-driven agent interaction foundation | P3 | XL |
| ADB-40 | i18n/localization strategy document | P3 | M |
| ADB-41 | Deployment/runtime operations runbook | P3 | M |
| ADB-44 | Consolidated OpenAPI index | P3 | M |

---

## A. Architectural decisions (write down before building on top of them)

### ADB-01 — ADR: TS kernel ecosystem's relationship to the Python backend

- **Problem:** `src/kernel` + 6 TypeScript packages are real, non-trivial code with zero runtime
  connection to the Python backend or `src/web` — confirmed by grep, not assumption.
- **Impact:** every future sprint touching either side has to independently rediscover this is true,
  since no document declares it as an intentional decision versus an abandoned experiment.
- **Proposed solution:** write an ADR stating whether this ecosystem is (a) a parallel product with its
  own roadmap, (b) slated for eventual integration, or (c) legacy to be retired — any of the three is
  fine; the absence of a stated answer is the actual problem.
- **Affected modules:** `src/kernel`, `src/orchestrator`, `src/providers`, `src/chat_bridge`,
  `src/voice`, `src/mcp`, `src/execution`, `platform_console` (its one real consumer).
- **Implementation priority:** P0 (decision only — costs nothing to resolve, blocks nothing to leave
  open, but is the platform's single most consequential undocumented fact).
- **Estimated complexity:** M (decision + write-up; no code).
- **Dependencies:** none. Cross-reference: `TECH_DEBT.md` TD-33, `ARCHITECTURE_MAP.md` §15.

### ADB-02 — ADR: Unify or formally separate the three "memory" stacks

- **Problem:** `platform_memory`, `platform_ai/memory`, and `platform_ai_os`'s `/memory-layers`
  (short/session/workspace/organization/knowledge/semantic) are three candidate AI-memory
  implementations with no documented relationship.
- **Impact:** any future feature needing durable AI context (the Creative Knowledge Base, ADB-26; the
  Enterprise lifecycle's organizational memory, `ENTERPRISE_AI_OS.md` §5) risks building on the wrong
  one, or building a fourth.
- **Proposed solution:** an ADR declaring which stack is canonical for which use case (e.g.,
  `/memory-layers` for anything organization-durable and agent-facing; `platform_memory` for
  general document/knowledge search), and whether the other(s) are deprecated, merged, or intentionally
  scoped differently.
- **Affected modules:** `platform_memory/`, `platform_ai/memory/`, `platform_ai_os/`.
- **Implementation priority:** P1.
- **Estimated complexity:** M (requires reading all three stacks closely enough to recommend a real
  merge/separation plan, not just naming the conflict).
- **Dependencies:** none directly; blocks ADB-26.

### ADB-03 — ADR: City navigation hierarchy — resolve the Architecture/Bible disagreement

- **Problem:** `ENTERPRISE_CITY_ARCHITECTURE.md` §0 asserts "login lands in City, City is the primary
  navigation paradigm" as a settled decision. `ENTERPRISE_CITY_BIBLE.md`'s later reality-update section
  corrects this against the real, separately-built Desktop shell, concluding City is the OS's headline
  *app within* Desktop, not the outermost shell. The two documents currently disagree with each other.
- **Impact:** a future contributor reading only one of the two documents gets a different mental model
  of where a user lands after login — a real product-behavior ambiguity, not just a documentation
  nicety.
- **Proposed solution:** a short ADR picking one framing, then a follow-up edit to whichever document is
  wrong (most likely `ENTERPRISE_CITY_ARCHITECTURE.md` §0, since the Bible's correction is grounded in
  real shipped code) — this backlog does not perform that edit itself, per this task's constraint not to
  change existing architecture documents.
- **Affected modules:** `ENTERPRISE_CITY_ARCHITECTURE.md`, `ENTERPRISE_CITY_BIBLE.md`, `DESKTOP.md`,
  `03_ENTERPRISE_OS.md`.
- **Implementation priority:** P0 (cheap to resolve, actively confusing while open).
- **Estimated complexity:** S (decision + a follow-up documentation edit, not code).
- **Dependencies:** none. Feeds ADB-28, ADB-29 (both assume a resolved navigation hierarchy).

### ADB-04 — ADR: Job-execution backend division of labor

- **Problem:** `platform_jobs.JobEngine` (general async jobs) and the Multi-Agent OS's Task Orchestrator
  (agent-specific DAGs, `/tasks`) are both real, with no documented rule for which job types use which.
- **Impact:** a future sprint wiring the frontend `jobManager` (ADB-08) has no guidance on which backend
  to call for a given job kind, risking an arbitrary or inconsistent choice.
- **Proposed solution:** an ADR stating the rule (e.g., "general business/creative jobs → `platform_
  jobs`; multi-step agent collaboration/planning → Task Orchestrator") and whether one should eventually
  delegate to the other.
- **Affected modules:** `platform_jobs/`, `platform_ai_os/` (Task Orchestrator), `enterprise-runtime/
  jobManager.ts`.
- **Implementation priority:** P1.
- **Estimated complexity:** S (decision only).
- **Dependencies:** blocks ADB-08, ADB-17.

### ADB-05 — ADR: Disambiguate the "Production" district

- **Problem:** Enterprise City's Production district serves both operational/manufacturing production
  (Mission Control, drone/port verticals) and the unrelated AI Production Center, under one name.
- **Impact:** the Production Manager and Designer personas (`USER_JOURNEYS.md` §6, §7) land in
  genuinely different places despite the shared district label — a real user-facing ambiguity once more
  than one persona relies on this district.
- **Proposed solution:** an ADR deciding whether to split into two districts (e.g., "Operations" and
  "Production Studio") or keep one district with clearly sub-labeled zones — either is acceptable, the
  current silent overlap is not.
- **Affected modules:** `CITY_DISTRICTS.md`, `ENTERPRISE_CITY_BIBLE.md` §2, `AI_PRODUCTION_CENTER_
  BIBLE.md`.
- **Implementation priority:** P1.
- **Estimated complexity:** S (decision only; district split itself would be M if pursued).
- **Dependencies:** none.

### ADB-06 — ADR: Resolve the shared `/api/ai-os/v1` prefix collision

- **Problem:** `platform_ai_os` (Sprint 27.1 Multi-Agent OS), `applications/ai_os` (Platform AI OS
  kernel), and the legacy Autonomous AIOS (Sprint 20.4) all sit at or near one API prefix
  (`TECH_DEBT.md` TD-07).
- **Impact:** growing confusion as more real capability (this session found the Multi-Agent OS to be
  substantially more capable than previously documented) accumulates behind an ambiguous prefix.
- **Proposed solution:** an ADR assigning each system its own unambiguous prefix or explicitly
  documenting the sub-path convention that already avoids collision today (`/maos/*` vs. the kernel's
  own paths), then updating `API_MAP.md` to reflect the decision.
- **Affected modules:** `platform_ai_os/`, `applications/ai_os/`, `API_MAP.md`.
- **Implementation priority:** P1.
- **Estimated complexity:** S (decision only).
- **Dependencies:** none. Cross-reference: `TECH_DEBT.md` TD-07.

---

## B. Runtime integration

### ADB-07 — Wire frontend Runtime Engine to `platform_ai_os` Executive Dashboard

- **Problem:** the real frontend Runtime Engine (Sprint 28.1) simulates all agent/job/health metrics
  client-side; the real backend Executive Dashboard (`GET /maos/dashboard`) already exists and is
  unused by any frontend.
- **Impact:** this is the single highest-leverage integration gap in the platform — real backend
  capability sitting idle behind a well-built but disconnected frontend.
- **Proposed solution:** replace `runtimeEngine`'s simulated `readMetrics()`/`aiAgentRuntime.tick()`
  with real polling/fetch against `/maos/dashboard` and `/maos/health`, keeping the existing snapshot
  shape (`RuntimeSnapshot`) so downstream consumers (Dashboard widgets, Desktop menubar) need no
  changes.
- **Affected modules:** `src/web/src/enterprise-runtime/` (`runtimeEngine.ts`, `healthService.ts`,
  `aiAgentRuntime.ts`, `jobManager.ts`), `platform_ai_os/`.
- **Implementation priority:** P1.
- **Estimated complexity:** L (real network integration + auth handling + graceful degradation when
  the backend is unreachable).
- **Dependencies:** ADB-06 (prefix clarity helps, not strictly required).

### ADB-08 — Wire frontend Runtime Engine to `platform_jobs`

- **Problem:** `jobManager`'s job list is seeded/synthetic except for its real bridge from Production
  Center automation jobs (which are themselves simulated, ADB-20/ADB-22).
- **Impact:** "Background Jobs"/"Event Queue" widgets on the real Live Dashboard (`DASHBOARD.md`) show
  numbers with no real backend job behind them.
- **Proposed solution:** call the real `jobs_router.py` REST surface (status/history/statistics) and
  merge real job records into `jobManager`'s state alongside whatever remains client-only.
- **Affected modules:** `enterprise-runtime/jobManager.ts`, `platform_jobs/jobs_router.py`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-04 (division-of-labor decision should land first).

### ADB-09 — Wire frontend Runtime Engine to `platform_observability`

- **Problem:** CPU/memory/GPU metrics in the Runtime Engine are a local random walk, explicitly
  commented as such in the source ("browser has no process CPU API").
- **Impact:** the Developer Dashboard profile (`DASHBOARD.md`) and any future ops-facing surface show
  plausible-looking but entirely fictional system metrics.
- **Proposed solution:** call `platform_observability`'s real metrics endpoints
  (`/management/v1/observability/metrics`, per `API_MAP.md`) for anything claiming to represent actual
  system load; keep client-only estimates only for values with no real backend equivalent (e.g.,
  browser heap via `performance.memory`, which is already real).
- **Affected modules:** `enterprise-runtime/runtimeEngine.ts`, `platform_observability/`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** none.

### ADB-10 — WebSocket-backed notification push into `notificationStore`

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md`; notifications today
  arrive via poll/seed, not a real push channel.
- **Impact:** notification latency and the "live" feel of the whole OS depend on this; currently the
  platform's own real-time socket wiring (`liveUpdates`) degrades to polling whenever `VITE_SOCKET_URL`
  is unset.
- **Proposed solution:** connect `notificationStore.push` to the existing `liveUpdates` socket bridge's
  `notifications:new` event once a real socket URL is configured in a target environment.
- **Affected modules:** `src/web/src/notifications/notificationStore.ts`,
  `src/web/workspace/realtime/liveUpdates.ts`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** requires a real `VITE_SOCKET_URL` deployment target to exist (environment
  prerequisite, not a code dependency).

### ADB-11 — Single health-poller singleton, fully driven through every consumer

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md`: the ref-counted singleton
  pattern exists in `healthService` but "today shared interval, still N hook instances."
- **Impact:** minor performance/consistency risk — some consumers may still run independent polling
  paths instead of subscribing to the shared instance.
- **Proposed solution:** audit every `useRuntimeHealth`/`useIntegrationRuntimeHealth` call site and
  confirm each goes through `healthService.subscribe`, removing any independent interval.
- **Affected modules:** `enterprise-runtime/healthService.ts`, `useRuntimeHealth.ts`,
  `integration-hub/` consumers.
- **Implementation priority:** P2.
- **Estimated complexity:** S.
- **Dependencies:** none.

### ADB-12 — Cross-window `postMessage` for Desktop iframe embeds

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md`; Desktop windows embed
  content via same-origin iframes (`?embed=1`) with no defined cross-window messaging contract.
- **Impact:** low today (`WINDOW_MANAGER.md`'s own non-goals list already excludes "cross-window shared
  React context inside embeds" as out of scope) — this is a forward-looking gap, not an active bug.
- **Proposed solution:** define a minimal `postMessage` contract (e.g., for a window to request focus
  or report its own title/status to the shell) once a real use case needs it.
- **Affected modules:** `enterprise-desktop/WindowFrame.tsx`.
- **Implementation priority:** P3.
- **Estimated complexity:** S.
- **Dependencies:** none.

### ADB-13 — Backend integration-hub status endpoint

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md`; the Integration Hub
  (`INTEGRATION_HUB.md`) currently orchestrates only frontend stores, with no backend-side status
  surface confirming the hub's own health.
- **Impact:** the "one OS" claim is weaker without a backend acknowledgment that the integration layer
  itself is healthy, not just the individual surfaces it stitches together.
- **Proposed solution:** a lightweight backend endpoint (likely under `platform_management`) reporting
  aggregate health of the surfaces the Integration Hub coordinates.
- **Affected modules:** `platform_management/`, `src/integration-hub/`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-06 (prefix/routing clarity helps).

### ADB-14 — Live building occupancy/presence from real job queues

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md` ("before Enterprise City
  Runtime"); City buildings currently show simulated activity signals, not real job-queue-derived
  occupancy.
- **Impact:** the City's core promise ("a building that looks busy *is* busy," `ENTERPRISE_CITY.md` §2)
  is not yet fully true for job-driven activity specifically.
- **Proposed solution:** once ADB-08 lands, derive a building's "Busy" state from real job counts
  scoped to that building's underlying module.
- **Affected modules:** `src/web/src/enterprise-city/useCityLiveStatus.ts`, `jobManager.ts`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-08.

### ADB-15 — City camera URL sync (`?x=&y=&zoom=`)

- **Problem:** explicitly named as remaining work in `SPRINT_28_0_RESULT.md`; camera viewport persists
  to `localStorage` (`ews_city_viewport_v1`) but not to the URL, so a shared link can't reproduce a
  specific view.
- **Impact:** minor UX gap — can't deep-link to "this exact framing of the City," only to the City in
  general (`?building=` deep links already work for buildings specifically, per `INTEGRATION_HUB.md`).
- **Proposed solution:** sync `CityViewport` to URL search params, read on load, write on pan/zoom
  (debounced).
- **Affected modules:** `src/web/src/enterprise-city/cityEngine.ts`, `EnterpriseCityPage.tsx`.
- **Implementation priority:** P2.
- **Estimated complexity:** S.
- **Dependencies:** none.

---

## C. AI agent integration

### ADB-16 — Wire real Multi-Agent OS Collaboration protocol to a frontend consumer

- **Problem:** `POST /collaborate` (discuss/vote/select_best/critique/merge) is real backend capability
  with zero frontend consumers anywhere in the platform.
- **Impact:** the platform's most capable real multi-agent mechanism is invisible to users and unused
  by any product surface.
- **Proposed solution:** the Production Center's Brand Compliance / Publishing Agent concepts
  (`AI_PRODUCTION_STUDIO.md` §19, still vision) are the best-scoped first consumer — build a thin UI
  surfacing a real `/collaborate` call for one concrete use case (e.g., two creative variants, agent
  `select_best`) before generalizing further.
- **Affected modules:** `platform_ai_os/`, `src/web/src/ai-production-studio/`.
- **Implementation priority:** P2.
- **Estimated complexity:** L.
- **Dependencies:** ADB-07 (establishes the real-backend wiring pattern to reuse).

### ADB-17 — Wire real Task Orchestrator to a frontend consumer

- **Problem:** `POST /tasks` (DAG, retry/rollback/timeout) is real backend capability with zero
  frontend consumers.
- **Impact:** same class of gap as ADB-16 — real capability, no visible product value yet.
- **Proposed solution:** the AI Director concept (`AI_PRODUCTION_STUDIO.md` §20) is the natural
  consumer — a creative-production plan decomposed into a real DAG via `/tasks` rather than
  `platform_planning`'s more generic (and separately real) machinery.
- **Affected modules:** `platform_ai_os/`, `src/web/src/ai-production-studio/`.
- **Implementation priority:** P2.
- **Estimated complexity:** L.
- **Dependencies:** ADB-04, ADB-16 (shares infrastructure).

### ADB-18 — AI Director + Creative Brief/Brand Compliance/Publishing Agents

- **Problem:** the full creative-agent roster (`AI_PRODUCTION_STUDIO.md` §19–§20,
  `AI_AGENTS_BIBLE.md` §2) remains entirely vision even after two further real sprints landed adjacent
  infrastructure.
- **Impact:** the Production Center's real agent-*assignment* UI (`PRODUCTION_CENTER.md`) has no real
  agent *behavior* behind it (`AI_PRODUCTION_CENTER_BIBLE.md` §0/§9 — the platform's most-repeated
  finding across this whole documentation set).
- **Proposed solution:** build in the order `AI_PRODUCTION_CENTER_BIBLE.md` §10 already sequences:
  real Content Factory/Cross-Posting routes (ADB-20/21) → one real provider (ADB-22) → consent gate
  (ADB-23) → Brand Library (ADB-24) → then this full agent roster.
- **Affected modules:** `platform_ai_os/`, `platform_ai/`, `src/web/src/ai-production-studio/`.
- **Implementation priority:** P2 (sequenced last among Production Center work by design).
- **Estimated complexity:** XL.
- **Dependencies:** ADB-20, ADB-21, ADB-22, ADB-23, ADB-24, ADB-16, ADB-17.

### ADB-19 — Voice-driven agent interaction foundation

- **Problem:** no voice input/output exists anywhere in the platform; `docs/VOICE_FIRST_ENTERPRISE.md`
  (commissioned separately) was never written.
- **Impact:** an entire requested interaction modality (Voice navigation/Desktop/AI/commands, Meeting/
  Production/Emergency modes, hands-free operation) has neither implementation nor a design document
  yet.
- **Proposed solution:** write the design document first (ADB-46), then build voice input as an
  alternate trigger into the existing AI-mode NLU parser (`aiCommandCenter`,
  `ENTERPRISE_NAVIGATION.md` §5) — never a second command grammar.
- **Affected modules:** `command-center/`, `08_AI_PERSONALITY.md`'s voice-input design in
  `ENTERPRISE_NAVIGATION.md` §19.
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** ADB-46.

---

## D. Production Center

### ADB-20 — Real Content Factory HTTP route

- **Problem:** `services/pg_content_factory_engine.py` has zero HTTP route — pure Python-internal
  service class.
- **Impact:** the Production Center's Creative/Prompt studios have nothing real to call for even
  text-only generation, the platform's most mature (if narrow) existing generation capability.
- **Proposed solution:** add a real REST route (POST generate, GET version history) following the
  existing `platform_api`/`platform_management` envelope conventions.
- **Affected modules:** `services/pg_content_factory_engine.py`, `api/` or `platform_management/`.
- **Implementation priority:** P1.
- **Estimated complexity:** M.
- **Dependencies:** none — the single lowest-friction real backend win available in this whole backlog.

### ADB-21 — Real Cross-Posting publish trigger + new channels

- **Problem:** `CrossPostingEngineV1` has a complete real scheduling/state-machine/analytics layer with
  a **simulated** publish call (fake URLs/IDs) and GET-only public routes; no YouTube/LinkedIn channel
  type exists.
- **Impact:** every "publishing" concept in the Production Center (§ Publishing Center, Reels/Ads
  studios) has nothing real to eventually schedule against.
- **Proposed solution:** replace `_publish_job`'s simulated call with real per-platform API clients
  (Telegram/Instagram/Facebook first, reusing existing channel enums), add YouTube/LinkedIn as new
  `PostingChannelType` values with their own OAuth flow.
- **Affected modules:** `services/pg_cross_posting_engine.py`, `services/pg_channel_integration_
  engine.py`, `api/v1/public_router.py`.
- **Implementation priority:** P1.
- **Estimated complexity:** L (real third-party API integration, credential lifecycle management).
- **Dependencies:** ADB-20 (shares the "give Production Center something real to call" motivation).

### ADB-22 — One real generation provider (single modality)

- **Problem:** `platform_ai`'s provider registry is entirely text/LLM (6 mock providers); no image/
  video/voice/avatar provider is registered anywhere.
- **Impact:** all 17 Production Center studios are real UI shells with no generation capability behind
  any of them.
- **Proposed solution:** extend `platform_ai`'s `TaskType`/`ProviderRegistry` with one new modality
  (image generation is the lowest-risk starting point, per `AI_PRODUCTION_STUDIO.md` §1/§3), wire it
  through `platform_tools.AgentToolBridge` for governed execution/audit, and prove the whole pipeline
  end-to-end on one studio before expanding.
- **Affected modules:** `platform_ai/provider_registry.py`, `platform_ai/provider_manager.py`,
  `platform_tools/`, `src/web/src/ai-production-studio/`.
- **Implementation priority:** P2.
- **Estimated complexity:** L.
- **Dependencies:** ADB-23 must land first if the chosen modality is avatar/voice (it is not, for the
  first provider — image carries no consent requirement); ADB-20/ADB-21 establish the surrounding
  pipeline this provider plugs into.

### ADB-23 — Consent-record infrastructure before any avatar/voice provider

- **Problem:** no consent-record data model or validation gate exists for avatar/voice-likeness
  generation (`AI_PRODUCTION_STUDIO.md` §6–§7); the real Production Center UI shell already exists as a
  plausible place a future sprint could wire in avatar/voice generation before this gate is built.
- **Impact:** **the single highest-risk sequencing mistake available in this entire backlog** — shipping
  avatar/voice generation without this gate first is a real legal/ethical exposure, not just a design
  gap.
- **Proposed solution:** build the consent-record model (who consented, scope, expiry) and a hard
  validation gate that blocks avatar/voice-clone generation without a valid reference — before, never
  after, any provider work in that modality.
- **Affected modules:** new data model (likely under `platform_ai_marketing_os` or a new
  `platform_production_studio` package once created), `src/web/src/ai-production-studio/`.
- **Implementation priority:** **P0** (must precede any avatar/voice provider work specifically, even
  though it is not itself blocking unrelated work).
- **Estimated complexity:** M.
- **Dependencies:** none technically, but gates any future avatar/voice extension of ADB-22.
  Cross-reference: `TECH_DEBT.md` TD-46.

### ADB-24 — Real Brand Library data model

- **Problem:** the Production Center's Brand studio is a real navigation destination with no real
  backing data model (`AI_PRODUCTION_CENTER_BIBLE.md` §9).
- **Impact:** brand-constraint injection (color/tone/forbidden-words) into generation — a core
  governance mechanism `AI_PRODUCTION_STUDIO.md` §14 designs — has nothing real to read from.
- **Proposed solution:** implement the field shape already specified in `docs/AMO_BRAND_CREATIVE_
  CONTENT.md` / `platform_ai_marketing_os`'s `BrandCenter` intent, for real, as one or more brand
  profiles per tenant.
- **Affected modules:** `platform_ai_marketing_os/`, `src/web/src/ai-production-studio/`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** none; blocks a fully-governed ADB-22/ADB-18.

### ADB-25 — Style Presets gallery

- **Problem:** only a 3-theme + custom-brand-override system exists (`07_DESIGN_SYSTEM.md`); no preset
  gallery of generation-style bundles (palette + typography + image mood + video pacing) exists.
- **Impact:** lower priority than ADB-24 — a nice-to-have consistency layer, not a governance
  requirement.
- **Proposed solution:** build a system/organization/favorite three-tier preset gallery
  (`AI_PRODUCTION_STUDIO.md` §18), layered on top of, not replacing, the existing theme engine.
- **Affected modules:** `src/web/design-system/theme/`, `platform_enterprise_design_system/`.
- **Implementation priority:** P3.
- **Estimated complexity:** M.
- **Dependencies:** ADB-24 (presets should be brand-library-aware).

### ADB-26 — Prompt Library / Creative Knowledge Base backed by real `/memory-layers`

- **Problem:** the real Prompt Library (`PROMPT_LIBRARY.md`) is session-scoped only; the vision Creative
  Knowledge Base (`AI_PRODUCTION_STUDIO.md` §16) has no backing store at all. `ENTERPRISE_AI_OS.md` §8
  found a real `/memory-layers` backend (organization/knowledge/semantic layers) both could be built on
  instead of inventing a new store.
- **Impact:** without this, prompt history and creative learnings reset every session — a real,
  durable-context gap named independently in three different documents this session.
- **Proposed solution:** wire the Prompt Library and Creative Knowledge Base as consumers of
  `/memory-layers`'s `organization`/`knowledge` layers rather than building separate storage.
- **Affected modules:** `platform_ai_os/`, `src/web/src/ai-production-studio/` (`productionStore.ts`
  prompts).
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-02 (the memory-stack ADR should land first so this doesn't build on an
  unresolved assumption).

### ADB-27 — Rendering Farm compute-cost tracking dimension

- **Problem:** `platform_ai.cost_tracker` is strictly token/dollar-based; no compute-time/GPU-hour/
  frame-count dimension exists for video/3D rendering cost.
- **Impact:** low until real video/3D generation exists — a prerequisite for accurate cost visibility
  once ADB-22 expands beyond image generation.
- **Proposed solution:** extend `CostRecord` with a `unit_type` dimension (token/image/second-of-video/
  GPU-minute/frame) alongside the existing token-based fields.
- **Affected modules:** `platform_ai/cost_tracker.py`.
- **Implementation priority:** P3.
- **Estimated complexity:** M.
- **Dependencies:** relevant only once ADB-22 extends to video/3D modalities.

---

## E. Enterprise City

### ADB-28 — Enterprise City building-catalog completeness audit

- **Problem:** the real 12-district catalog does not yet map every real platform capability to a
  building (`ENTERPRISE_CITY_ARCHITECTURE.md` §3's completeness bar).
- **Impact:** the City cannot honestly claim to represent "the whole business" while real capabilities
  have no corresponding building.
- **Proposed solution:** audit `MODULES.md`'s full package/application list against `CITY_
  DISTRICTS.md`'s current buildings, adding entries for any real, navigable capability missing one.
- **Affected modules:** `src/web/src/enterprise-city/cityCatalog.ts`, `cityDistricts.ts`.
- **Implementation priority:** P1.
- **Estimated complexity:** M.
- **Dependencies:** ADB-03 (resolve navigation hierarchy first, so this work isn't done twice under two
  different framings).

### ADB-29 — Accessible List View as first-class parallel surface

- **Problem:** no non-spatial, fully accessible equivalent of the City map exists yet
  (`ENTERPRISE_CITY_ARCHITECTURE.md` §20).
- **Impact:** the highest UX risk named anywhere in this documentation set — a spatial-first navigation
  paradigm is a real regression for screen-reader/keyboard-only users without this.
- **Proposed solution:** build a `DataGrid`/`Table`-based List View with full column parity to the map
  (name/district/state/notifications/AI-active/present-users), sharing the exact same click-to-navigate
  interaction as a building tile.
- **Affected modules:** `src/web/src/enterprise-city/`, `src/web/src/ui/DataGrid.tsx`.
- **Implementation priority:** P1.
- **Estimated complexity:** L.
- **Dependencies:** ADB-28 (should reflect the completed catalog, not an in-progress one).

### ADB-30 — Role-aware building visibility (RBAC-scoped City buildings)

- **Problem:** every signed-in user currently sees the same building set regardless of role
  (`ENTERPRISE_CITY.md` §8, designed but not built).
- **Impact:** a City that shows buildings a user has no permission to act on is misleading, and doesn't
  match how the Sidebar/Workspace already scope visibility by permission.
- **Proposed solution:** reuse the real RBAC decision already governing Sidebar/route visibility
  (`platform_identity`) as the single source of truth for building dimming/hiding, via the same
  `dimmed` prop the executive overlays already use.
- **Affected modules:** `src/web/src/enterprise-city/`, `platform_identity/`.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-28.

### ADB-31 — Government / Cloud District / Innovation District

- **Problem:** three of `ENTERPRISE_CITY_BIBLE.md` §2's originally-proposed districts remain entirely
  unbuilt.
- **Impact:** low near-term — these districts are explicitly scoped to scale tiers (Government) or
  meta-concerns (Cloud/Innovation) most current tenants don't need yet.
- **Proposed solution:** defer until a real Government-tier tenant or a real product need for
  infrastructure/roadmap visualization emerges — do not build speculatively ahead of that need.
- **Affected modules:** `src/web/src/enterprise-city/cityDistricts.ts`.
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** `ENTERPRISE_CITY_BIBLE.md` §23's scale-tier gating; also depends on real Government-
  tier tenant demand existing at all.

### ADB-32 — Departments / Enterprises / Portals structural concepts

- **Problem:** the sub-building (Departments), multi-entity (Enterprises), and cross-organization
  (Portals) structural concepts (`ENTERPRISE_CITY_BIBLE.md` §10–§12) remain entirely vision.
- **Impact:** blocks any real holding-company or cross-organization City experience.
- **Proposed solution:** build Departments first (lowest complexity, pure UI detail-panel work over
  existing buildings), then Enterprises once a real multi-tenant-per-holding scenario exists to design
  against, then Portals last (depends on Enterprises).
- **Affected modules:** `src/web/src/enterprise-city/`.
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** ADB-28, real multi-entity tenant demand.

### ADB-33 — 3D City mode (camera, lighting, fog, materials, walking)

- **Problem:** the entire 3D vision (`ENTERPRISE_CITY.md` §7.2, `ENTERPRISE_CITY_BIBLE.md` §5) remains
  unbuilt.
- **Impact:** none near-term — 2D remains the default for most tenants indefinitely by design.
- **Proposed solution:** defer until 2D's building catalog and district count justify it
  (`ENTERPRISE_CITY_BIBLE.md` §10 Version 3), and until `CLAUDE.md`'s platform-module-completion gate
  is satisfied.
- **Affected modules:** `src/web/src/enterprise-city/` (new rendering layer, likely WebGL).
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** ADB-28, `10_ROADMAP.md` Horizon 3 gating.

### ADB-34 — Multiplayer / presence / cursor-sharing / meetings

- **Problem:** zero existing precedent anywhere in the platform (`WORKSPACE_INTERACTIONS.md` §0).
- **Impact:** none near-term; named specifically for Enterprise City as the primary intended use case
  once built.
- **Proposed solution:** build on the existing `socket.io`/`liveUpdates` transport as a new lightweight
  presence event type, rather than a new connection or protocol — sequenced after City/Studio/Workspace
  are mature enough to have something worth collaborating on together.
- **Affected modules:** `src/web/src/integrations/socket.ts`, `src/web/src/enterprise-city/`.
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** ADB-28, ADB-33 (cursor-sharing is most valuable once City is visually richer).

---

## F. UX / personas

### ADB-35 — Marketing / Production Manager / Designer Dashboard profiles

- **Problem:** three of ten commissioned personas (`USER_JOURNEYS.md`) have no real Dashboard profile,
  unlike the six that do (CEO/Manager/Sales/Developer/Finance/Administrator).
- **Impact:** these personas' journeys are grounded in generic navigation only, not a role-tailored
  view — a real, low-effort UX gap.
- **Proposed solution:** add three new profiles to `DASHBOARD.md`'s real profile list, each pulling
  from widgets that already exist (Marketing → CRM/Analytics; Production Manager → Mission Control/
  System Health; Designer → Production Center studios/Media).
- **Affected modules:** `src/live-dashboard/liveDashboardStore.ts`.
- **Implementation priority:** P2.
- **Estimated complexity:** S.
- **Dependencies:** none.

### ADB-36 — Partner and Investor real journeys

- **Problem:** both personas are almost entirely vision (`USER_JOURNEYS.md` §9–§10) — no real login
  path, portal, or reporting surface exists for either.
- **Impact:** low near-term; both depend on capabilities (Portals, ADB-32) that don't exist yet.
- **Proposed solution:** defer Partner until ADB-32's Portals land; scope Investor as a read-only,
  narrower-access variant of the real Owner Portal once an access-scope decision is made (a real design
  question this backlog does not answer for the team).
- **Affected modules:** `src/web/src/pages/` (portal pages), `platform_identity/`.
- **Implementation priority:** P3.
- **Estimated complexity:** XL.
- **Dependencies:** ADB-32 (Partner specifically).

### ADB-37 — First-run/onboarding journey design

- **Problem:** no document walks through a brand-new tenant's first login with zero configured
  buildings — `ENTERPRISE_CITY_BIBLE.md` §8's "district-first onboarding" is designed but not detailed
  as a full journey.
- **Impact:** moderate — first impressions matter disproportionately, and this is currently unspecified.
- **Proposed solution:** write a dedicated onboarding-journey design (could extend `USER_JOURNEYS.md` or
  stand alone) covering empty-state City, empty-state Dashboard, and the first Advisor interaction.
- **Affected modules:** documentation only, informing `src/web/src/onboarding/`.
- **Implementation priority:** P3.
- **Estimated complexity:** M.
- **Dependencies:** ADB-28 (a completeness-audited catalog makes onboarding design more concrete).

---

## G. Documentation & governance

### ADB-38 — Canonical Glossary

- **Problem:** "Portal," "Enterprise AI OS," and "Production" each now mean two-to-four different
  things across this documentation set, with no single place resolving any of them.
- **Impact:** every naming collision found in `PRODUCT_ARCHITECTURE_REVIEW.md` traces back to this one
  root cause — the highest-leverage documentation fix available.
- **Proposed solution:** `docs/GLOSSARY.md` defining every overloaded term once, linked from every
  document that currently re-explains or silently diverges on one.
- **Affected modules:** documentation only.
- **Implementation priority:** P1.
- **Estimated complexity:** M.
- **Dependencies:** none — should be done early since it clarifies the terms used throughout the rest
  of this backlog.

### ADB-39 — Formal ADR log

- **Problem:** `CLAUDE.md` requires architectural decisions to be documented, but the only prescribed
  location is a sprint's own `RESULT.md` — no searchable decision history exists.
- **Impact:** ADB-01 through ADB-06 above have nowhere durable to live once decided, other than this
  backlog itself (which tracks *recommendations*, not *resolved decisions*).
- **Proposed solution:** start `docs/decisions/` (or a single `ARCHITECTURE_DECISIONS.md` log,
  distinct from this backlog), and record ADB-01 as its first real entry once resolved.
- **Affected modules:** documentation only.
- **Implementation priority:** P1.
- **Estimated complexity:** S.
- **Dependencies:** none.

### ADB-40 — i18n/localization strategy document

- **Problem:** language policy is referenced piecemeal (City RU/UA, Dashboard/Concierge English) with
  no central i18n architecture document.
- **Impact:** low near-term; matters before any further locale-specific work expands.
- **Proposed solution:** write the strategy document explaining why current surfaces diverge and how a
  new locale would be added.
- **Affected modules:** documentation only.
- **Implementation priority:** P3.
- **Estimated complexity:** M.
- **Dependencies:** none.

### ADB-41 — Deployment/runtime operations runbook

- **Problem:** the dual bot+API runtime has no unified deploy story (`docker-compose.yml` defines only
  `postgres`+`redis`).
- **Impact:** blocks any serious production rollout beyond current dev/pilot posture.
- **Proposed solution:** write the runbook; likely requires an actual `docker-compose` app-service
  addition as a follow-up (out of scope for this documentation-only backlog).
- **Affected modules:** documentation + `docker-compose.yml` (future, not this pass).
- **Implementation priority:** P3.
- **Estimated complexity:** M (doc); the underlying compose work would be separate and larger.
- **Dependencies:** none.

### ADB-42 — Accessibility conformance audit

- **Problem:** WCAG AA is stated as the platform standard but never verified.
- **Impact:** the platform's own accessibility bar is a claim, not a fact, most acutely relevant to
  ADB-29's List View.
- **Proposed solution:** commission a real audit against a representative surface set (Dashboard,
  Desktop, City, Production Center) and publish the report.
- **Affected modules:** `src/web/` broadly.
- **Implementation priority:** P2.
- **Estimated complexity:** L.
- **Dependencies:** ADB-29 (audit should include the List View once it exists).

### ADB-43 — Data-privacy/consent-governance document

- **Problem:** `AI_PRODUCTION_STUDIO.md` §6–§7's hard consent-record requirement has no home document
  describing data retention, consent lifecycle, or regulatory posture.
- **Impact:** directly gates ADB-23's implementation quality — a data model without a governance
  document behind it is incomplete.
- **Proposed solution:** write the document alongside, not after, ADB-23.
- **Affected modules:** documentation only.
- **Implementation priority:** P2.
- **Estimated complexity:** M.
- **Dependencies:** ADB-23 (should be written together).

### ADB-44 — Consolidated OpenAPI index

- **Problem:** uneven OpenAPI coverage across Platform Builder/verticals; no generated, browsable API
  reference exists.
- **Impact:** low near-term for internal work; matters once external/partner integration (ADB-36's
  Partner journey) becomes real.
- **Proposed solution:** generate and publish a consolidated index once the Publishing Center (ADB-21)
  and other Horizon-2 API surfaces land.
- **Affected modules:** `API_MAP.md`, backend route files broadly.
- **Implementation priority:** P3.
- **Estimated complexity:** M.
- **Dependencies:** ADB-20, ADB-21 (more real routes worth indexing by then).

### ADB-45 — UI/UX test-and-review checklist

- **Problem:** `UX_GUIDELINES.md` exists but nothing formally ties "is this accessible, calm, and
  on-brand" to a pre-ship review process.
- **Impact:** moderate — the guidelines exist but aren't enforced by any named process.
- **Proposed solution:** extend `CLAUDE.md`'s existing build/lint/test sprint-closeout requirement with
  a UX checklist pass, reusing `UX_GUIDELINES.md`'s existing checklist items directly rather than
  writing a new one.
- **Affected modules:** documentation only (process, not code).
- **Implementation priority:** P2.
- **Estimated complexity:** S.
- **Dependencies:** none — `UX_GUIDELINES.md` already provides the content.

### ADB-46 — Write `docs/VOICE_FIRST_ENTERPRISE.md`

- **Problem:** commissioned separately, interrupted before being written; Voice navigation/Desktop/AI/
  commands, Meeting/Production/Emergency modes, and hands-free operation remain unspecified.
- **Impact:** blocks ADB-19 (no design exists to build against).
- **Proposed solution:** write the document once ADB-03 (City hierarchy) is resolved, so voice
  navigation design doesn't need to be revisited when that ambiguity is settled.
- **Affected modules:** documentation only.
- **Implementation priority:** P2.
- **Estimated complexity:** M (documentation effort).
- **Dependencies:** ADB-03 (recommended precondition, not a hard blocker).

### ADB-47 — Write `docs/FUTURE_RUNTIME.md`

- **Problem:** commissioned separately, interrupted before being written; 3D Enterprise City, Digital
  Twin, AI Employees, Marketplace evolution, Production Farm, AI Company Builder, Cross-company
  collaboration, and Enterprise Cloud remain unconsolidated as a single Horizon 2/3 document (though
  each individually has partial coverage scattered across `ENTERPRISE_CITY_BIBLE.md`,
  `AI_PRODUCTION_STUDIO.md`, `10_ROADMAP.md`).
- **Impact:** the long-range vision remains fragmented across multiple documents rather than having one
  canonical home.
- **Proposed solution:** write the document once ADB-01 through ADB-06 (the open ADRs) are resolved,
  since several of Horizon 2/3's topics (Cloud District, AI Company Builder) depend directly on how
  those decisions land.
- **Affected modules:** documentation only.
- **Implementation priority:** P2.
- **Estimated complexity:** M (documentation effort).
- **Dependencies:** ADB-01, ADB-02, ADB-05 (recommended preconditions).

### ADB-48 — Promote sprint-self-admitted remaining-work items into `TECH_DEBT.md`

- **Problem:** `SPRINT_28_0_RESULT.md`'s own six-item "Remaining work" list (ADB-10 through ADB-15's
  source items) currently lives only in a Tier 4 historical sprint record, not the living debt
  registry.
- **Impact:** real, sprint-acknowledged debt is invisible to anyone who only checks `TECH_DEBT.md`, per
  `00_MASTER_PRODUCT_BIBLE.md`'s own tier rules.
- **Proposed solution:** **not performed by this backlog itself** (this task explicitly excludes
  modifying `TECH_DEBT.md` for now) — flagged here as the first item to action once that constraint
  lifts; each of ADB-10 through ADB-15 above should get a corresponding `TD-##` entry at that time.
- **Affected modules:** `TECH_DEBT.md` (future edit, not this pass).
- **Implementation priority:** P0 (cheapest, highest-integrity fix available — the analysis is already
  done).
- **Estimated complexity:** S.
- **Dependencies:** none; explicitly deferred per this task's own instruction, not blocked technically.

---

## Related documents

`TECH_DEBT.md` (deliberately untouched by this pass; cross-referenced throughout, not duplicated),
`PRODUCT_ARCHITECTURE_REVIEW.md` (the source this backlog reorganizes into sprint-ready items),
`00_MASTER_PRODUCT_BIBLE.md` §4, `ENTERPRISE_AI_OS.md` §14, `AI_PRODUCTION_CENTER_BIBLE.md` §10,
`ENTERPRISE_CITY_ARCHITECTURE.md` §24, `10_ROADMAP.md` (the original scattered locations these
recommendations were collected from), `USER_JOURNEYS.md`, `ENTERPRISE_CITY_BIBLE.md`,
`WORKSPACE_INTERACTIONS.md` (persona/City/collaboration detail behind Section E–F items).
