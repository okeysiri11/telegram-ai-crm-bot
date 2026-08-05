# Design Token Standard

**Status:** permanent standard. Documentation only — no source code was modified to produce this
document. This is a **governance and compliance** document, not a values reference — every color/
spacing/typography/motion value is defined once in `ENTERPRISE_DESIGN_SYSTEM.md` and linked here, never
restated. This document's job is the *rule* ("tokens are the only legal source of a visual value") and
the *audit* (where that rule is currently bypassed in real code). Governed by
`DESIGN_SYSTEM_GOVERNANCE.md`.

## 1. The one rule

**Every color, spacing, typography, motion, and icon value in the platform traces back to exactly one
token definition.** No feature area defines its own color, invents its own spacing value, or reaches
for a raw utility class where a component-level token already exists. This is
`ENTERPRISE_DESIGN_SYSTEM.md` §2's existing rule ("extend tokens, never hardcode") — this document adds
the audit that rule was missing.

## 2. Color system — governance, not a repeat of the palette

Full palette: `ENTERPRISE_DESIGN_SYSTEM.md` §4. Governance findings from the audit behind
`DESIGN_SYSTEM_GOVERNANCE.md`:

- **Raw token-variable utility classes bypass component-level styling.** All twelve Strip components
  (`COMPONENT_LIBRARY_STANDARD.md` §2.1) write their link color as
  `className="eds-type-small text-[var(--eds-primary)]"` directly, rather than using a `Button`/`Link`
  component that already encodes this relationship. **This is technically still "using the token"** (no
  hardcoded hex value is present) but it bypasses the component layer the token system is meant to be
  consumed through — the standard is: reach for a styled component first, a raw token-variable utility
  class only when no component fits, never as the default.
- **`ews-glass` used outside its chrome scope** (`DESIGN_SYSTEM_GOVERNANCE.md` §2.1) is a token-*system*
  violation, not just a component one — it applies a background/border/shadow combination intended for
  fixed navigation chrome onto content surfaces, which will visually drift the moment the chrome token
  values change for an unrelated reason (e.g., a future Day/Night mode adjustment,
  `ENTERPRISE_CITY_ARCHITECTURE.md` §17) and silently affects five content surfaces that were never
  supposed to be coupled to chrome styling.
- **No hardcoded hex values were found** in the audited feature folders — a genuine compliance success
  worth stating, since it means the color-token discipline itself (as opposed to which component
  consumes it) is holding.

## 3. Typography

No violations found in the audited scope — every audited feature file uses the real type-scale classes
(`eds-type-small`, `eds-type-caption`, etc., `ENTERPRISE_DESIGN_SYSTEM.md` §3). Standard: continue
requiring every new text element to pick from the existing scale; a new font-size value is a defect the
same way a new hex color is.

## 4. Spacing

No violations found in the audited scope. Standard, restated for completeness: layout spacing comes from
the existing scale and contextual tokens (`ENTERPRISE_DESIGN_SYSTEM.md` §12) — no one-off rem values.

## 5. Icons — governance summary (full detail: `UI_NAMING_CONVENTIONS.md` §4)

Two icon systems currently exist (canonical `iconLibrary` + the parallel `ShellIcons.tsx`), plus raw
Unicode glyphs used as icons in four files. **Token-level standard:** an icon is not a free-floating
visual choice — it is a token the same way a color is, meaning it should be selectable from exactly one
governed set, sized from exactly one scale (`ENTERPRISE_DESIGN_SYSTEM.md` §10's sm/md/lg tokens), and
never a raw glyph chosen for convenience in the moment. The remediation path is `UI_NAMING_
CONVENTIONS.md` §4's; this section exists so "icons are tokens too" is stated explicitly rather than
implied.

## 6. Motion & animation

Full duration/easing table: `ENTERPRISE_DESIGN_SYSTEM.md` §9, motion principles: §5. Governance
findings:

- **No violations found in the audited scope** — every feature file checked uses `edm-*`/`eds-anim-*`
  classes or the shared duration tokens rather than inventing a new timing value. This is a genuine
  compliance success across Desktop, City, and Production Center specifically — none of the real-time-
  feeling surfaces (Runtime Engine ticks, Strip badge updates, window open/close) introduced a bespoke
  animation timeline.
- **One thing worth flagging for future vigilance, not a current violation:** the frontend Runtime
  Engine's 12-second tick (`ENTERPRISE_AI_OS.md` §6) and the Live Dashboard's 15-second poll
  (`DASHBOARD.md`) are two different, real, independently-chosen cadences for "how often does this
  feel live" — neither is a *motion* token violation (they're polling intervals, not animation
  durations), but as more "live" surfaces are added, a governed polling-cadence scale (analogous to the
  motion duration scale) may become worth defining, the same way five different Strip class names
  eventually became worth consolidating. Flagged here as a forward-looking observation, not a current
  defect.

## 7. Compliance checklist (for any new component, cross-referenced from `UX_GUIDELINES.md`)

- [ ] No raw hex/rem/duration value anywhere in the new component.
- [ ] Color/spacing/typography/motion reached through a styled component first, a raw token-variable
      utility class only when no component fits (§2).
- [ ] `ews-glass` (or any chrome-scoped class) used only on header/sidebar/window-chrome elements, never
      content (§2).
- [ ] Icons selected from the canonical `iconLibrary`, never `ShellIcons.tsx` or a raw glyph, unless a
      written, reasoned exception exists (§5, `UI_NAMING_CONVENTIONS.md` §4).
- [ ] Any new CSS class name matches the *component* it styles, not the *feature* that happens to use it
      first (`UI_NAMING_CONVENTIONS.md` §3).

## Related documents

`DESIGN_SYSTEM_GOVERNANCE.md` (the charter this standard enforces), `ENTERPRISE_DESIGN_SYSTEM.md`
(every token value referenced by number in this document), `COMPONENT_LIBRARY_STANDARD.md` §2 (the
component-level remediation for §2/§5's findings), `UI_NAMING_CONVENTIONS.md` §3–§4 (naming detail for
the class/icon findings here), `UX_GUIDELINES.md` (the pre-ship checklist §7 extends).
