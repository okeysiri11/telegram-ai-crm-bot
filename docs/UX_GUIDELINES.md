# UX Guidelines — Practical Companion

**Status:** permanent, practical reference. Documentation only — no source code should be modified as a
result of reading this document. This is not a new specification — it is a **checklist distilled from**
`06_DESIGN_LANGUAGE.md`, `07_DESIGN_SYSTEM.md`, `ENTERPRISE_NAVIGATION.md`, `WORKSPACE_
INTERACTIONS.md`, `ENTERPRISE_CITY_BIBLE.md`, and `AI_PRODUCTION_CENTER_BIBLE.md`, meant to be read in
under five minutes by anyone (human or AI agent) about to build a new Enterprise OS surface — a Desktop
app, a City building, a Production Center studio, or any other feature. Every rule below links back to
its full source; this document adds no new rule of its own.

## Before you build anything: five questions

1. **Does this already exist somewhere?** Check `MODULES.md`, `AI_PRODUCTION_CENTER_BIBLE.md` §0,
   `ENTERPRISE_CITY_BIBLE.md` §2 before writing a new component. Real precedent for "reuse before
   create" done right: the Enterprise Desktop's window manager and the Production Center's job queue
   both extended existing systems (`platform_jobs`, the Dock/notification store) instead of duplicating
   them — match that discipline.
2. **What does this feel like, and is that already defined?** `06_DESIGN_LANGUAGE.md` — brand test,
   card anatomy, identity-surface radius sharing. Don't invent a new visual recipe if an existing card/
   dialog/drawer recipe already fits.
3. **Does this need a new window primitive?** No. `WORKSPACE_INTERACTIONS.md` §9 defines exactly three:
   Tab, Dock panel, Floating panel. A fourth is a real design decision, not a default.
4. **Does this publish, act externally, or bypass an approval gate?** If yes, it needs a human approval
   step before it can — no exception, ever (`02_PRODUCT_PHILOSOPHY.md` principle 6,
   `AI_PRODUCTION_CENTER_BIBLE.md` §4).
5. **Is this animation or motion attached to a real event?** If you can't name the specific state
   change it represents, don't build it (`06_DESIGN_LANGUAGE.md`'s motion section,
   `ENTERPRISE_CITY_ANIMATIONS.md` §0).

## Visual checklist

- [ ] No hardcoded hex/rem/duration values — every value comes from `ENTERPRISE_DESIGN_SYSTEM.md`'s
      tokens (`07_DESIGN_SYSTEM.md`).
- [ ] Glass/backdrop-blur only on fixed navigation chrome (header, sidebar, Dock) — never on content
      cards, tables, dialogs, or floating panels (`ENTERPRISE_DESIGN_SYSTEM.md` §6.1,
      `ENTERPRISE_CITY_UI_RULES.md` §4).
- [ ] New card-shaped UI uses the existing `.eds-card` recipe (header/body/actions, loading/empty/
      success/interactive/raised states) — not a bespoke panel (`ENTERPRISE_DESIGN_SYSTEM.md` §13).
- [ ] Color is never the only signal for state — pair with shape/label/text
      (`ENTERPRISE_CITY_STATES.md` §6, `ENTERPRISE_CITY_ARCHITECTURE.md` §20).
- [ ] Identity/hero surfaces share the platform's radius/border tokens, not a bespoke look
      (`06_DESIGN_LANGUAGE.md`).

## Motion checklist

- [ ] Duration picked from the five shared tokens (instant/fast/normal/slow/settle) — never a sixth
      invented value (`ENTERPRISE_DESIGN_SYSTEM.md` §9).
- [ ] No bounce, no full-page spinners as primary chrome, no parallax/autoplay, no continuous motion on
      static content, nothing blocking interaction past 400ms (`ENTERPRISE_DESIGN_SYSTEM.md` §5.4).
- [ ] Reduced-motion behavior defined *before* the animation ships, not patched in after
      (`ENTERPRISE_DESIGN_SYSTEM.md` §5.5).
- [ ] Ambient/looping motion is the exception, not the default — the AI-pulse dot is the one platform-
      wide sanctioned continuous loop; a new one needs its own justification (`ENTERPRISE_CITY_
      ANIMATIONS.md` §4).

## Navigation & interaction checklist

- [ ] New feature is reachable from the existing Command Palette / Sidebar / Dock — not a fourth
      parallel navigation system (`ENTERPRISE_NAVIGATION.md` §1, §22).
- [ ] Hover/focus previews (inspects); click/Enter acts (navigates or executes) — never blur this line
      (`ENTERPRISE_CITY_BIBLE.md` §17, `WORKSPACE_INTERACTIONS.md` §25.2).
- [ ] Every mouse/touch interaction has a keyboard equivalent (`ENTERPRISE_NAVIGATION.md` §16,
      `WORKSPACE_INTERACTIONS.md` §1).
- [ ] Right-click menus use the shared `ContextMenu` primitive once it exists — don't build a second
      bespoke one like the tab bar's original implementation (`WORKSPACE_INTERACTIONS.md` §5).
- [ ] New windowed content uses the real embed contract (`?embed=1`, honoring `WorkspaceLayout`/
      `SettingsPage`'s existing pattern) rather than a new windowing mechanism
      (`WINDOW_MANAGER.md`).
- [ ] Persisted state uses one `localStorage`/session key per surface, following `shellLayoutStore`'s
      and `desktopStore`'s real pattern — not scattered ad hoc keys (`ENTERPRISE_NAVIGATION.md` §9,
      `DESKTOP.md`).

## AI & governance checklist

- [ ] Any AI-facing copy uses the one Executive Advisor voice: calm, confident, concise, proactive,
      respectful — Observation → Why → Action → Impact (`08_AI_PERSONALITY.md`, `AI_AGENTS_BIBLE.md`
      §0).
- [ ] Any agent action is visible and attributed — no silent AI writes (`AI_AGENTS_BIBLE.md` §5).
- [ ] Any publish/external action requires a real human approval step, structurally enforced, not just
      documented (`AI_PRODUCTION_CENTER_BIBLE.md` §4).
- [ ] Confidence, if shown, is one badge (High/Likely/Explore) — never a percentage or progress bar
      (`08_AI_PERSONALITY.md`).

## Accessibility checklist

- [ ] WCAG AA is the bar, not an aspiration — verify against it, don't just declare it
      (`06_DESIGN_LANGUAGE.md`, `00_MASTER_PRODUCT_BIBLE.md` §3 gap #4).
- [ ] A spatial/visual-first feature (a map, a canvas) ships with a real, non-degraded List/text
      equivalent — never a lesser fallback bolted on afterward
      (`ENTERPRISE_CITY_ARCHITECTURE.md` §20).
- [ ] Reduced motion, keyboard navigation, and screen-reader labels are designed in from the start, not
      retrofitted (`02_PRODUCT_PHILOSOPHY.md` principle 9's "accessible by default" reading).

## Status-honesty checklist (the one this whole documentation set is built on)

- [ ] Every new feature's documentation states plainly what is real/shipped vs. what is vision/designed
      — never blur the two (`02_PRODUCT_PHILOSOPHY.md` principle 9; every "§0 grounding table" across
      this documentation set is the model to follow).
- [ ] If a UI surface exists ahead of its real backend (as the Production Center's studios currently
      do, `AI_PRODUCTION_CENTER_BIBLE.md` §0), that gap is stated explicitly in the surface's own
      documentation, not left implicit.
- [ ] "Non-goals" are written down as deliberately as goals — `WINDOW_MANAGER.md`, `MEDIA_MANAGER.md`,
      and `PRODUCTION_AUTOMATION.md` all do this well; match that discipline for any new surface.

## Related documents

`06_DESIGN_LANGUAGE.md`, `07_DESIGN_SYSTEM.md` (full detail behind the Visual/Motion checklists),
`ENTERPRISE_NAVIGATION.md`, `WORKSPACE_INTERACTIONS.md` (full detail behind the Navigation checklist),
`AI_AGENTS_BIBLE.md`, `08_AI_PERSONALITY.md` (full detail behind the AI checklist),
`AI_PRODUCTION_CENTER_BIBLE.md`, `ENTERPRISE_CITY_BIBLE.md` (worked real examples this guide draws
from), `02_PRODUCT_PHILOSOPHY.md` (the nine principles every checklist item traces back to).
