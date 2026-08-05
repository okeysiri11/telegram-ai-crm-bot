# Product Architecture Review

**Status:** a point-in-time review of the entire ADOS documentation set produced across this
documentation initiative (`00_MASTER_PRODUCT_BIBLE.md` and its chapters, `ENTERPRISE_CITY_BIBLE.md`,
`AI_PRODUCTION_CENTER_BIBLE.md`, `AI_AGENTS_BIBLE.md`, `ENTERPRISE_AI_OS.md`, `UX_GUIDELINES.md`,
`USER_JOURNEYS.md`, the deep specs, and the real Sprint 27.x/28.x implementation reference docs), cross-
checked against the current repository. Documentation only — no source code was modified to produce
this review, and this review does not rewrite any existing document; it references them by name and
section. Where a finding below duplicates something a prior document already tracks (most notably
`TECH_DEBT.md`), this review says so explicitly rather than re-describing it as new.

**Method:** synthesis of everything written this session, re-verified against the real repository state
where a claim mattered enough to check rather than recall (route existence, event-bus wiring, sprint
result files). Two categories of finding recur constantly below and are worth naming once, up front,
rather than repeating per item: (1) **real, capable backend/frontend infrastructure with no consumer on
the other side** — the single most common gap pattern found in this whole documentation set; (2)
**one concept, several names** — a recurring naming-collision pattern this platform's fast, additive
sprint cadence produces faster than documentation can consolidate it.

**One deliverable gap in this review's own history, named for completeness:** the previous task
requested `docs/VOICE_FIRST_ENTERPRISE.md` and `docs/FUTURE_RUNTIME.md`; both were interrupted before
being written when this review was requested instead. They remain outstanding — see §5 and the
Priority Recommendations.

---

## 1. Missing architectural decisions

1. **The TypeScript kernel ecosystem's relationship to the Python backend** — real, non-trivial code
   (`src/kernel` + 6 packages) with zero runtime connection to the platform it shares a repo with
   (`ARCHITECTURE_MAP.md` §15, `TECH_DEBT.md` TD-33). Still the single most consequential undocumented
   decision in this platform; nothing written since has resolved it.
2. **Whether `platform_ai_os`'s layered Memory Manager (`/memory-layers`) is the same stack as
   `platform_memory`/`platform_ai/memory`, or a third one** — surfaced by `ENTERPRISE_AI_OS.md` §7/§14
   while reconciling the real Multi-Agent OS backend against this session's earlier (narrower)
   characterization of the memory story. Not resolvable by reading alone; needs an ADR.
3. **Whether Enterprise City is "the primary navigation paradigm" (login lands there) or "the OS's
   headline app within Desktop"** — `ENTERPRISE_CITY_ARCHITECTURE.md` §0 asserts the former as a
   decision already made; `ENTERPRISE_CITY_BIBLE.md`'s later reality-update section corrects this
   against the real, separately-built Desktop shell (`DESKTOP.md`) and concludes the latter. **These
   two documents currently disagree with each other and neither has been reconciled against the other
   directly** — this review flags it as a documentation inconsistency (§ "Conflicting module names"
   below) and an open decision (which framing this platform actually commits to) simultaneously.
4. **Which real job-execution backend a given job type should use** — the general `platform_jobs`
   engine vs. the Multi-Agent OS's own Task Orchestrator (`ENTERPRISE_AI_OS.md` §12) — both real, no
   documented division of responsibility.
5. **Whether the Production district (Enterprise City) means operational/manufacturing production or
   the AI Production Center** — both real concepts share the City's "Production" district today
   (`ENTERPRISE_CITY_BIBLE.md` §2's own note; restated independently in `USER_JOURNEYS.md` §6's
   cross-journey findings) — no decision has split them or clarified the overlap is intentional.

## 2. Duplicate concepts

1. **Event buses, now five, not the "6+ backend" count `TECH_DEBT.md` TD-20 originally tracked**:
   `PlatformEventBus` (backend, canonical), the Multi-Agent OS's Communication Bus (backend,
   agent-scoped), `enterpriseEventBus` (frontend, OS-wide, `INTEGRATION_HUB.md`), `dashboardEventBus`
   (frontend, Dashboard-scoped, `DASHBOARD.md`), plus TD-20's original backend list. `ENTERPRISE_AI_
   OS.md` §10 is the first place all of these are named together — TD-20 should be updated to
   reference it rather than re-deriving the list.
2. **Memory, now three candidate stacks**: `platform_memory`, `platform_ai/memory` (TD-21), and the
   newly-surfaced `platform_ai_os` `/memory-layers` (`ENTERPRISE_AI_OS.md` §7). TD-21 predates this
   third discovery and should be updated.
3. **"Dashboard"/"Executive Dashboard," now four distinct real things**: the Live Dashboard
   (`DASHBOARD.md`, Sprint 27.6, route `/dashboard`), the Executive Morning Brief
   (`EP_01_EXECUTIVE_EXPERIENCE.md`), the Command Center's Enterprise Metrics Strip (`COMMAND_
   CENTER.md`), and the Multi-Agent OS's real `GET /maos/dashboard` / `/exec-dashboard` endpoints
   (`ENTERPRISE_AI_OS.md` reference section) — a genuine naming collision not previously tracked
   anywhere in this documentation set.
4. **Job/queue systems, now three**: `platform_jobs` (general backend), the Multi-Agent OS Task
   Orchestrator (agent-DAG backend), and the frontend `jobManager` (simulated, partially bridged) —
   restated from §1 item 4 here specifically as a duplication, not just an undecided division of labor.
5. **"AI OS," now three adjacent backends sharing one API prefix**: `platform_ai_os` (Sprint 27.1
   Multi-Agent OS), `applications/ai_os` (Platform AI OS kernel), and the legacy Autonomous AIOS
   (Sprint 20.4) — all documented in `ENTERPRISE_AI_OS.md`'s preserved reference section, already
   tracked as `TECH_DEBT.md` TD-07, but worth restating here since this review's own §1 item 3 shows
   the confusion compounding (this platform now also has a *Bible* called "Enterprise AI OS" describing
   the whole-platform philosophy, a fourth, different-scope use of the same three words — see next
   section).
6. **"Production," restated as duplication rather than just a missing decision** (§1 item 5) — the
   City's Production district, the AI Production Center, and manufacturing/logistics verticals
   (`drone_platform`, `port_erp`) all use the word with different scope.

## 3. Conflicting module names

1. **"Portal"** — `ENTERPRISE_CITY_BIBLE.md` §12 (inter-organization gateway) vs. the real
   `CustomerPortalPage`/`EmployeePortalPage`/`OwnerPortalPage` (`App.tsx` routes, role-scoped landing
   areas within one org). Already tracked as `00_MASTER_PRODUCT_BIBLE.md` §3 gap #3 — restated here
   only to confirm it remains unresolved, not to re-describe it.
2. **"Enterprise AI OS"** — this review's own §2 item 5 extended: the phrase now names *both* a specific
   real backend package (`platform_ai_os`) *and* the whole-platform philosophy document
   (`docs/ENTERPRISE_AI_OS.md`, this session's Bible). The Bible document itself handles this by
   preserving the backend reference verbatim and building the philosophy content around it rather than
   over it — a reasonable resolution at the document level, but the *name* collision at the product
   level (what does a stakeholder mean when they say "the AI OS") is not resolved and should go in the
   glossary this documentation set has recommended twice now (`00_MASTER_PRODUCT_BIBLE.md` §4 item 1).
3. **Enterprise City's district taxonomy vs. the Bible's original vision taxonomy** — reconciled inside
   `ENTERPRISE_CITY_BIBLE.md` §2 already (12 real vs. 14 vision), not a live conflict, but flagged here
   as a fragile reconciliation: if the real district catalog changes again before the Bible is
   re-verified, this table will silently go stale, and there is no automated check that would catch it
   (the same "documentation is now tracking a moving target" risk `00_MASTER_PRODUCT_BIBLE.md` §3 item
   10 already names generally — this is a concrete instance of it).
4. **Route aliases** — `/enterprise-city` / `/city` / `/city-hub`, and `/production-studio` /
   `/production` — already tracked as `TECH_DEBT.md` TD-43, restated here as a "conflicting name" issue
   specifically because `ENTERPRISE_CITY_CORE.md` itself calls `/city-hub` "legacy... optional," which
   is the implementing sprint's own admission this wasn't a fully settled decision.

## 4. Missing APIs

1. Real HTTP route for Content Factory generation — still absent (`AI_PRODUCTION_STUDIO.md` §0,
   unchanged across every subsequent document).
2. Real POST publish trigger behind Cross-Posting — still GET-only.
3. Any real image/video/voice/avatar generation provider in `platform_ai`'s registry.
4. A real bridge from the frontend Runtime Engine to `platform_ai_os`'s real `/maos/*` endpoints
   (`ENTERPRISE_AI_OS.md` §14 item 1 — the single highest-leverage recommendation in that document,
   restated here as a missing API integration specifically).
5. **Backend integration-hub status endpoint** — not a documentation inference, this is the
   implementing sprint's *own* stated remaining work (`SPRINT_28_0_RESULT.md`: *"Backend integration-hub
   status endpoint"* is listed under "Remaining work before Enterprise City Runtime"). Worth flagging
   because it is real, sprint-acknowledged debt that has not yet been promoted into `TECH_DEBT.md`'s
   living registry — it currently lives only in a Tier 4 historical sprint record, which
   `00_MASTER_PRODUCT_BIBLE.md`'s own tier rules say should not be where a future contributor has to go
   looking for open work.
6. Real consent-record API for avatar/voice likeness (`AI_PRODUCTION_CENTER_BIBLE.md` §9, `TECH_
   DEBT.md` TD-46).
7. Consolidated OpenAPI index (`TECH_DEBT.md` TD-13).

## 5. Missing user journeys

1. **`docs/VOICE_FIRST_ENTERPRISE.md` was never written** — Meeting mode, Production mode, Emergency
   mode, hands-free operation all remain unspecified. This is the clearest concrete gap this review can
   name, since it was explicitly commissioned and interrupted.
2. **Partner and Investor journeys are almost entirely vision** (`USER_JOURNEYS.md` §9–§10) — no real
   login path, portal, or reporting surface exists for either persona today.
3. **Marketing Manager, Production Manager, and Designer have no real Dashboard profile**
   (`USER_JOURNEYS.md` cross-journey finding #1) — three of ten commissioned personas are grounded in
   generic navigation only, not a role-tailored view.
4. **No dedicated first-run/onboarding journey** distinct from a returning user's journey — City's
   "district-first onboarding" is designed (`ENTERPRISE_CITY_BIBLE.md` §8) but no document walks through
   what a brand-new tenant with zero configured buildings actually sees on their very first login.

## 6. Missing AI Agent interactions

1. The real Multi-Agent OS Collaboration protocol (`discuss/vote/select_best/critique/merge`) and Task
   Orchestrator (DAG/retry/rollback) have **zero frontend consumers** — the most capable real agent
   infrastructure in the platform is entirely unused by any UI (`ENTERPRISE_AI_OS.md` §9).
2. The AI Director, Creative Brief Agent, Brand Compliance Agent, and Publishing Agent
   (`AI_PRODUCTION_STUDIO.md` §19–§20, `AI_AGENTS_BIBLE.md` §2) remain fully vision even after two
   further real sprints (27.9, 28.1) landed adjacent infrastructure.
3. Enterprise City's AI-agent visualization is limited to a single-building "AI working" flag
   (`ENTERPRISE_CITY_BIBLE.md` §7) — there is no real visualization of an agent hand-off *between*
   buildings, even though the real Task Orchestrator (item 1) would be a genuine data source for exactly
   that once connected.
4. No voice-driven agent interaction exists or is specified (compounds §5 item 1's gap).

## 7. Missing Production Center specifications

Unchanged from `AI_PRODUCTION_CENTER_BIBLE.md` §9, restated as still-current rather than re-derived:
no real generation provider behind any of the 17 studios; no real Brand Library data model; no Style
Presets gallery; no consent-record infrastructure (`TECH_DEBT.md` TD-46, still P0); no compute-time cost
dimension for the (still-vision) Rendering Farm; no real semantic search for the Prompt Library — **this
last item is now correctable more cheaply than `PROMPT_LIBRARY.md`'s own "Future" section assumed**,
since `ENTERPRISE_AI_OS.md` §8 identifies a real `/memory-layers` backend the Prompt Library and the
still-vision Creative Knowledge Base could both be built on rather than inventing a new store.

## 8. Missing Enterprise City interactions

1. Government, Cloud District, and Innovation District — 0 of 3 vision districts built.
2. Departments, Enterprises, and Portals structural concepts — fully vision.
3. 3D mode in its entirety (camera, lighting, fog, materials, walking) — vision.
4. Multiplayer/presence/cursor-sharing/meetings — confirmed zero existing precedent
   (`WORKSPACE_INTERACTIONS.md` §0), restated here as a City-specific gap since `ENTERPRISE_CITY_
   BIBLE.md` §8/§16 name City as the primary intended use case for exactly this capability.
5. **Live building occupancy/presence from real job queues, and camera-state URL sync
   (`?x=&y=&zoom=`)** — both explicitly named as remaining work in `SPRINT_28_0_RESULT.md`'s own
   "Remaining work before Enterprise City Runtime" list. Same status as §4 item 5 above: real,
   sprint-acknowledged, not yet in the living debt registry.
6. Role-aware building visibility (RBAC-scoped City buildings) — designed (`ENTERPRISE_CITY.md` §8,
   `ENTERPRISE_CITY_BIBLE.md` §2) but not built.

## 9. Missing Enterprise Runtime integration

This is the single densest gap category in the entire review — the frontend Runtime Engine (Sprint
28.1) is real, well-architected code that is connected to almost nothing real:

1. Not connected to `platform_jobs` (real backend job engine).
2. Not connected to `platform_ai_os`'s real Executive Dashboard, Agent Registry, Communication Bus, or
   Task Orchestrator.
3. Not connected to `platform_observability` for real CPU/memory/health telemetry — every runtime
   metric today is a local random walk (`ENTERPRISE_AI_OS.md` §6, §0).
4. **WebSocket-backed notification push into `notificationStore`** — explicitly named remaining work in
   `SPRINT_28_0_RESULT.md`.
5. **Single health-poller singleton not fully driven through every consumer** ("today shared interval,
   still N hook instances") — explicitly named remaining work in `SPRINT_28_0_RESULT.md`.
6. **Cross-window `postMessage` for Desktop iframe embeds** — explicitly named remaining work in
   `SPRINT_28_0_RESULT.md`.

Items 4–6 above are, again, real gaps the implementing sprint already wrote down itself — this review's
contribution is noticing that none of the three have been promoted from a Tier 4 sprint record into the
living `TECH_DEBT.md` registry, where `00_MASTER_PRODUCT_BIBLE.md`'s own tier rules say ongoing work
should be tracked.

## 10. Technical debt that should be resolved before new implementation

Prioritized, not re-describing detail already in `TECH_DEBT.md`:

1. **TD-46 (P0)** — the consent-record gate must exist before any real avatar/voice provider work
   begins; this remains the single highest-priority item in the entire registry, and nothing in this
   session's later work has changed that.
2. **TD-17 (P0, CI-blocking)** — `platform_security` bypassing `ConfigurationCenter`; still open,
   still the lowest-effort fix available anywhere in the registry.
3. **TD-40** — orphaned Command Palette; confirmed still open by direct grep during this session (the
   navigation module's `CommandPalette.tsx` is still never imported).
4. **TD-07** — the shared `/api/ai-os/v1` prefix collision across three real backends, now more urgent
   given how much real capability `ENTERPRISE_AI_OS.md` found living behind that one prefix.
5. **TD-45** — Production Center UI-ahead-of-backend risk; directly relevant to any near-term
   implementation sprint tempted to "just wire up one studio quickly."
6. **TD-43 / TD-44** — routing aliases and the self-admitted "double chrome" embed debt; lower severity
   but cheap to fix and currently undecided.
7. **New, not yet in the registry** — this review recommends `TECH_DEBT.md` gain a formal entry (or
   entries) for `SPRINT_28_0_RESULT.md`'s own six-item "Remaining work" list (§4 item 5, §8 item 5, §9
   items 4–6 above) — real, sprint-acknowledged debt currently living only in a historical record.

---

## Architecture gaps

The TS-kernel relationship (§1.1), the memory-stack triplication (§1.2, §2.2), the City-as-primary-
paradigm-vs-headline-app disagreement between two of this session's own documents (§1.3, §3.3), and the
undecided division of labor between the two real job-execution backends (§1.4, §2.4) are the four
structural decisions this platform most needs made and written down. None require new engineering to
resolve — all four are choices about *how existing real systems relate to each other*, which is exactly
what `00_MASTER_PRODUCT_BIBLE.md` §4's recommended ADR log exists to capture.

## UX gaps

Enterprise City's multiplayer/presence layer (§8.4), role-aware building visibility (§8.6), and three
personas' missing Dashboard profiles (§5.3) are the concrete UX debt. The City-vs-Desktop navigation
disagreement (§1.3) is also a UX gap in disguise: a user experiences whichever framing actually shipped,
regardless of which document is "right," so resolving §1.3 is as much a UX fix as an architecture one.

## Runtime gaps

By far the largest category in raw count (§9 in full, plus §4 items 4–5, §8 item 5): the frontend
Runtime Engine's near-total disconnection from every real backend runtime signal it could plausibly
consume. This is not a design gap — the design (`ENTERPRISE_AI_OS.md` §6, §10) is sound — it is a wiring
gap, and the three sprint-self-admitted items (WebSocket push, single poller, cross-window postMessage)
show the implementing team already knows this and has a punch list; that punch list simply hasn't
reached the living debt registry yet.

## AI gaps

The real Multi-Agent OS backend (Collaboration protocol, Task Orchestrator, layered Memory Manager) is
dramatically more capable than any frontend surface uses (§6.1–§6.2) — this is the single most
actionable AI-gap finding in this review, because it means the next AI-facing sprint's highest-leverage
move is *integration*, not *invention*. Voice-driven interaction (§5.1, §6.4) remains a wholesale gap
with no started work.

## Documentation gaps

Two kinds: (a) **things that should exist and don't** — `VOICE_FIRST_ENTERPRISE.md`, `FUTURE_RUNTIME.md`
(§5.1), a glossary resolving "Portal"/"Enterprise AI OS"/"Production" (§3.1–§3.2, §2.6, restated from
`00_MASTER_PRODUCT_BIBLE.md` §4 item 1); and (b) **things that exist in the wrong tier** —
`SPRINT_28_0_RESULT.md`'s real, self-admitted remaining-work items (§4.5, §8.5, §9.4–§9.6) sitting in a
Tier 4 historical record instead of the living `TECH_DEBT.md` registry, and the unresolved disagreement
between `ENTERPRISE_CITY_ARCHITECTURE.md` and `ENTERPRISE_CITY_BIBLE.md` (§1.3) that no single document
currently flags as a live inconsistency between two supposedly-authoritative sources.

## Priority recommendations

In order:

1. **Promote every sprint-self-admitted "remaining work" item found in this review into `TECH_DEBT.md`**
   (§4.5, §8.5, §9.4–§9.6) — the lowest-effort, highest-integrity fix available, since the analysis is
   already done by the implementing sprint itself.
2. **Resolve the City-as-primary-paradigm-vs-headline-app disagreement** (§1.3) with a single ADR, and
   update `ENTERPRISE_CITY_ARCHITECTURE.md` §0 to match whatever `ENTERPRISE_CITY_BIBLE.md`'s
   reality-update already concluded, so the two documents stop disagreeing.
3. **Wire the frontend Runtime Engine to at least one real backend** (`platform_ai_os`'s Executive
   Dashboard is the best-scoped first target, per `ENTERPRISE_AI_OS.md` §14) before any further
   simulated-metric surface is added on top of it.
4. **Write the ADR resolving the memory-stack question** (§1.2) before building the Creative Knowledge
   Base or any other new "memory" feature on top of an assumption that might be wrong.
5. **Start the glossary** (`00_MASTER_PRODUCT_BIBLE.md` §4 item 1) — every naming collision in §2–§3
   above resolves to the same root cause (no single place defines these terms once), and every one of
   them will recur again in the next sprint if the glossary keeps not existing.
6. **Fix TD-46 and TD-17** before any other implementation work in the Production Center or
   `platform_security` respectively — both are P0 for reasons independent of everything else in this
   review.
7. **Write `VOICE_FIRST_ENTERPRISE.md` and `FUTURE_RUNTIME.md`** once the above are stable — building
   voice/3D-era vision on top of an unresolved City/Desktop disagreement (#2) would just add a third
   inconsistency to reconcile later.

## Related documents

Every document named inline above by section reference. This review deliberately does not repeat a
"related documents" list at the scale this session's other Bibles use, since nearly the entire
documentation set is in scope — the inline references throughout are the map.
