# Workspace Interactions — Complete Interaction Pattern Language

**Status:** permanent product bible chapter, new document. Documentation only — no source code should
be modified as a result of reading it. This defines **one unified interaction language** for
everything a user touches, drags, selects, or collaborates on across the platform. Where
`ENTERPRISE_NAVIGATION.md` describes how a user *moves between* surfaces, this document describes how
a user *acts within* one — and where `ENTERPRISE_DESIGN_SYSTEM.md` defines the visual/motion tokens,
this document defines the *behavioral* rules those tokens are applied to.

## 0. What already exists vs. what this designs

Grounded in direct code research across `src/web`. Read this first — several interaction concepts
below are real and working in exactly one place today; the design work in this document is mostly
**generalizing one real pattern to every surface that needs it**, not inventing unrelated new ones.

| Concept | Exists today? | Where | Reality check |
|---|---|---|---|
| Drag-and-drop | **Yes, but only for one thing** | `WorkspaceTabBar.tsx` | Native HTML5 drag-and-drop (`draggable`, `onDragStart/Over/Drop`) reorders open workspace tabs. **No `dnd-kit` dependency exists in `src/web`** (unlike `platform_console`, which does use it for its own widget grid). Dashboard/workspace widgets have **no drag-and-drop at all** — `WidgetCard.tsx` only has "Move"/"Resize" buttons that nudge position by fixed increments. Widget drag-and-drop is genuinely new (§1). |
| Selection / multi-selection | **Absent** | — | Zero real bulk multi-select pattern anywhere in `src/web` (confirmed by grep for selection-state patterns). Genuinely new (§2, §3). |
| Context menus (right-click) | **Yes, exactly one place** | `WorkspaceTabBar.tsx` | The only `onContextMenu` implementation in the app (tab right-click: activate/pin/duplicate/close/reopen). No general-purpose `ContextMenu` primitive exists in the design system catalog. Generalizing this is the direct subject of §5. |
| Hover behaviors | **Yes, real, token-driven** | `ENTERPRISE_DESIGN_SYSTEM.md` §5, §13 | Card hover-lift, button hover-lift, table row hover — all real, all driven by shared motion tokens. Nothing new to design here; §6 restates the rule for completeness of this document's coverage. |
| Glass effects | **Yes, real, chrome-only** | `ENTERPRISE_DESIGN_SYSTEM.md` §6 | Backdrop-blur reserved for header/sidebar chrome; content stays solid. Restated in §7 as it applies to this document's window/panel/floating-surface behaviors specifically. |
| Widget behavior | **Yes, real but limited** | `workspace/managers/widgetManager.ts` | 14-kind widget catalog, real `move/resize/configure`, but move/resize are button-driven increments, not drag/resize handles (§1, §8). |
| Window management | **Absent as a concept** | — | This is a page-based SPA; there is no multi-window manager. What exists are Tabs (real) and Dock panels (real) — treated in this document as the two *existing* primitives "window management" (§9) organizes, not as evidence a window manager already exists. |
| Tab management | **Yes, real and fairly complete** | `WorkspaceTabBar.tsx`, `workspaceManagerStore.ts` | Real drag-reorder, pin/unpin (pinned tabs can't be closed), duplicate, close, reopen-closed (one-level-deep, not a full history stack), right-click menu. The most mature interaction surface in the app — the template §1–§5 generalize from. |
| Split views | **Absent** | — | Zero results for "SplitView" anywhere. Genuinely new (§10). |
| Docking | **Yes, real, persisted** | `shellLayoutStore.ts` (`ENTERPRISE_NAVIGATION.md` §9) | Collapse/pin/auto-hide/resize for left/right/bottom docks, the one genuinely persistent (`localStorage`) layout state in the app. |
| Floating panels | **Absent** | — | Positioned in `ENTERPRISE_NAVIGATION.md` §13 as a designed, narrowly-scoped escape hatch from the Dock; this document (§11) defines its drag/dismiss/z-order behavior. |
| Notifications | **Yes, real** | `notificationStore.ts` (`ENTERPRISE_NAVIGATION.md` §12) | Toast (6s auto-dismiss) vs. persistent panel, real store, socket-based push degrading to poll by default. |
| Command palette | **Yes, real — see `ENTERPRISE_NAVIGATION.md` §5, §8** | — | Not re-described here; this document only covers how palette *results* behave once acted on (§13). |
| Smart suggestions | **Yes, real** | `ai-os-chrome/smartSuggestions.ts` | Real, contextual, path-aware suggestion generation feeding both the AI Dock and Enterprise City's advisor hints. |
| History / Undo / Redo | **Absent — confirmed zero hits** | — | No `undo`, `redo`, or history-stack pattern exists anywhere in `src/web`. The only "undo-adjacent" feature is tab "reopen last closed" (one level, not a stack). Genuinely new (§14–§15). |
| Favorites / Pinning | **Yes, real, but duplicated and unpersisted** | Two separate systems — see `ENTERPRISE_NAVIGATION.md` §0 | Navigation-scoped and workspace-scoped favorites managers are distinct instances; tab pinning is a third, independent pin concept. None persist across reload. |
| Workspace memory / persistent layouts | **Partially real** | `shellLayoutStore.ts` (real, persisted) vs. `layoutManager.ts` (simulated, in-memory `Map`, never touches `localStorage`) | Dock chrome remembers itself; dashboard/widget layout does not survive a refresh today, despite `layoutManager.features()` literally listing `"drag_drop"`/`"docking"` as **metadata strings**, not implemented capabilities. |
| Collaboration / presence / cursor sharing / voice collaboration / AI collaboration | **Absent — confirmed, except "Collaborative AI"** | — | No live multi-user presence, cursor tracking, or real-time shared editing exists. "Collaborative AI" (`platform-builder/collaborative-ai/`) coordinates AI *agent* teams, not human co-presence — unrelated to this document's collaboration sections (§16–§20), which are entirely new design territory. |

---

## 1. Drag & drop

**One drag-and-drop model for the whole platform**, generalized from the one real implementation
(tab reordering, §0) rather than a second, different pattern per surface:

- **Draggable elements** always show a clear grab affordance on hover (cursor change + subtle lift,
  reusing the existing hover-lift token from `ENTERPRISE_DESIGN_SYSTEM.md` §5) before a drag starts —
  a user should never discover draggability by accident mid-drag.
- **Drop targets highlight during drag** with a token-driven outline (reusing the focus-ring color,
  `ENTERPRISE_DESIGN_SYSTEM.md` §8), never a bespoke drop-zone color invented per feature.
- **Two concrete generalization targets, both currently absent:**
  1. **Dashboard/widget drag-and-drop** (§8) — replacing `WidgetCard`'s Move/Resize buttons with real
     drag-to-reposition and drag-handle resize, the same interaction tabs already have for reordering.
  2. **Storyboard/asset reordering** in `AI_PRODUCTION_STUDIO.md`'s video/podcast composition tools —
     reordering scenes or audio segments is structurally identical to reordering tabs.
- **Keyboard equivalent required for every drag interaction** (accessibility, per `ENTERPRISE_DESIGN_
  SYSTEM.md` §9's accessible-by-default principle) — arrow-key reorder as a fallback to pointer drag,
  not an afterthought; this is already how the widget Move buttons work today (§0), and that keyboard
  path must survive once real drag-and-drop is added, not be replaced by it.

## 2. Selection

**Absent today (§0) — designed as a single, shared selection model:**

- **Click selects one item and clears any other selection** — the baseline, unambiguous interaction.
- **Selection state is visually distinct from focus/hover** (`ENTERPRISE_CITY.md` §17's inspection-vs-
  action distinction generalizes here too: hover/focus previews, click selects, selection persists
  until explicitly changed) — a selected row/card/tile gets a persistent highlight token (primary-tinted
  border, per the card system's existing `is-success`-style state-border pattern in
  `ENTERPRISE_DESIGN_SYSTEM.md` §13), not just a transient hover state.
- **Selection is scoped to its container** (a table's selection doesn't leak into a sibling widget's
  selection) — never a single global "selected item" variable shared across the app.

## 3. Multi-selection

**Absent today (§0) — designed, generalizing standard OS conventions rather than inventing new ones:**

- **`Shift+click`** selects a contiguous range from the last-selected item.
- **`Ctrl/Cmd+click`** toggles one additional item in/out of the selection without clearing the rest.
- **A selection count and a contextual action bar appear** once 2+ items are selected (bulk
  approve/reject/delete/export) — reusing the toolbar chrome pattern already defined in
  `ENTERPRISE_DESIGN_SYSTEM.md` §12 (`.eds-toolbar`), not a new bar style.
- **`Escape` clears selection** — consistent with `ENTERPRISE_NAVIGATION.md` §16's "Escape closes
  everything" rule, generalized to selection state as one more thing Escape resets.
- **Checkboxes are the touch/accessibility equivalent** of `Shift`/`Ctrl`+click — a data grid or asset
  list should show a checkbox column when multi-select is available so touch and screen-reader users
  have a first-class path to the same capability, not a keyboard-only feature.

## 4. Context actions

Distinct from Context *Menus* (§5): a context action is any action available directly on a hovered/
focused item without opening a menu — e.g. a widget's visible Move/Resize buttons (§0), a tab's pin
icon, an approval card's inline Approve/Reject buttons (`AI_PRODUCTION_STUDIO.md` §25). **Rule:**
context actions are for the 1–3 most common operations on an item; anything beyond that belongs in the
item's context menu (§5), never bolted on as a fourth/fifth inline icon that crowds the item.

## 5. Right-click menus (context menus)

**Real in exactly one place today (§0); designed as a shared primitive everywhere else** — directly
following `ENTERPRISE_NAVIGATION.md` §15's identification of this gap:

- **One `ContextMenu` component**, not a bespoke implementation per surface — the tab bar's existing
  menu (activate/pin/duplicate/close/reopen) is the reference shape every future adopter should match:
  positioned at the cursor, dismissed on click-outside or `Escape`, a simple vertical action list.
- **Long-press is the touch equivalent** (`ENTERPRISE_NAVIGATION.md` §17) — same menu component, two
  trigger paths.
- **Right-click never replaces a left-click's primary action** — it only ever adds secondary actions;
  an item's main behavior must remain fully reachable via left-click/Enter alone.

## 6. Hover behaviors

Fully real and token-driven already (`ENTERPRISE_DESIGN_SYSTEM.md` §5, §13) — restated here for
completeness of this document's coverage, not redesigned: hover-lift (`translateY(-1px)`) on
interactive cards/buttons, border/shadow transitions on `--eds-motion-fast`, table row background
tint on hover. **Rule for this document's new surfaces:** every new interactive element (drag handles,
selection checkboxes, context-menu triggers, floating-panel headers) reuses these existing hover tokens
— no new hover treatment is introduced anywhere in this document.

## 7. Glass effects

Fully real and scope-limited already (`ENTERPRISE_DESIGN_SYSTEM.md` §6) — restated for this document's
window/panel/floating-surface sections specifically: **Dock chrome (§9 in `ENTERPRISE_NAVIGATION.md`)
uses the reserved chrome-glass treatment; floating panels (§11) and split-view panes (§10) do not** —
they are content surfaces, not fixed navigation chrome, and stay on solid `--eds-surface` per the
same rule that keeps City buildings and Workspace cards solid. Applying glass to a floating panel would
directly violate the "glass is chrome, not content" rule this whole platform already follows.

## 8. Widget behavior

Real catalog (14 kinds), real `move/resize/configure` API (§0) — currently exposed only via
increment buttons. Designed extension: **the same API, driven by drag-and-drop** (§1) — a widget
gains a visible drag handle (header area) and resize handles (corner/edge), both calling the exact
same `widgetManager.move`/`resize` functions that already exist, just with continuous pointer input
instead of fixed-increment button clicks. **No new widget data model is required** — this is a pure
interaction-layer upgrade over real, existing widget state.

## 9. Window management

Not a literal multi-window desktop manager (§0) — designed as the relationship between the three real
"window-like" primitives the platform already has, made explicit and consistent:

| Primitive | Persistence | Use |
|---|---|---|
| **Tab** (§0, real) | Session-scoped (open tabs list) | The default container for sustained work — one workspace module per tab |
| **Dock panel** (`ENTERPRISE_NAVIGATION.md` §9, real, persisted) | `localStorage`-persisted | Fixed, positional, always-available chrome (navigation, activity/notifications) |
| **Floating panel** (`ENTERPRISE_NAVIGATION.md` §13, designed) | Session-scoped, dismissed on navigation away unless explicitly kept | Follow-along context that shouldn't require leaving the current tab |

**Rule:** a new "I need a window-like surface" feature request should map to exactly one of these
three — never a fourth window primitive invented per feature. Floating panels are always dismissible
and never persist across a full page reload (that's what Tabs and Dock are for); Dock panels are the
only surface that persists across a reload at all.

## 10. Split views

**Absent today — genuinely new (§0).** Designed narrowly:

- **A split view is two Tabs (§0) shown side by side**, not a new content model — any tab-hosted
  module can be placed in either pane; this reuses the existing Tab data model completely.
- **Split is a per-workspace-session layout choice**, toggled from the tab bar (a "split right" action
  on a tab's context menu, §5) — splitting does not create a new persistent layout type distinct from
  the workspace's existing layout state (§12).
- **Resizing the split divider** uses the same drag interaction and handle affordance as widget/dock
  resize (§1, §8, `ENTERPRISE_NAVIGATION.md` §9) — one resize interaction pattern, reused a third time.
- **Mobile/touch collapses a split view back to single-pane tabs** (per `ENTERPRISE_DESIGN_SYSTEM.md`
  §18's mobile-first responsive rules) — split view is a laptop/desktop-viewport feature, not
  force-fit onto small screens.

## 11. Floating panels

Positioned in `ENTERPRISE_NAVIGATION.md` §13; this section defines the interaction detail:

- **Drag by header only** (never by clicking anywhere in the body) — consistent with how a user
  expects any floating surface to behave, and avoids accidental drags while interacting with content.
- **No resize** — a floating panel has a fixed, content-appropriate size (per §13's "small,
  dismissible" scope); if content needs resizing, it belongs in a Tab or Split View (§10) instead,
  which is a signal the feature has outgrown the floating-panel use case.
- **Z-order:** the most recently interacted-with floating panel comes to front; multiple floating
  panels never fully overlap without a visible stacking offset, so one is never invisibly hidden behind
  another.
- **Dismiss:** `Escape` (topmost panel only, not all at once — distinct from Dock/overlay dismiss
  behavior, since a user may have a floating panel open *while* using a modal elsewhere), an explicit
  close control, or clicking its own header's collapse affordance (mirroring the AI Dock's existing
  collapse-to-pill pattern, `ENTERPRISE_NAVIGATION.md` §0).

## 12. Notifications (interaction detail)

Real store and real toast/panel split (`ENTERPRISE_NAVIGATION.md` §12) — the interaction rules this
document adds: **a toast is never draggable or resizable** (it is transient by design, §12 there); the
**Notifications Panel supports the same multi-selection model as §3** (bulk mark-read/dismiss); and a
notification tied to a background job (e.g. a Production Studio render completing,
`AI_PRODUCTION_STUDIO.md` §23) is clickable straight into the relevant Approval card or asset —
notifications are always an action shortcut, never a dead-end read receipt.

## 13. Command palette (result interaction)

Full palette behavior is `ENTERPRISE_NAVIGATION.md` §5/§8 — this document adds only how a **result**
behaves once acted on: selecting a navigation result closes the palette and transitions per
`ENTERPRISE_NAVIGATION.md` §21's page-transition rules; selecting an action result (Quick Action) runs
it in place and shows a toast (§12) confirming completion, without necessarily navigating away — a
command and a navigation are visually distinct outcomes, so a user always knows which one just happened.

## 14. History

**Absent as a general concept today** (tab "reopen last closed" is the only precedent, §0) — designed
as a real, cross-surface history model:

- **Every significant user action** (navigation, create, edit, delete, approve/reject in
  `AI_PRODUCTION_STUDIO.md`'s workflows, layout changes once persisted, §12 there) appends to one
  **session history log** — not a per-feature ad hoc history like today's tab-only "reopen closed."
- **History is inspectable**, not just traversable — a history panel (reusing the Notifications
  Panel's list chrome, §12) shows recent actions with timestamps, distinct from the Navigation
  History already covered in `ENTERPRISE_NAVIGATION.md` §0 (page visits) — this is *action* history,
  a superset.
- **History is the substrate Undo/Redo (§15) is built on** — without a real history log, undo/redo has
  nothing to operate over; this section is a prerequisite for the next one, not a parallel feature.

## 15. Undo / Redo

**Entirely absent today (§0) — the single largest genuinely-new interaction gap this document
identifies.** Designed scope, deliberately conservative:

- **Undo operates on the History log (§14)**, one step at a time, standard `Ctrl/Cmd+Z` /
  `Ctrl/Cmd+Shift+Z` (or `Ctrl+Y`) shortcuts, consistent with `ENTERPRISE_NAVIGATION.md` §16's global
  shortcut philosophy — these become two more entries in that document's canonical shortcut table
  once implemented.
- **Not every action is undoable** — destructive actions with external side effects (a real Publishing
  Center post going live, `AI_PRODUCTION_STUDIO.md` §26) are **excluded from Undo by design**; undo
  applies to reversible platform-internal state (layout changes, draft edits, local reordering), never
  to an action that already reached an external system. This mirrors the platform's existing "no silent
  bypass" governance instinct (`AI_PRODUCTION_STUDIO.md` §2/§25) — undo must never become a way to
  quietly un-publish something that already went out.
- **A visible toast confirms every undo/redo** ("Undid: moved widget," §12's confirmation pattern),
  so a user always knows what state they just reverted to, rather than a silent stack pop.

## 16. Favorites

Real but duplicated/unpersisted today (`ENTERPRISE_NAVIGATION.md` §0) — the design fix belongs to
that document (§22, TD-41); this document's addition is the **interaction**, once unified: a single
favorite/star toggle affordance (icon button, consistent placement — top-right of a card, next to a
tab's pin icon) that works identically whether favoriting a page, a City building, a saved search, or
an Asset Versioning entry (`AI_PRODUCTION_STUDIO.md` §17) — one favoriting gesture, reused everywhere,
not a different star-icon convention per feature.

## 17. Pinning

Real for tabs today (§0, `WorkspaceTabBar`) — designed generalization: pinning means "exempt from
automatic cleanup/collapse," applied consistently — a pinned tab can't be closed; a pinned Dock panel
disables auto-hide (`ENTERPRISE_NAVIGATION.md` §9, already real); a pinned widget (designed extension)
would be exempt from a future "auto-arrange" layout feature. **Pin and Favorite are different
concepts and must stay visually distinct** — favoriting is about *findability* (shows up in a
favorites list), pinning is about *persistence* (won't be auto-removed/collapsed) — conflating the two
icons would blur two genuinely different user intentions.

## 18. Workspace memory

The umbrella concept covering everything a returning user should not have to re-configure: dock layout
(real, persisted, §9 `ENTERPRISE_NAVIGATION.md`), favorites/pins (real but unpersisted, §16–§17),
dashboard/widget layout (simulated only, §0), open tabs and split-view arrangement (§9–§10, session-
scoped only today), and command/navigation history (§14, new). **Design principle: workspace memory
should have one persistence tier, not per-feature ad hoc storage** — see §19.

## 19. Persistent layouts

**The concrete fix this document specifies for §18's biggest real gap:** dashboard/widget layout is
currently simulated (an in-memory `Map`, §0) despite `layoutManager.features()` already *claiming*
`"drag_drop"`/`"docking"`/`"responsive_grid"` as capabilities. This document's design requirement:
**every layout-affecting interaction in this document (§1 widget drag/resize, §9 window arrangement,
§10 split views) should persist through the same mechanism `shellLayoutStore` already uses for Dock
layout** (`localStorage` today, a real backend preference store at enterprise scale) — not a second,
parallel persistence approach invented per layout type. One persistence tier, applied to dock layout
today and widget/split/tab layout as this document's interactions are built out.

---

## 20. Collaboration

**Entirely absent today (§0) — genuinely new product territory**, designed with the same discipline
this whole document applies elsewhere: reuse the platform's existing real-time transport
(`socket.io` wiring already present per `ENTERPRISE_NAVIGATION.md` §0, currently used for
notifications/live-data refresh) rather than inventing a second real-time channel.

- **Scope:** shared visibility and light co-editing on platform surfaces that benefit from it most —
  Approval Workflow review (`AI_PRODUCTION_STUDIO.md` §25), Workflow Builder composition
  (`AI_PRODUCTION_STUDIO.md` §21), and Enterprise City exploration during a briefing (`ENTERPRISE_
  CITY.md` §6's AI-agent-as-transit-marker precedent extends naturally to "here's where my colleague
  is looking too").
- **Not full simultaneous multi-cursor document editing** (a Google-Docs-style OT/CRDT text-editing
  engine) — that is a materially larger, different system than this platform's existing architecture
  supports today, and is explicitly out of scope for this design; collaboration here means shared
  *presence and light interaction awareness*, not concurrent character-level co-editing.

## 21. Live presence

- **Who else is here, and where.** A small presence indicator (avatar stack, reusing the existing
  Avatar token treatment from `ENTERPRISE_DESIGN_SYSTEM.md` §2's card-anatomy conventions) shows which
  colleagues are currently viewing the same page/asset/City building.
- **Presence is ambient, never blocking** — seeing someone else present never locks a surface or
  prevents interaction; it is informational, following the same "AI is an advisor, never gatekeeping"
  principle (`ENTERPRISE_DESIGN_SYSTEM.md` §16) applied to human co-presence instead of AI.
- **Presence signals travel over the existing socket transport** (§20) as a new, lightweight event
  type alongside the real `workspace:refresh`/`notifications:new` events already flowing through it —
  not a new connection or protocol.

## 22. Cursor sharing

- **Scoped to spatial/canvas surfaces only** (Enterprise City, a future Workflow Builder canvas,
  `AI_PRODUCTION_STUDIO.md` §21) — not to ordinary text-heavy pages, where a shared cursor adds noise
  without value.
- **A named, colored cursor marker**, following the same "recognizable without reading" instinct that
  governs City building silhouettes (`ENTERPRISE_CITY.md` §4) — color-coded per user, label on hover,
  never a persistent floating name tag cluttering the view.
- **Cursor position is presence data, not an editing lock** — seeing a colleague's cursor over a City
  building never prevents another user from also focusing/clicking that same building (§0, §2's
  selection-is-scoped-per-container rule extends here: shared presence doesn't create shared,
  exclusive selection).

## 23. Voice collaboration

- **Not a new video/audio-calling product** — this platform does not need to build a Zoom competitor.
  Voice collaboration here means **lightweight, contextual voice notes/annotations** attached to a
  specific asset or approval card (`AI_PRODUCTION_STUDIO.md` §25) — "here's 15 seconds of why I
  requested this edit" — rather than live synchronous calling.
- **Reuses the Voice Studio's synthesis/storage substrate** (`AI_PRODUCTION_STUDIO.md` §6, §17) for
  recording/storing the annotation as a versioned, lineage-tracked asset — a voice comment is a small
  audio asset like any other, not a separate real-time media system.
- **Always optional and asynchronous** — a reviewer can always leave a text comment instead; voice is
  an additive input method, never a required one (accessibility, consistent with §19's "text always
  works" instinct throughout the AI-interaction sections of this platform).

## 24. AI collaboration

The one collaboration category with real substrate to build on today:

- **The AI Advisor already participates in the workspace as a contextual collaborator**
  (`ai-os-chrome/AiOsExperienceChrome.tsx`, `ENTERPRISE_NAVIGATION.md` §20) — "AI collaboration" in
  this document means extending that existing relationship, not introducing a new AI persona.
- **AI as a co-reviewer, not just a suggester.** In Approval Workflow (`AI_PRODUCTION_STUDIO.md` §25),
  the Brand Compliance Agent's validation is a form of AI collaboration already designed there — this
  document's contribution is the **interaction surface**: an AI's compliance flag appears inline on the
  approval card exactly where a human co-reviewer's comment would (§20's shared presence pattern,
  applied to an AI participant instead of a human one) — same visual slot, same interaction, different
  participant type.
- **AI never has silent write access.** Every AI collaboration action (a suggestion, a flag, a
  generated draft) is visible and attributed, following the same Observation/Why/Action/Impact
  transparency rule as every other AI surface in this platform (`ENTERPRISE_DESIGN_SYSTEM.md` §16) —
  an AI "collaborator" never edits something and leaves no trace of having done so.

---

## 25. Synthesis — one unified interaction language

The rules that recur across every section above, stated once as the whole document's summary:

1. **One pattern, many adopters** — drag-and-drop (§1), context menus (§5), resize handles (§8, §10),
   and the favorite/pin toggle (§16–§17) are each defined once and reused everywhere they're needed,
   never reinvented per feature the way the platform's tab bar currently is the *only* place several
   of these patterns exist for real (§0).
2. **Hover previews, click acts, selection persists** — the one interaction-model rule this document
   inherits directly from `ENTERPRISE_CITY.md` §17 and applies to every surface, not just the City.
3. **Transient chrome never blocks work; persistent chrome remembers itself** — toasts and floating
   panels are dismissible and non-blocking (§11–§12); Dock and (once fixed, §19) layout/favorites
   persist across sessions. Nothing in between is acceptable — a feature is either clearly transient or
   clearly persistent, never ambiguously both.
4. **Governance never has an interaction shortcut around it** — undo excludes externally-published
   actions (§15); AI collaboration is always visible and attributed (§24); this is the same
   `ai_never_publishes_alone`/no-silent-bypass discipline from `AI_PRODUCTION_STUDIO.md` §2 restated as
   an interaction-design rule, not just a backend one.
5. **Text always works.** Voice (§23), controller (`ENTERPRISE_NAVIGATION.md` §18), and AI-suggested
   actions (§24) are all additive input methods layered over interactions that remain fully usable by
   keyboard and pointer alone.

---

## Related documents

- `ENTERPRISE_NAVIGATION.md` — how a user moves *between* surfaces; this document covers acting
  *within* one. §9, §13, §15 of that document and §9–§11 here describe the same window/panel
  primitives from two complementary angles.
- `ENTERPRISE_DESIGN_SYSTEM.md` — the token/motion/glass canon every interaction in this document
  reuses rather than reinvents (§6–§7 restate the two most load-bearing rules).
- `ENTERPRISE_CITY.md` — the origin of this document's hover-previews/click-acts interaction rule
  (§25.2), and the primary current use case for cursor sharing (§22) and controller navigation.
- `AI_PRODUCTION_STUDIO.md` — the primary consumer of history/undo (§14–§15, asset edit history),
  multi-selection (§3, bulk asset actions), and AI collaboration (§24, Brand Compliance Agent review).
- `TECH_DEBT.md` — the persistent-layout gap (§19) and the duplicated/unpersisted favorites (§16) are
  tracked there (TD-41, shared with `ENTERPRISE_NAVIGATION.md`'s findings); add a new item for the
  absence of any general-purpose drag-and-drop/context-menu/undo primitive in `src/web` at next
  registry update.
- `CLAUDE.md` — "use feature modules," "reuse services before creating new ones," and "prefer extension
  over replacement" are the direct justification for this entire document's "one pattern, many
  adopters" synthesis (§25.1).
