# The Enterprise AI Operating System — Bible

**Status:** the canonical, highest-level design authority for how ADOS behaves *as an operating
system* — as distinct from any single feature within it. Documentation only — no source code should
be modified as a result of reading this document. This extends the pre-existing implementation
reference below (preserved verbatim, Sprint 27.1) into a full Bible covering philosophy, lifecycles,
and every OS-level concept this platform is built around. Sits alongside `ENTERPRISE_CITY_BIBLE.md`
and `AI_PRODUCTION_CENTER_BIBLE.md` in the Bible tier, and is the canonical home for
`03_ENTERPRISE_OS.md`'s topic going forward.

---

## Implementation reference — Multi-Agent OS backend (Sprint 27.1, preserved, real)

Sprint **27.1** / Platform **v9.2.0** — Enterprise Multi-Agent Operating System.

AI Executive Layer that directs, registers, orchestrates and collaborates across the platform agent
fleet.

### Architecture

```
platform_ai_os/                              # Multi-Agent OS library
applications/enterprise_hub/enterprise_ai_os/ # Hub suite + API
applications/enterprise_hub/ai_os/enterprise_multi_agent.py  # bridge
src/web/ai-os/                               # Executive Dashboard UI
```

Legacy Autonomous AIOS (Sprint 20.4) remains at `/api/enterprise-aios/v1`.
Platform AI OS kernel (`applications/ai_os`) remains at `/api/ai-os/v1` (health/kernel/processes/…).
Sprint 27.1 Multi-Agent routes share `/api/ai-os/v1` without colliding (this shared-prefix fact is
independently tracked as `TECH_DEBT.md` TD-07 — worth resolving before this Bible's philosophy sections
below are taken as evidence the platform never has naming collisions).

### API

Base: **`/api/ai-os/v1`**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/maos/health` | MAOS readiness |
| POST | `/maos/bootstrap` | Bootstrap suite |
| GET | `/maos/inventory` | Architecture inventory |
| GET | `/maos/dashboard` | Executive dashboard |
| GET | `/exec-dashboard` | Executive dashboard alias |
| POST | `/executive` | AI Director: accept & execute goals |
| GET | `/agents` | Agent Registry 2.0 |
| GET/POST | `/agent-bus` | Communication bus |
| POST | `/tasks` | Task orchestrator (DAG) |
| GET/POST | `/memory-layers` | Layered memory manager |
| POST | `/collaborate` | Multi-agent collaboration |

### Capabilities

1. **Executive AI** — decompose, assign, control, merge
2. **Agent Registry 2.0** — name, role, status, load, capabilities, cost, speed, memory, models
3. **Communication Bus** — request/response/event/broadcast/stream + priority queue
4. **Task Orchestrator** — parallel/sequential/conditional + retry/rollback/timeout
5. **Memory Manager** — short/session/workspace/organization/knowledge/semantic
6. **Collaboration** — discuss/vote/select_best/critique/merge
7. **Executive Dashboard** — active agents, queues, load, cost, latency, errors, history

### Frontend

Route: `/ai-os`. **Status correction (verified while writing this Bible):** the real frontend page
(`src/web/ai-os/pages/AIOSPage.tsx`, `dashboard/executiveDashboard.ts`) defines the real
`AI_OS_API = "/api/ai-os/v1"` constant but **does not call it** — `buildExecutiveDashboard()` returns a
hardcoded, static agent roster (8 named agents with fixed load/cost/latency numbers) with no `fetch`
against the real backend anywhere in the page. This is the same pattern found everywhere else in this
documentation set (§0 below): **real, substantive backend capability, disconnected frontend
demo data.** This gap — wiring `/ai-os`'s real page to the real `/maos/*` endpoints already
documented above — is this Bible's single highest-leverage near-term recommendation (§14).

---

## 0. What this reference changes about every prior document in this set

This backend (`platform_ai_os`) is **more capable than anything previously assumed** in
`AI_AGENTS_BIBLE.md` or the enterprise-runtime research behind it. Concretely:

- **A real layered Memory Manager exists** — short/session/workspace/organization/knowledge/semantic —
  materially richer than the "text-only, disconnected" characterization this Bible's earlier drafting
  pass gave the memory story (§8 corrects `AI_AGENTS_BIBLE.md` §1 accordingly).
- **A real Task Orchestrator (DAG, retry/rollback/timeout) and a real Collaboration protocol
  (discuss/vote/select_best/critique/merge) exist** — this is a real, working mechanical foundation for
  multi-agent collaboration, not merely `platform_planning`'s domain-agnostic planning machinery
  (`AI_PRODUCTION_STUDIO.md` §20's earlier, narrower framing) — §9 below corrects this.
- **The gap is not "no backend capability," it is "no frontend wiring."** Every section below that
  discusses AI memory, collaboration, or task orchestration should be read against this corrected
  baseline: the hard part (real backend logic) is done; the remaining work is connecting real frontend
  surfaces to it instead of the demo data currently standing in.

---

## 1. AI Operating System philosophy

ADOS is not "a platform with an AI feature." It is designed so that **the operating system itself is
AI-aware at the structural level** — the same way a modern OS is aware of touch or of the network, not
as a bolted-on app but as a dimension every surface can assume is present. Concrete evidence this
philosophy is real, not aspirational: a dedicated Multi-Agent OS package (`platform_ai_os`) exists as
its own capability layer, with its own Executive AI, Agent Registry, Communication Bus, Task
Orchestrator, Memory Manager, and Collaboration protocol — this is not a feature bolted onto CRM or
Finance, it is infrastructure every future feature inherits, exactly the way a conventional OS's
process scheduler is infrastructure every app inherits rather than something each app reimplements.

Three consequences of this philosophy, realized (with varying completeness) by real systems:

1. **One shared context, not one context per app** — the Integration Hub's `integrationContextStore`
   (`INTEGRATION_HUB.md`, Sprint 28.0) at the frontend session level; the Multi-Agent OS's own
   `/memory-layers` at the backend, organization-durable level (§8).
2. **One event/communication language, not one per feature** — `enterpriseEventBus` at the frontend
   (§10); the Multi-Agent OS's real Communication Bus (request/response/event/broadcast/stream +
   priority queue) at the backend.
3. **AI presence is ambient, not summoned** — the AI Command Center panel (`COMMAND_CENTER.md`), the AI
   Dock (`08_AI_PERSONALITY.md`), and the real Agent Registry 2.0 (this document's reference section)
   are three views of the same underlying fact — AI work is always visible somewhere in the shell.

## 2. Human ↔ AI interaction

Inherited from `08_AI_PERSONALITY.md` and `AI_AGENTS_BIBLE.md` §0: one persona (the Executive Advisor),
reachable from the AI Dock, the Command Palette's AI mode, and the AI Command Center panel. The
Multi-Agent OS's `POST /executive` endpoint ("AI Director: accept & execute goals") is the real backend
counterpart of this persona's decision-making — a human states a goal, the Executive AI capability
decomposes/assigns/controls/merges the work across the Agent Registry. **Confidence is one badge, never
a percentage or a raw cost/latency number surfaced as if it were a confidence signal** — the Executive
Dashboard's real cost/latency/load metrics (this document's reference section) describe system state,
never AI confidence, and must never be visually conflated with the Advisor's Observation/Why/Action/
Impact voice.

## 3. Workspace lifecycle

Real, per `WORKSPACE_INTERACTIONS.md` and the Integration Hub's `sessionCoordinator.restoreAll()`
(`INTEGRATION_HUB.md`): tabs open, pin/duplicate/close/reopen, and persist to `ews_workspace_session_v1`
— coordinated with Desktop/Dashboard/Production/City restore in one pass, not four racing ones.

## 4. Desktop lifecycle

Real, per `DESKTOP.md`/`WINDOW_MANAGER.md`: `openApp` → focus/restore/cascade → move/resize/minimize/
maximize/snap → close (reopen stack). Integration-hub-aware as of Sprint 28.0 — Desktop lifecycle
events are real `enterpriseEventBus` events other surfaces can observe.

## 5. Enterprise lifecycle

The organization-level lifecycle, spanning onboarding through `ENTERPRISE_CITY_BIBLE.md` §23's five-tier
scaling model: tenant onboarding → module/vertical enablement → City district growth (real precedent:
5→12 districts, Sprint 32.3.3→27.8) → scale-tier transition (vision) → cross-organization connection via
Portals (vision, `FUTURE_RUNTIME.md`). The Multi-Agent OS's `organization` memory layer (this document's
reference section) is the real backend concept this lifecycle's durable, cross-session organizational
facts should live in once wired to a real frontend consumer (§0, §8).

## 6. Runtime lifecycle

Real, per the frontend Runtime Engine (`src/web/src/enterprise-runtime/`, Sprint 28.1):
`runtimeEngine.start()` boots a ref-counted health service (real soft HTTP probes where a URL is
configured) and a 12-second tick that advances job/agent state and emits a `RuntimeSnapshot` onto
`enterpriseEventBus`. **What this tick currently advances is simulated, client-side state** — CPU/
memory/GPU are a local random walk (the code's own comment: "browser has no process CPU API"), and
agent statuses "soft rotate... for live feel." This frontend runtime lifecycle has **no wiring today**
to the real Multi-Agent OS backend's Executive Dashboard (`GET /maos/dashboard`) or real Agent Registry
— two real systems, one frontend and one backend, both modeling "runtime state," currently disconnected
from each other (§14's top recommendation).

## 7. AI memory model — corrected

**Three things named "memory" exist, and none should be confused with another:**

1. **The real Multi-Agent OS layered Memory Manager** (`GET/POST /memory-layers`) — short, session,
   workspace, organization, knowledge, semantic layers. This is the actual AI memory model this
   platform has built, and it is real backend capability, not vision.
2. **The general backend memory packages** (`platform_memory/`, and the separately-tracked duplicate
   `platform_ai/memory/`, `TECH_DEBT.md` TD-21) — general-purpose context/knowledge storage, related to
   but not the same code path as (1); reconciling whether `platform_ai_os`'s memory layers are built on
   top of `platform_memory` or are a third independent stack is an open question this Bible flags for a
   future ADR (`00_MASTER_PRODUCT_BIBLE.md` §4) rather than assuming an answer.
3. **The frontend Runtime Engine's "Memory" health item** (§6) — a browser-heap diagnostic, unrelated
   to AI memory in any sense. Still, as stated in this document's earlier draft, the item most likely to
   be confused with (1) by a future contributor skimming code — flagged here a second time because it
   matters enough to repeat.

## 8. Long-term context

The real `/memory-layers` organization/knowledge/semantic layers (§7 item 1) are this platform's actual
mechanism for long-term context — **this corrects §8's earlier draft**, which (written before this
Bible's author found the pre-existing implementation reference above) claimed no long-term-context
mechanism existed at all. The corrected, accurate status: **the backend mechanism is real; no frontend
surface reads or writes to it yet.** The Production Center's Prompt Library and the still-vision
Creative Knowledge Base (`AI_PRODUCTION_STUDIO.md` §16) should be built as *consumers* of this real
memory-layers API rather than inventing a separate long-term-context store — this is the single most
important architectural correction this Bible makes to `AI_PRODUCTION_CENTER_BIBLE.md`'s roadmap (§10
there should be updated to reflect that the Creative Knowledge Base has a real backend to build on,
not a gap to fill from scratch).

## 9. Multi-agent collaboration — corrected

**Real backend mechanism:** the Multi-Agent OS's Collaboration capability (`POST /collaborate`) supports
discuss/vote/select_best/critique/merge — a real, named protocol for multiple agents reaching a joint
outcome — plus a real Task Orchestrator (`POST /tasks`) supporting parallel/sequential/conditional
execution with retry/rollback/timeout. **This corrects `AI_AGENTS_BIBLE.md` §1's characterization** of
`platform_collaboration`/`platform_planning` as the only relevant backend precedent — `platform_ai_os`
is a real, more directly applicable foundation for exactly this purpose. **Still disconnected from the
frontend:** the Runtime Engine's `aiAgentRuntime` roster (§6) simulates busy/idle rotation locally and
has no call into `/tasks` or `/collaborate` — the real collaboration protocol exists and is unused by
any frontend surface today.

## 10. Event-driven architecture

Three real event mechanisms, related but distinct — restated precisely because getting this relationship
wrong is an easy mistake for a future contributor to make:

| Mechanism | Layer | Scope |
|---|---|---|
| `PlatformEventBus` (`events/event_bus.py`) | Backend, canonical | Platform business events |
| Multi-Agent OS Communication Bus (`GET/POST /agent-bus`) | Backend, agent-specific | request/response/event/broadcast/stream + priority queue, scoped to agent coordination |
| `enterpriseEventBus` (`INTEGRATION_HUB.md`) | Frontend, OS-wide | `navigate`/`open_module`/`ai_request`/`job_update`/`runtime_update`/`notification`/`context_changed`/`session_restored` |
| `dashboardEventBus` (`DASHBOARD.md`) | Frontend, Dashboard-scoped | Widget refresh only |

None of the two backend buses and two frontend buses are currently bridged end-to-end for AI-agent
events specifically — `enterpriseEventBus`'s `ai_request`/`job_update` events originate from the
frontend Runtime Engine's simulation (§6), not from the real Communication Bus. Bridging this is the
concrete technical work behind §14's top recommendation.

## 11. Permission model

Real backend (`platform_identity`/`platform_management`), header-only pending full live tokens
(`TECH_DEBT.md` TD-08). One permission model, read from everywhere — City building visibility, Command
Palette action availability, and (once wired) Multi-Agent OS task/agent access should all resolve
against this one decision, never independently-maintained lists (`02_PRODUCT_PHILOSOPHY.md`
principle 7).

## 12. Background jobs

Real backend substrate exists at two levels now, not one: the general `platform_jobs.JobEngine`
(`AI_PRODUCTION_STUDIO.md` §0) and the Multi-Agent OS's own Task Orchestrator (§9) for agent-specific
DAG execution. The frontend `jobManager` (`enterprise-runtime/jobManager.ts`) tracks a real, if
currently-simulated, job list and does genuinely sync from the Production Center's automation store —
but nothing bridges it to either real backend job substrate yet. **This platform has two real
job-execution backends** (general `platform_jobs`, agent-specific Task Orchestrator) that should stay
distinct by purpose (general async work vs. agent task DAGs) — a future integration should wire the
frontend to whichever is the correct source for a given job type, never invent a third.

## 13. Automation philosophy

Unchanged, restated because every new real implementation independently re-derives it: **automation
controls when work happens, never whether a human approves before anything externally visible occurs**
(`AI_PRODUCTION_CENTER_BIBLE.md` §4, `02_PRODUCT_PHILOSOPHY.md` principle 6). This applies to the
Multi-Agent OS's real Task Orchestrator exactly as it applies to Production Center pipelines — a DAG
task with retry/rollback is an execution detail, not a license to skip approval for anything the DAG
ultimately publishes or acts on externally.

## 14. Recommendations (this Bible's concrete near-term contribution)

1. **Wire `/ai-os`'s real frontend page to the real `/maos/*` backend** — the single highest-leverage
   fix identified while writing this document; the backend is real and capable, the frontend page
   already has the right API constant defined and simply never calls it.
2. **Bridge the frontend Runtime Engine (§6) to the real Multi-Agent OS Executive Dashboard and
   Communication Bus** — replacing simulated agent/job state with real backend state is now a wiring
   problem, not a "build the backend" problem.
3. **Resolve whether `platform_ai_os`'s memory layers and `platform_memory`/`platform_ai/memory` are
   one stack or three** (§7) — a real architectural decision this Bible could not resolve by reading
   alone; needs an ADR.
4. **Build the Creative Knowledge Base (`AI_PRODUCTION_STUDIO.md` §16) as a consumer of `/memory-layers`
   `organization`/`knowledge` layers**, not a new store — the corrected §8 finding above.
5. **Resolve the shared `/api/ai-os/v1` prefix collision** between this Multi-Agent OS, the legacy
   Autonomous AIOS, and the Platform AI OS kernel (`TECH_DEBT.md` TD-07) before adding further routes to
   any of the three.

---

## Related documents

`03_ENTERPRISE_OS.md`, `AI_AGENTS_BIBLE.md` (§1, §7, §9 here correct that document's backend-stack
characterization), `AI_PRODUCTION_CENTER_BIBLE.md` (§8, §10 here correct its Creative Knowledge Base
roadmap item), `INTEGRATION_HUB.md`, `DASHBOARD.md`, `COMMAND_CENTER.md`, `DESKTOP.md`,
`WINDOW_MANAGER.md` (the real frontend OS implementation), `ARCHITECTURE_MAP.md` §5, `MODULES.md` §5–§6,
`TECH_DEBT.md` (TD-07, TD-08, TD-21 — all directly relevant here; add a new item for the `/ai-os`
frontend-backend disconnect at next registry update), `USER_JOURNEYS.md`, `VOICE_FIRST_ENTERPRISE.md`,
`FUTURE_RUNTIME.md`.
