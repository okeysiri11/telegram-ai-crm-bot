# Visual System

**Sprint:** 31.1 (web Visual Polish track)  
**Tokens:** `src/web/design-system/styles/tokens.css`, `edl.css`, `motion.css`  
**City chrome:** `src/web/src/index.css` (`.ec-*`)

## Principles

1. **Enterprise dark theme** — EDS surfaces, primary accents, muted helpers  
2. **One typography scale** — `eds-type-h1` … `eds-type-caption`  
3. **Unified spacing** — dashboard grids (`eds-grid--dashboard`), glass headers (`ews-glass`)  
4. **Motion with purpose** — `edm-page`, `edm-page-soft`, skeletons (`edm-skeleton`); respect `prefers-reduced-motion`  
5. **No placeholder graphics** — City preview links to live `/city`; studios use loading skeletons, not “скоро” fake maps

## City visual language

- Building states: online / warning / critical / maintenance (`.ec-online-dot`, `.ec-state-*`)
- Focused data flow: `.ec-link-line.is-flowing`
- Select pulse: `.ec-building.is-focused`
- Mini-map dots mirror live visual state

## Studio polish

- AI Studio / Production Studio: Russian chrome, skeleton loaders, runtime monitors
- Role dashboards: shared `RoleDashboardPolish` (health bars, activity, notifications, AI tips, quick actions)

## Related

- `EP_02_ENTERPRISE_DESIGN_LANGUAGE.md`, `EP_03_MOTION_DESIGN_LANGUAGE.md`
- `UI_GUIDELINES.md`, `SPRINT_31_1_RESULT.md`
