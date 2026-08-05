# UX Review — The Platform From the User's Seat

**Status:** permanent, living review. Documentation only — no source code was modified to produce this
review. This document walks through ten real surfaces the way a user actually experiences them — login
to daily work — and records what's confusing, redundant, missing a shortcut, inconsistent, missing
onboarding, inaccessible, a workflow bottleneck, or a place AI should show up unasked. It does not
re-derive architecture-level findings already in `PRODUCT_ARCHITECTURE_REVIEW.md` or
`ARCHITECTURE_DECISIONS_BACKLOG.md` — it references them, and adds what only a user-perspective
walkthrough surfaces: friction inside a real screen, not a gap between two systems.

**Severity vocabulary for this review (deliberately distinct from `TECH_DEBT.md`'s P0–P3, since this is
a UX audience, not an engineering-priority one):**

- **Critical** — blocks or silently breaks a core daily task; a user cannot complete what they came to
  do, or believes they did something that didn't actually happen.
- **High** — real, repeated friction on a common task; workable, but slower or more confusing than it
  should be every time.
- **Medium** — real friction, but occasional or non-blocking.
- **Low** — polish; a returning user barely notices it, a new user might.

Every finding here is echoed, with full detail (problem/impact/fix/effort), in
`docs/USER_EXPERIENCE_BACKLOG.md` — this document is the narrative walkthrough; that one is the
actionable list. Navigation-specific findings are consolidated separately in
`docs/NAVIGATION_IMPROVEMENTS.md` rather than repeated here in full.

---

## 1. Enterprise Desktop

Real: window manager (move/resize/minimize/maximize/snap/reopen-closed), Dock, Launcher (`Cmd/Ctrl+
Space`), session-persisted (`DESKTOP.md`, `WINDOW_MANAGER.md`).

**Walkthrough — opening CRM from a cold Desktop session:** Launcher → type or click CRM → a window
opens, embedding `/crm?embed=1`.

- **[High] Double chrome inside most windows.** `WINDOW_MANAGER.md` itself admits this: only
  `WorkspaceLayout` and `SettingsPage` honor `?embed=1` by suppressing their own chrome; every other hub
  (CRM, ERP, Marketplace, Knowledge, Analytics — all real `EnterpriseModulePage` instances) renders its
  full page chrome *inside* the window frame, so a user sees a header/nav bar twice — the window's own
  title bar, and the embedded page's. Already tracked as `TECH_DEBT.md` TD-44; restated here as the
  first thing a new user notices about the Desktop specifically.
- **[Medium] No onboarding for the Desktop metaphor itself.** A user arriving from the old Dashboard-
  first mental model has no in-product explanation that windows exist, snap, or persist — the first
  discovery is accidental (double-clicking an icon) rather than guided.
- **[Low] Reopen-closed (`Cmd/Ctrl+Shift+T`) has no visible affordance.** The shortcut is real
  (`WINDOW_MANAGER.md`) but nothing in the Dock or window chrome hints it exists — a keyboard-first user
  benefits, a mouse-first user never discovers it.

## 2. Enterprise City

Real: 12-district catalog, real camera engine, real navigation memory (`CITY_ENGINE.md`,
`CITY_DISTRICTS.md`). Already the subject of extensive review in `ENTERPRISE_CITY_BIBLE.md`,
`ENTERPRISE_CITY_ARCHITECTURE.md`, and `PRODUCT_ARCHITECTURE_REVIEW.md` §8 — this section adds only
what a fresh user-perspective pass surfaces beyond those.

- **[Critical] No accessible non-spatial equivalent exists yet.** Already tracked
  (`ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-29) — restated here at Critical severity specifically
  because, from a user's seat, a keyboard-only or screen-reader user cannot use this surface *at all*
  today, not just less conveniently.
- **[High] A first-time user has no explanation of what a "district" or "building" means before being
  dropped onto the map.** `ENTERPRISE_CITY_BIBLE.md` §8 designs district-first onboarding; it is not
  built. A returning user's existing mental model (from the old Dashboard-first flow) doesn't transfer.
- **[Medium] The "Production" district's name collides with the AI Production Center** (already
  flagged as a naming/module conflict in `PRODUCT_ARCHITECTURE_REVIEW.md` §1 item 5/§3 restated) — from
  a pure navigation-friction angle, a user clicking "Production" expecting the creative studio and
  landing on Mission Control (or vice versa) is a real, repeatable moment of confusion, not just a
  documentation ambiguity.
- **[Low] No visible hint that `+`/`-`/scroll all do the same zoom action** — three input methods for
  one operation, undocumented in-product.

## 3. CRM

Real: a generic `EnterpriseModulePage` hub template (`ModuleHubRoute.tsx`) — not a bespoke CRM
experience; the same template renders ERP, Marketplace, Knowledge, Analytics, etc.

**Walkthrough — creating a new client via the Command Palette (the fastest path the product itself
advertises):** `⌘K` → "Create Client" → navigates to `/crm?action=create_client`.

- **[Critical] The "Create Client" quick action does not create anything.** Confirmed by direct code
  read: `EnterpriseModulePage.tsx` reads the `action` query param, logs an activity-journal entry, and
  shows a `Badge` reading `Action: create_client` — **no form, dialog, or creation flow ever opens.**
  This is the single most concrete, user-visible broken promise found in this entire review: the
  platform's own Command Palette advertises "Create Client" as a real action, and completing it produces
  only a cosmetic badge. The same is true for every other `create_*` quick action (`create_project`,
  `create_task`, `create_document`, `create_ai_agent`, `create_knowledge`, `create_workflow`,
  `quickActions.ts`) — this is a pattern, not a one-off.
- **[High] No way to tell, from the CRM hub itself, that "Create Client" didn't work.** The badge reads
  as confirmation, not as a stub — a new user has no signal to go looking for the real creation path
  elsewhere.
- **[Medium] The CRM hub is templated identically to unrelated modules** (ERP, Marketplace) — real per
  `MODULES.md`'s "Hub component" convention, but from a user's seat, CRM's "Overview → Statistics →
  Status → Recent Activity → Configuration → Quick Actions → Roadmap" structure gives no CRM-specific
  affordance (no pipeline view, no contact list) beyond what the generic template offers everywhere.

## 4. Production Center

Real: 17-studio shell, real approval-gated pipeline, no real generation behind any studio
(`AI_PRODUCTION_CENTER_BIBLE.md` §0 — already the most thoroughly documented status-honesty finding in
this whole documentation set).

- **[Critical] A user can open any of 17 studios and attempt to generate something, with no real
  output ever produced, and no in-product message explaining why.** This is the user-facing consequence
  of the well-documented backend gap — from a pure UX angle, a studio that accepts input and silently
  produces nothing is worse than a studio that's visibly disabled with an explanation.
- **[High] No visible "this is a preview/demo" framing anywhere in the 17-studio shell.** Compare to
  the honest `readiness: "coming_soon"` badge treatment the generic Hub template already supports
  (`MODULES.md`'s `EnterpriseModuleDef` — a real, existing pattern) — the Production Center does not
  reuse this pattern for its non-functional studios, so it looks fully live when it isn't.
- **[Medium] Agent-assignment UI (real) has no indication that the assigned agent doesn't actually do
  anything yet** (`AI_PRODUCTION_CENTER_BIBLE.md` §2) — assigning "Ops Copilot" to a studio reads as a
  real delegation.

## 5. AI Agents

Real: Agent Registry (both the Command Center's AI panel and the Multi-Agent OS's real backend
registry, `ENTERPRISE_AI_OS.md`), a real NLU parser for the Command Palette's AI mode.

- **[High] Two different "agent list" experiences exist and don't agree with each other.** The Command
  Center's AI panel (`COMMAND_CENTER.md`) shows a demo agent roster; the frontend Runtime Engine's
  `aiAgentRuntime` (`ENTERPRISE_AI_OS.md` §9) shows a *different* synthetic roster with soft-rotating
  busy/idle status; the real backend Agent Registry 2.0 (`/agents`) is a third, unconsumed list. A user
  who checks "what agents exist" in two different places can get two different answers.
- **[Medium] No agent ever explains what it's about to do before doing it** — real per
  `AI_AGENTS_BIBLE.md` §5's transparency rule being aspirational for anything beyond the Executive
  Advisor's own recommendations; the simulated roster's "busy" status has no accompanying explanation
  visible to a user.
- **[Low] "AI Studio" (a real Hub module) and "AI Team Center" (a real City building) both exist and
  a user has no clear reason to prefer one over the other** for a given task.

## 6. Marketplace

Real: a generic Hub module (`moduleCatalog.ts` id `marketplace`), same template as CRM/ERP.

- **[High] "Marketplace" as a City district/Hub module is not the same thing as the real vertical
  marketplaces** (`auto_marketplace`, `agro_marketplace`, `applications/marketplace`,
  `ARCHITECTURE_MAP.md` §9) — a user clicking Marketplace from the Command Palette or City lands on a
  generic overview page, not any specific vertical storefront; there is no visible path from the generic
  hub to a specific real marketplace application.
- **[Medium] No onboarding or explanation of what "Marketplace" contains** before a user opens it — the
  generic hub's "Overview" hero is populated from `moduleCatalog.ts` data, which describes the concept
  in the abstract, not what a specific tenant's enabled marketplaces actually are.

## 7. Knowledge Base

Real: a generic Hub module (id `knowledge`), same template pattern.

- **[High] "Create Knowledge" quick action has the identical broken-promise problem as CRM's "Create
  Client"** (§3) — same root cause (`EnterpriseModulePage`'s `action` param handling), same fix.
- **[Medium] No search-within-Knowledge affordance distinct from the platform's global search** — a
  user inside the Knowledge hub has no dedicated "search my knowledge base" box, only the same `⌘K`
  global search everyone else uses for everything.

## 8. Command Center

Real, and the most mature real surface in the platform: Command Palette (`⌘K`), Omnibox (`⌘P`), AI mode
(`⌘⇧P`), Global Activity Feed, AI Command Center panel, Enterprise Metrics Strip, Universal Quick
Actions, Status Bar (`COMMAND_CENTER.md`).

- **[Critical] The "Create" section's actions are the primary source of §3/§7's broken-promise
  finding.** This is the single highest-leverage place to fix the create-action gap, since every
  broken "Create X" action in this review routes through this one catalog
  (`command-center/managers/quickActions.ts`).
- **[High] Two Command Palettes exist; only one runs.** Already tracked as `TECH_DEBT.md` TD-40 — from
  a pure user-perspective angle, this is invisible to the user *today* (the dead one never renders), but
  it is the single largest risk that a future fix to one palette's shortcuts/catalog silently doesn't
  apply to muscle memory built around the other if the wrong one is ever surfaced.
- **[Medium] Five ways to open essentially the same palette family** (`⌘K`, `⌘P`, `⌘⇧P`, `⌘/`, `⌘Space`)
  is real and documented (`ENTERPRISE_NAVIGATION.md` §16, `COMMAND_CENTER.md`) but is more entry points
  than most users will ever intentionally use — worth a first-run tooltip explaining the *one* they
  should remember (`⌘K`), rather than presenting all five with equal weight.

## 9. Notifications

Real: one shared `notificationStore`, toast (6s auto-dismiss) + persistent panel, cross-module-unified
badge counts (`ENTERPRISE_NAVIGATION.md` §12, `INTEGRATION_HUB.md`).

- **[High] No WebSocket push yet — notifications arrive on a poll cadence, not instantly.** Already
  tracked (`SPRINT_28_0_RESULT.md`'s own remaining-work list, `ARCHITECTURE_DECISIONS_BACKLOG.md`
  ADB-10) — restated here because "notifications feel late" is a direct, felt user experience, not
  only a backend-wiring concern.
- **[Medium] No bulk actions in the Notifications Panel** (mark-all-read exists per
  `notificationStore.markAllRead`, but no bulk *dismiss* or bulk *filter-then-act* pattern) —
  `WORKSPACE_INTERACTIONS.md` §3's multi-selection model is designed but not applied here.
- **[Low] Toast and panel can show slightly different "latest" items** if a toast is dismissed
  before the panel is opened — both read the same store, so this is a display-timing nuance, not a
  data inconsistency, but worth confirming with a quick visual QA pass.

## 10. Settings

Real: `SettingsPage.tsx`, one of only two pages (with `WorkspaceLayout`) that correctly honor
`?embed=1` (§1).

- **[Medium] Settings is the one surface that correctly handles embedding, and nothing in-product
  explains why it behaves differently from every other window** — a user who notices CRM's double
  chrome (§1) but not Settings' clean embed has no way to know this is a known, tracked asymmetry
  (`TECH_DEBT.md` TD-44) rather than random inconsistency.
- **[Low] No settings search** — a long settings page with no `⌘K`-style in-page filter, unlike most of
  the rest of the platform's search-first posture.

---

## Cross-cutting findings (patterns, not single-surface issues)

1. **The single most valuable fix in this entire review is the "Create X" quick-action gap** (§3, §4,
   §7, §8) — one root cause (`EnterpriseModulePage`'s `action` param handling), touching CRM, Knowledge,
   and every other Hub-templated module, surfaced as the platform's own advertised Command Palette
   shortcut. Fixing the shared template once fixes every instance.
2. **"This is not real yet" has no consistent visual language.** The Hub module template already has a
   real `readiness: "coming_soon"` badge pattern (`MODULES.md`); Production Center's studios and the
   simulated AI agent rosters (§4, §5) don't reuse it. One honest-status pattern exists; it should be
   applied everywhere something looks live but isn't.
3. **Missing AI assistance — the places AI should appear automatically and doesn't:**
   - **CRM (§3):** when a "Create Client" action fails to open a real form, the Executive Advisor
     should proactively explain what's happening, rather than the badge silently standing in.
   - **Production Center (§4):** a studio with no real generation behind it is exactly where a "this
     isn't wired up yet, here's what it will do" Advisor message would turn a dead end into a
     legible one.
   - **Marketplace/Knowledge (§6, §7):** first-open of a generic Hub module is a natural moment for a
     one-line Advisor orientation ("this connects to your enabled marketplaces — you don't have any
     configured yet"), currently absent.
   - **Notifications (§9):** a burst of related notifications (e.g., multiple job failures) is a
     natural moment for the Advisor to summarize rather than leaving a user to read each one — this
     is the concrete "why doesn't AI just tell me" moment a support ticket would eventually surface.

## Related documents

`docs/USER_EXPERIENCE_BACKLOG.md` (every finding above, actionable), `docs/NAVIGATION_IMPROVEMENTS.md`
(navigation-specific detail), `PRODUCT_ARCHITECTURE_REVIEW.md`, `ARCHITECTURE_DECISIONS_BACKLOG.md`
(the architecture-level findings this review builds on rather than repeats), `USER_JOURNEYS.md`
(the ten-persona journeys this surface-by-surface review complements), `TECH_DEBT.md` (TD-40, TD-44 —
cited, not restated), `UX_GUIDELINES.md`, `ENTERPRISE_DESIGN_SYSTEM.md`, `08_AI_PERSONALITY.md` (the
Advisor voice every "missing AI assistance" finding above assumes).
