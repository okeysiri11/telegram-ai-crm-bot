# 06 — Design Language

**Chapter of the Master Product Bible.** This chapter covers the platform's **visual and motion
language** — the recipes and principles that make screens feel like one product. It is distinct from
`07_DESIGN_SYSTEM.md`, which covers the underlying **token implementation** those recipes are built
from. Full detail: `ENTERPRISE_DESIGN_SYSTEM.md`, `docs/EP_02_ENTERPRISE_DESIGN_LANGUAGE.md` (EDL 1.0),
`docs/EP_03_MOTION_DESIGN_LANGUAGE.md` (MDL 1.0).

## Language vs. system, precisely

- The **Design System** (`07_DESIGN_SYSTEM.md`) is the token layer: exact hex values, exact spacing
  scale, exact duration numbers — the vocabulary.
- The **Design Language** (this chapter) is how that vocabulary is composed into recognizable sentences:
  card anatomy, identity-surface radius sharing, the motion principles that decide *which* token applies
  *when*. A designer or AI agent should reach for this chapter to answer "what should this feel like,"
  and for `07_DESIGN_SYSTEM.md` to answer "what's the exact value."

## Visual language

- **Brand test:** teal primary + IBM Plex + quiet uppercase section labels + soft executive cards =
  recognizable without a logo (`ENTERPRISE_DESIGN_SYSTEM.md` §1, EDL's own stated mission).
- **Identity surfaces share a signature.** Morning Brief, AI Concierge dock, Control Tower, Enterprise
  City hero panels, and Marketplace/Builder strips all share one radius/border language
  (`--edl-identity-radius`/`--edl-identity-border`) — this is the concrete mechanism that makes disparate
  executive surfaces read as one family, not a coincidence of similar styling.
- **Shape scales with weight in the hierarchy.** Small controls get small radii; cards get medium radii;
  hero/identity surfaces get the largest radius — bigger surfaces get bigger radii, consistently
  (`ENTERPRISE_DESIGN_SYSTEM.md` §2).
- **Glass is chrome, never content.** Backdrop-blur is reserved for header/sidebar chrome; cards, tables,
  and dialogs stay on solid surfaces (`ENTERPRISE_DESIGN_SYSTEM.md` §6.1) — this rule is violated in
  exactly one accepted, contained exception (`platform_console`'s pervasive dark-glass theme, §6.2),
  named explicitly so it is never mistaken for platform-wide guidance.

## Motion language

Mission, stated once and never restated with a different meaning anywhere in the platform: **motion
explains state, it does not entertain** (`docs/EP_03_MOTION_DESIGN_LANGUAGE.md`).

1. **Purposeful** — motion answers "what changed?" or "what can I do?"
2. **Calm** — short durations, no bounce, no endless decorative loops.
3. **Fast** — micro-interactions ≤120ms, page enter ≤320ms, settle ≤400ms.
4. **Shared timing** — one duration/easing scale for the whole product, never invented per component.
5. **Reduce Motion first** — an accessibility constraint applied from the start, not retrofitted.

The full duration/easing token table lives in `07_DESIGN_SYSTEM.md` §9 — this chapter states the
*rule* that governs which token gets used where (`ENTERPRISE_DESIGN_SYSTEM.md` §5.2's pattern table,
§5.3's surface map), and the **forbidden list** every future feature is checked against: no bounce, no
full-page spinners as primary chrome, no parallax/autoplay carousels, no continuous motion on static
text, nothing blocking interaction past 400ms, no "attraction mode" idle animation anywhere
(`ENTERPRISE_DESIGN_SYSTEM.md` §5.4). Enterprise City's "meaningful-only" motion (`ENTERPRISE_CITY.md`
§19) and Workspace's hover/press conventions (`WORKSPACE_INTERACTIONS.md` §6) are this same rule applied
to two different surfaces, not two different rules.

## Enterprise UX principles

- **Executive-first composition.** Dashboard leads with a ~10-second comprehension target
  (`EP_01_EXECUTIVE_EXPERIENCE.md`); dense data is available but never leads.
- **Observation → Why → Action → Impact** is the one structure every recommendation surface uses,
  everywhere in the platform (`08_AI_PERSONALITY.md`) — a UX pattern, not just a copy-writing rule.
- **Hover previews, click acts, selection persists** — the one interaction-model rule that recurs from
  Enterprise City to Workspace to (designed) every future surface (`WORKSPACE_INTERACTIONS.md` §25.2).

## Accessibility

WCAG AA is the stated standard (`ENTERPRISE_DESIGN_SYSTEM.md` §1, principle 9), not an aspirational
target: keyboard navigation, screen-reader support, focus management, high-contrast mode, and reduced
motion are first-class states checked at design time, not accommodations added after a feature ships.
Every animated class in the platform has a defined reduced-motion behavior (`ENTERPRISE_DESIGN_SYSTEM.md`
§5.5); every drag interaction is required to have a keyboard equivalent
(`WORKSPACE_INTERACTIONS.md` §1); every voice/controller navigation input is additive over a fully
keyboard/pointer-usable base (`ENTERPRISE_NAVIGATION.md` §17–§19).

## Related chapters

`07_DESIGN_SYSTEM.md` (the token implementation this language is built from), `04_ENTERPRISE_CITY.md`
and `05_AI_PRODUCTION.md` (both inherit this language rather than defining their own),
`08_AI_PERSONALITY.md` (the language's application to AI-specific surfaces).
