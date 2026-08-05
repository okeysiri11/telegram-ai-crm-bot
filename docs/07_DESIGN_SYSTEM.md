# 07 — Design System

**Chapter of the Master Product Bible.** This chapter is a pointer chapter: the full token
implementation lives in `ENTERPRISE_DESIGN_SYSTEM.md` (18 sections, exact values) and the real source
of truth is `src/web/design-system/`. This chapter states *what exists and where*, so a developer or AI
agent knows which document to open for an exact value, rather than guessing or re-deriving one.

## What "Design System" means here, precisely

Per `06_DESIGN_LANGUAGE.md`'s distinction: the Design System is the **token layer** — colors,
typography, spacing, elevation, motion durations, grid, iconography — implemented as real TypeScript
constants and CSS custom properties, not just written guidance. Version lineage: EDS `9.4.0`
(architecture, unchanged since Sprint 26.2), layered with EDL `1.0` and MDL `1.0` (the *language*,
`06_DESIGN_LANGUAGE.md`).

## Where every token category lives

| Category | Implementation | Full reference |
|---|---|---|
| Colors | `src/web/design-system/{tokens,colors}/index.ts`, `styles/tokens.css` | `ENTERPRISE_DESIGN_SYSTEM.md` §4 |
| Typography | `src/web/design-system/typography/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §3 |
| Spacing | `src/web/design-system/spacing/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §12 |
| Elevation & shadows | `src/web/design-system/elevation/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §7–§8 |
| Motion durations/easing | `src/web/design-system/animation/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §9 |
| Iconography | `src/web/design-system/icons/index.tsx` | `ENTERPRISE_DESIGN_SYSTEM.md` §10 |
| Layout grids | `src/web/design-system/grid/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §11 |
| Responsive breakpoints | `src/web/design-system/responsive/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §18 |
| Themes | `src/web/design-system/theme/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §4 |
| Accessibility flags | `src/web/design-system/accessibility/index.ts` | `06_DESIGN_LANGUAGE.md` |
| Component catalog | `src/web/design-system/catalog/index.ts` | `ENTERPRISE_DESIGN_SYSTEM.md` §13 |

## The four facts worth stating without opening the full document

1. **Brand color is teal** — `#0f6a5a` light / `#3ecfad` dark / `#125b4a` corporate — paired with a navy
   secondary (`#1f3a5f`). This pairing, not any single hex, is the brand.
2. **One shared duration/easing scale** — instant (80ms) → fast (120ms) → normal (200ms) → slow (320ms)
   → settle (400ms) — every animated element in the platform picks the nearest of these five, never a
   sixth invented value.
3. **The card is the primary content unit** everywhere — dashboards, workspace, identity surfaces are all
   built from one `.eds-card` recipe with a shared state vocabulary (loading/empty/success/interactive/
   raised), not a bespoke panel per feature.
4. **Style Presets do not exist yet.** Only three named themes (light/dark/corporate) plus a single
   custom brand-override object exist today (`AI_PRODUCTION_STUDIO.md` §0's finding) — the Production
   Studio's Style Presets module (§18 there) is the first place this platform designs a real preset
   gallery, and it is vision, not shipped.

## Governance

`ENTERPRISE_DESIGN_SYSTEM.md`'s own rule: **extend tokens, never hardcode.** No raw hex/rem value in
feature code when a token exists — a hardcoded value in a PR is treated as a defect, the same severity
class as a hardcoded brand color was when EP-02 swept `#0f766e` out of shell CSS. This is
`02_PRODUCT_PHILOSOPHY.md` principle 2 (extension over replacement) applied at the smallest possible
scale — a single color value.

## Related chapters

`06_DESIGN_LANGUAGE.md` (how these tokens are composed into recognizable patterns),
`04_ENTERPRISE_CITY.md` (inherits this system unmodified in both 2D and vision 3D modes),
`05_AI_PRODUCTION.md` (the UI Generator module has the single hardest dependency on this system of
any feature in the platform, per its own §11 constraint).
