# User Experience Backlog

**Status:** permanent, living backlog. Documentation only — no source code was modified to produce
this file. Every item below is the actionable counterpart of a finding in `docs/UX_REVIEW.md` — that
document explains *why* each item matters from a user's seat; this document makes each one sprint-ready.
Distinct from `ARCHITECTURE_DECISIONS_BACKLOG.md`: that backlog tracks system/architecture decisions and
backend integration work; this one tracks interaction-level fixes a user would notice directly. Where
the two overlap (e.g., notification push latency), this document cross-references the `ADB-##` item
rather than duplicating its detail.

**Severity vocabulary (matches `docs/UX_REVIEW.md`, deliberately distinct from `TECH_DEBT.md`'s
P0–P3):** **Critical** (blocks or silently breaks a core daily task) · **High** (real, repeated
friction) · **Medium** (real but occasional friction) · **Low** (polish).

**Effort vocabulary (matches `ARCHITECTURE_DECISIONS_BACKLOG.md`):** S (<1 day) · M (1–3 days) ·
L (1–2 weeks) · XL (multi-sprint).

---

## Index (priority order)

| ID | Title | Surface | Priority | Effort |
|---|---|---|---|---|
| UXB-01 | "Create X" quick actions don't create anything | CRM, Knowledge, Production, Command Center | **Critical** | M |
| UXB-02 | Production Center studios accept input and silently produce nothing | Production Center | **Critical** | S (messaging fix) |
| UXB-03 | No accessible non-spatial equivalent of Enterprise City | Enterprise City | **Critical** | L |
| UXB-04 | Double chrome inside most Desktop windows | Enterprise Desktop | High | M |
| UXB-05 | Two "agent list" experiences disagree with each other | AI Agents | High | M |
| UXB-06 | No "coming soon"/preview badge on non-functional Production Center studios | Production Center | High | S |
| UXB-07 | Marketplace hub has no path to a specific real vertical marketplace | Marketplace | High | M |
| UXB-08 | No district-first onboarding for Enterprise City | Enterprise City | High | M |
| UXB-09 | No WebSocket push — notifications feel late | Notifications | High | (see ADB-10) |
| UXB-10 | Command Palette advertises broken actions to the platform's own audience | Command Center | High | (see UXB-01) |
| UXB-11 | "Production" district name collides with AI Production Center | Enterprise City | Medium | (see ADB-05) |
| UXB-12 | No onboarding for the Desktop window metaphor itself | Enterprise Desktop | Medium | M |
| UXB-13 | CRM hub gives no CRM-specific affordance beyond the generic template | CRM | Medium | L |
| UXB-14 | No bulk actions in the Notifications Panel | Notifications | Medium | M |
| UXB-15 | Settings' correct embed behavior isn't explained as intentional | Settings | Medium | S |
| UXB-16 | No orientation message on first open of a generic Hub module | Marketplace, Knowledge | Medium | S |
| UXB-17 | No "why is this agent busy" explanation | AI Agents | Medium | M |
| UXB-18 | Five palette-summon shortcuts presented with equal weight | Command Center | Medium | S |
| UXB-19 | Reopen-closed-window shortcut has no visible affordance | Enterprise Desktop | Low | S |
| UXB-20 | No hint that zoom has three equivalent inputs | Enterprise City | Low | S |
| UXB-21 | AI Studio vs. AI Team Center — no guidance on which to use | AI Agents | Low | S |
| UXB-22 | No dedicated in-Knowledge search distinct from global search | Knowledge Base | Low | M |
| UXB-23 | No settings-page search/filter | Settings | Low | S |
| UXB-24 | Toast/panel can show a slightly different "latest" item | Notifications | Low | S |
| UXB-25 | Missing proactive AI assistance at four identified moments | Cross-cutting | High | (see below) |

---

## Detailed items

### UXB-01 — "Create X" quick actions don't create anything

- **Problem:** Command Palette actions `create_client`, `create_project`, `create_task`,
  `create_document`, `create_ai_agent`, `create_knowledge`, `create_workflow`
  (`command-center/managers/quickActions.ts`) navigate to `{route}?action=create_x`, but
  `EnterpriseModulePage.tsx` only logs an activity entry and shows a `Badge` — no form or dialog ever
  opens.
- **User impact:** a user who trusts the platform's own advertised shortcut believes they created
  something; nothing was created. This is the single most concrete broken promise found in this review.
- **Proposed fix:** either (a) implement a real lightweight creation dialog triggered by `action`, or
  (b) if the real creation flow lives elsewhere, redirect `action` to that real flow instead of the
  generic Hub page. Fix once in `EnterpriseModulePage.tsx`/`ModuleHubRoute.tsx` and every module using
  the shared template inherits the fix.
- **Affected surface(s):** CRM, Knowledge, Projects, Documents, AI Agents, Automation (every module
  reachable via the generic Hub template).
- **Priority:** **Critical.**
- **Effort:** M.
- **Depends on:** none.

### UXB-02 — Production Center studios accept input and silently produce nothing

- **Problem:** none of the 17 studios has a real generation provider behind it
  (`AI_PRODUCTION_CENTER_BIBLE.md` §0); attempting to generate produces no output and no explanation.
- **User impact:** a user cannot tell whether they made a mistake, the system is broken, or the feature
  simply isn't built yet.
- **Proposed fix:** short-term, add an explicit in-studio message ("Generation isn't connected yet —
  this studio is a preview of the upcoming workflow") gated the same way `readiness: "coming_soon"`
  already gates Hub modules; long-term, resolved by `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-22.
- **Affected surface(s):** Production Center (all 17 studios).
- **Priority:** **Critical** (as a messaging fix; the underlying capability gap is tracked separately
  and is XL).
- **Effort:** S (messaging only).
- **Depends on:** none for the messaging fix; ADB-22 for the real capability.

### UXB-03 — No accessible non-spatial equivalent of Enterprise City

- **Problem:** the City map has no List View equivalent (`ENTERPRISE_CITY_ARCHITECTURE.md` §20,
  tracked as `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-29).
- **User impact:** a keyboard-only or screen-reader user cannot use the platform's primary navigation
  surface at all, not just less conveniently.
- **Proposed fix:** see `ADB-29` for full detail — this item exists in this backlog specifically to
  keep it visible from a pure UX-severity lens (Critical here vs. P1 there, reflecting the different
  audiences the two backlogs serve).
- **Affected surface(s):** Enterprise City.
- **Priority:** **Critical.**
- **Effort:** L.
- **Depends on:** `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-28, ADB-29.

### UXB-04 — Double chrome inside most Desktop windows

- **Problem:** only `WorkspaceLayout` and `SettingsPage` honor `?embed=1`; every other hub renders full
  page chrome inside the window frame (`WINDOW_MANAGER.md`'s own admission, `TECH_DEBT.md` TD-44).
- **User impact:** visually redundant, and a new user's first impression of Desktop windows is a
  cluttered one.
- **Proposed fix:** extend `?embed=1` handling to every Hub-templated module (same shared template as
  UXB-01, meaning both fixes could land in the same pass).
- **Affected surface(s):** Enterprise Desktop (every windowed app except Workspace/Settings).
- **Priority:** High.
- **Effort:** M.
- **Depends on:** none; natural pairing with UXB-01 since both touch `EnterpriseModulePage`.

### UXB-05 — Two "agent list" experiences disagree with each other

- **Problem:** the Command Center's AI panel demo roster, the Runtime Engine's simulated
  `aiAgentRuntime` roster, and the real backend Agent Registry (`/agents`) are three different lists
  (`ENTERPRISE_AI_OS.md` §9, `docs/UX_REVIEW.md` §5).
- **User impact:** asking "what agents do I have" in two different places gives two different answers —
  a trust-eroding inconsistency.
- **Proposed fix:** converge on one roster source once `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-07/
  ADB-16 wire a real backend consumer; until then, at minimum label each demo roster as illustrative.
- **Affected surface(s):** AI Agents, Command Center.
- **Priority:** High.
- **Effort:** M (labeling fix); full convergence is L, tracked via ADB-07/ADB-16.
- **Depends on:** ADB-07, ADB-16 for the full fix.

### UXB-06 — No "coming soon"/preview badge on non-functional Production Center studios

- **Problem:** the Hub template's real `readiness` badge pattern is not reused inside Production Center
  studio cards.
- **User impact:** studios look fully live when none are.
- **Proposed fix:** apply the existing `readiness` badge component to each studio card, reusing the
  pattern rather than inventing a new one (`02_PRODUCT_PHILOSOPHY.md` principle 7).
- **Affected surface(s):** Production Center.
- **Priority:** High.
- **Effort:** S.
- **Depends on:** none.

### UXB-07 — Marketplace hub has no path to a specific real vertical marketplace

- **Problem:** the generic `/marketplace` Hub page describes the concept abstractly; it has no link
  into `auto_marketplace`/`agro_marketplace`/`applications/marketplace` specifically.
- **User impact:** a user looking for "my marketplace" lands on an overview with nothing to click
  through to.
- **Proposed fix:** surface the tenant's actually-enabled marketplace verticals as real quick-action
  links on the generic hub, sourced from the same per-tenant vertical enablement
  (`platform_management`) every other surface already reads.
- **Affected surface(s):** Marketplace.
- **Priority:** High.
- **Effort:** M.
- **Depends on:** none.

### UXB-08 — No district-first onboarding for Enterprise City

- **Problem:** `ENTERPRISE_CITY_BIBLE.md` §8 designs teaching districts before buildings on first visit;
  not built.
- **User impact:** a first-time user is dropped onto a spatial map with no orientation.
- **Proposed fix:** a short, skippable first-visit overlay naming the visible districts before letting
  the map render fully interactive.
- **Affected surface(s):** Enterprise City.
- **Priority:** High.
- **Effort:** M.
- **Depends on:** none; benefits from UXB-03 landing first so onboarding teaches one consistent surface.

### UXB-09 — No WebSocket push — notifications feel late

- **Problem/fix:** see `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-10 in full — not re-described here.
- **Affected surface(s):** Notifications.
- **Priority:** High (user-felt latency, distinct from ADB-10's P2 architecture-priority framing).
- **Effort:** see ADB-10.
- **Depends on:** ADB-10.

### UXB-10 — Command Palette advertises broken actions to the platform's own audience

- **Problem:** the Command Palette is the platform's flagship, most-polished surface
  (`docs/UX_REVIEW.md` §8) — which makes UXB-01's breakage there specifically damaging to trust, since
  it's the first place a new or power user tries a shortcut.
- **User impact:** same as UXB-01, amplified by the palette's role as the platform's advertised
  fast-path.
- **Proposed fix:** same fix as UXB-01; this item exists to flag the palette specifically as the
  highest-visibility instance to prioritize first.
- **Affected surface(s):** Command Center.
- **Priority:** High.
- **Effort:** — (resolved by UXB-01).
- **Depends on:** UXB-01.

### UXB-11 — "Production" district name collides with AI Production Center

- **Problem/fix:** see `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-05 (ADR) in full.
- **Affected surface(s):** Enterprise City.
- **Priority:** Medium.
- **Effort:** see ADB-05.
- **Depends on:** ADB-05.

### UXB-12 — No onboarding for the Desktop window metaphor itself

- **Problem:** a user arriving from the old Dashboard-first mental model has no in-product
  introduction to windows/snap/persistence.
- **User impact:** discovery is accidental, not guided — a real but non-blocking first-impression gap.
- **Proposed fix:** a brief first-run tooltip sequence on `/desktop`'s first visit (Dock, Launcher,
  one window action) — skippable, shown once.
- **Affected surface(s):** Enterprise Desktop.
- **Priority:** Medium.
- **Effort:** M.
- **Depends on:** none.

### UXB-13 — CRM hub gives no CRM-specific affordance beyond the generic template

- **Problem:** CRM, ERP, Marketplace, Knowledge, and Analytics all render from the same
  `EnterpriseModulePage` template with no domain-specific view (no pipeline board, no contact list).
- **User impact:** CRM "feels" like a placeholder rather than a working CRM, even where real backend
  data may exist behind it.
- **Proposed fix:** a real CRM-specific view (pipeline/contacts) is a larger product decision beyond
  this backlog's scope — flagged here as a finding, not solved here.
- **Affected surface(s):** CRM (and by extension every Hub-templated module).
- **Priority:** Medium.
- **Effort:** L.
- **Depends on:** a product decision on which modules deserve a bespoke view vs. staying generic.

### UXB-14 — No bulk actions in the Notifications Panel

- **Problem:** `WORKSPACE_INTERACTIONS.md` §3's multi-selection model is designed but not applied to
  the Notifications Panel; only `markAllRead` exists as a bulk action.
- **User impact:** clearing/dismissing several related notifications requires one-at-a-time action.
- **Proposed fix:** apply the existing (designed, not yet built) multi-selection pattern to the
  Notifications Panel specifically, as its first real adopter.
- **Affected surface(s):** Notifications.
- **Priority:** Medium.
- **Effort:** M.
- **Depends on:** `WORKSPACE_INTERACTIONS.md` §3's general multi-select primitive landing first (or
  building it scoped to this one surface as a pilot).

### UXB-15 — Settings' correct embed behavior isn't explained as intentional

- **Problem:** Settings is one of two pages that correctly avoid double chrome (§UXB-04); nothing tells
  a user this is deliberate rather than a random inconsistency.
- **User impact:** low-severity confusion for an attentive user comparing two windows.
- **Proposed fix:** resolved naturally once UXB-04 extends embed handling everywhere — no longer an
  asymmetry to explain.
- **Affected surface(s):** Settings.
- **Priority:** Medium.
- **Effort:** S.
- **Depends on:** UXB-04 (superseded once that lands).

### UXB-16 — No orientation message on first open of a generic Hub module

- **Problem:** Marketplace/Knowledge (and every generic Hub module) show the same abstract overview
  regardless of whether a tenant has anything configured.
- **User impact:** a new tenant sees a generic description with no indication of their own actual
  configuration state.
- **Proposed fix:** a one-line Advisor-voiced orientation message on first open, reusing the existing
  Executive Advisor tone (`08_AI_PERSONALITY.md`) — see also UXB-25.
- **Affected surface(s):** Marketplace, Knowledge Base (and, by pattern, every generic Hub module).
- **Priority:** Medium.
- **Effort:** S.
- **Depends on:** none.

### UXB-17 — No "why is this agent busy" explanation

- **Problem:** the simulated agent roster's busy/idle rotation has no accompanying explanation visible
  to a user.
- **User impact:** low-severity, since the roster is largely illustrative today (UXB-05), but sets a bad
  precedent for when it's real.
- **Proposed fix:** any future real agent-status surface should pair a status change with a one-line
  reason, matching `AI_AGENTS_BIBLE.md` §5's transparency rule.
- **Affected surface(s):** AI Agents.
- **Priority:** Medium.
- **Effort:** M.
- **Depends on:** ADB-07/ADB-16 (relevant once the roster is real).

### UXB-18 — Five palette-summon shortcuts presented with equal weight

- **Problem:** `⌘K`/`⌘P`/`⌘⇧P`/`⌘/`/`⌘Space` all open a palette-family surface with no in-product
  guidance on which one to actually remember.
- **User impact:** more choice than most users need; dilutes the "one fast path" promise.
- **Proposed fix:** a first-run tooltip or Command Center help panel naming `⌘K` as the one to remember,
  without removing the other four (they remain valid muscle-memory entry points for users coming from
  other tools).
- **Affected surface(s):** Command Center.
- **Priority:** Medium.
- **Effort:** S.
- **Depends on:** none.

### UXB-19 — Reopen-closed-window shortcut has no visible affordance

- **Problem:** `Cmd/Ctrl+Shift+T` is real (`WINDOW_MANAGER.md`) but has no Dock/menu hint.
- **User impact:** keyboard-first users benefit silently; mouse-first users never discover it.
- **Proposed fix:** a small "reopen last closed" affordance in the Dock or window-close confirmation.
- **Affected surface(s):** Enterprise Desktop.
- **Priority:** Low.
- **Effort:** S.
- **Depends on:** none.

### UXB-20 — No hint that zoom has three equivalent inputs

- **Problem:** `+`/`-`/scroll-wheel all zoom the City map identically, undocumented in-product.
- **User impact:** cosmetic; a user who discovers one input has no reason to look for the others, which
  is fine, but a tooltip would help power users.
- **Proposed fix:** a tooltip on the zoom control listing the scroll-wheel equivalent.
- **Affected surface(s):** Enterprise City.
- **Priority:** Low.
- **Effort:** S.
- **Depends on:** none.

### UXB-21 — AI Studio vs. AI Team Center — no guidance on which to use

- **Problem:** both a real Hub module (`/ai-studio`) and a real City building (AI Team Center) exist
  with no stated distinction for a user choosing between them.
- **User impact:** low-severity ambiguity, resolved case-by-case by exploration.
- **Proposed fix:** a one-line distinction in whichever surface a user reaches first (e.g., "AI Studio:
  configure agents · AI Team Center: see them working").
- **Affected surface(s):** AI Agents.
- **Priority:** Low.
- **Effort:** S.
- **Depends on:** none.

### UXB-22 — No dedicated in-Knowledge search distinct from global search

- **Problem:** the Knowledge hub has no scoped "search my knowledge base" box, only the shared global
  `⌘K` search.
- **User impact:** low-severity; global search already covers knowledge documents, per
  `ENTERPRISE_NAVIGATION.md` §6's real search index.
- **Proposed fix:** a scoped search box that pre-filters global search results to the Knowledge
  category, rather than a separate search implementation.
- **Affected surface(s):** Knowledge Base.
- **Priority:** Low.
- **Effort:** M.
- **Depends on:** none.

### UXB-23 — No settings-page search/filter

- **Problem:** Settings has no `⌘K`-style in-page filter, unlike the platform's search-first posture
  elsewhere.
- **User impact:** low-severity on a page of this size today; would compound if Settings grows.
- **Proposed fix:** a simple client-side filter over the settings sections list.
- **Affected surface(s):** Settings.
- **Priority:** Low.
- **Effort:** S.
- **Depends on:** none.

### UXB-24 — Toast/panel can show a slightly different "latest" item

- **Problem:** display-timing nuance if a toast is dismissed before the panel is opened; both read the
  same store, so this is not a data bug.
- **User impact:** cosmetic, low-severity.
- **Proposed fix:** a quick visual QA pass to confirm consistent "most recent" ordering between the two
  views.
- **Affected surface(s):** Notifications.
- **Priority:** Low.
- **Effort:** S.
- **Depends on:** none.

### UXB-25 — Missing proactive AI assistance at four identified moments

- **Problem:** four concrete moments where the Executive Advisor should appear unasked and doesn't
  (`docs/UX_REVIEW.md`'s cross-cutting findings #3): a failed "Create X" action (UXB-01), a
  non-functional Production Center studio (UXB-02), first open of a generic Hub module (UXB-16), and a
  burst of related notifications.
- **User impact:** each moment currently leaves a user to self-diagnose what the platform's own AI
  voice is well-positioned to explain proactively.
- **Proposed fix:** extend the existing Advisor/`smartSuggestions` mechanism (`08_AI_PERSONALITY.md`,
  `ENTERPRISE_NAVIGATION.md` §20) to trigger on these four events specifically, reusing the same
  Observation→Why→Action→Impact structure already used everywhere else the Advisor speaks — never a
  new AI voice or mechanism.
- **Affected surface(s):** Cross-cutting (CRM/Knowledge/Automation, Production Center, Marketplace/
  Knowledge, Notifications).
- **Priority:** High.
- **Effort:** M once UXB-01/UXB-02/UXB-16 land (the Advisor needs a real event to react to first).
- **Depends on:** UXB-01, UXB-02, UXB-16.

## Related documents

`docs/UX_REVIEW.md` (the narrative source for every item above), `docs/NAVIGATION_IMPROVEMENTS.md`
(navigation-specific items consolidated separately), `ARCHITECTURE_DECISIONS_BACKLOG.md` (ADB-05,
ADB-07, ADB-10, ADB-16, ADB-22, ADB-28, ADB-29 — cross-referenced, not duplicated), `TECH_DEBT.md`
(TD-40, TD-44), `08_AI_PERSONALITY.md`, `UX_GUIDELINES.md`.
