# EP-03 — Motion Design Language (MDL)

**Phase:** Enterprise Product Excellence  
**Scope:** Motion & microinteractions — perception only  
**Date:** 2026-07-27  
**Depends on:** EP-01 · EP-02 · Enterprise Design Language 1.0  
**MDL version:** `1.0` (`MOTION_DESIGN_LANGUAGE`)  
**Styles:** `src/web/design-system/styles/motion.css`  
**GA baseline:** MDL 1.0 is the motion standard for Enterprise Platform v1.0 GA (EP-08).

## Mission

Каждое действие пользователя сопровождается понятной, плавной и **функциональной** анимацией. Движение объясняет состояние — не развлекает.

## Architecture compliance

- No Engine / Runtime / AI Core / Store / architecture changes
- CSS recipes + existing class hooks on composition surfaces
- Extends EDS motion tokens; aligns legacy `eds-anim-*` presets to MDL easing

---

## 1. Principles

1. **Purposeful** — motion answers “what changed?” or “what can I do?”
2. **Calm** — short durations; no bounce, no endless decorative loops on content
3. **Fast** — micro ≤ 120ms; page enter ≤ 320ms; settle ≤ 400ms
4. **Shared timing** — one duration / easing scale for the whole product
5. **Reduce Motion first** — `prefers-reduced-motion` and `data-reduced-motion="true"` disable motion, keep layout

---

## 2. Duration & easing

| Token | Value | Use |
|-------|-------|-----|
| `--eds-motion-instant` | 80ms | Press feedback, palette highlight |
| `--eds-motion-fast` | 120ms | Hover, border, control focus |
| `--eds-motion-normal` | 200ms | Cards, lists, dialogs |
| `--eds-motion-slow` | 320ms | Page enter, Morning Brief |
| `--eds-motion-settle` | 400ms | Status flash, partial update |
| `--eds-stagger` | 40ms | List / column cascade |
| `--eds-ease` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Default |
| `--eds-ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Enter |
| `--eds-ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exit (rare) |
| `--eds-ease-emphasized` | `cubic-bezier(0.2, 0, 0, 1)` | Emphasis |

---

## 3. Patterns (allowed)

| Pattern | Class | Scenario |
|---------|-------|----------|
| Page enter | `.edm-page` | Route content (FullLayout keyed by path) |
| Soft enter | `.edm-page-soft` | City / secondary shells |
| Stagger | `.edm-stagger` | Brief columns, KPI grid, suggestions |
| Card enter / refresh | `.edm-card-enter` / `.edm-card-refresh` | Snapshot, data refresh |
| Expand / collapse | `.edm-card-expand` / `.edm-card-collapse` | Ops strips |
| Skeleton | `.edm-skeleton` | Loading placeholders |
| Stream | `.edm-stream-bar` | Analyzing / streaming |
| Refreshing | `.edm-refreshing` | Soft overlay while refetch |
| Partial / background | `.edm-partial-update` / `.edm-bg-update` | Live deltas |
| AI live / analyzing | `.edm-ai-live` / `.edm-ai-analyzing` | Concierge dock |
| AI suggest | `.edm-ai-suggest` | Recommendation rows |
| AI done | `.edm-ai-done` | Collapse / success |
| KPI | `.edm-kpi` | Tabular values + tick |
| Overlay / drawer | `.edm-overlay-panel` / drawer CSS | Modal, palette, auth |
| Toast / notify | `.edm-toast` / `.edm-notify-enter` | Feedback |
| Palette item | `.edm-palette-item` | Command / search rows |
| Press | `.edm-press` / button active | Microinteraction |

Legacy aliases: `eds-anim-fade|slide|scale|page` remapped to MDL keyframes.

---

## 4. Forbidden effects

- Bounce / springy overshoot on enterprise surfaces
- Full-page spin loaders as primary chrome
- Parallax scroll / autoplay carousels
- Continuous motion on static text blocks
- Motion that blocks interaction > 400ms
- City “attraction” loops (buildings flying, constant zoom pulse)
- Confetti / novelty animations

---

## 5. Surface map

| Scenario | Motion |
|----------|--------|
| Login | Auth panel `.edm-overlay-panel` |
| Dashboard / Morning Brief | Brief enter + staggered columns / KPIs |
| Mission Control / Control Tower | Page enter + card hover/press |
| Enterprise City | Soft enter; focus breathe; status flash; AI dot pulse only |
| AI Concierge | Live breathe / analyzing stream / staggered suggestions |
| Marketplace / Builder / Twin | Shared page enter + card recipes |
| Settings / Profile | Control focus + page enter |
| Search / Command Palette | Overlay scale + palette item press |

---

## 6. Accessibility

- `@media (prefers-reduced-motion: reduce)` zeros durations and disables animations / transforms
- `[data-reduced-motion="true"]` mirrors for app preference
- Loading / streaming remain **visible** without motion (static bars / opacity)
- Focus rings stay; only transition duration collapses

---

## 7. Premium Motion Improvements (≥35)

1. `motion.css` MDL layer  
2. Instant / settle duration tokens  
3. Ease-out / ease-in / emphasized curves  
4. Stagger token 40ms  
5. Page enter keyed by `pathname` in FullLayout  
6. Soft page enter for City  
7. Remap `eds-anim-*` to MDL keyframes  
8. Card press scale  
9. Card interactive lift token  
10. Card expand for ops strips  
11. Button hover lift + press  
12. Control focus transition  
13. Skeleton shimmer recipe  
14. Stream bar for AI / loading  
15. Refreshing overlay helper  
16. Partial update flash  
17. Background update pulse (restricted)  
18. Concierge live breathe  
19. Concierge analyzing state  
20. Suggestion stagger + slide  
21. Suggestion hover nudge  
22. Pulse busy state  
23. Snapshot card enter  
24. Collapsed dock done cue  
25. Morning Brief enter  
26. Brief meta stagger  
27. Brief grid stagger  
28. Brief card press  
29. KPI stagger grid  
30. KPI tabular + value class  
31. KPI hover shadow via motion tokens  
32. City building status flash  
33. City focus breathe (meaningful only)  
34. City plane transform ease  
35. Dialog overlay fade  
36. Drawer panel slide  
37. Modal overlay panel scale  
38. Auth shell overlay panel  
39. Command palette overlay + item press  
40. Universal palette overlay  
41. Toast MDL enter  
42. Notification enter  
43. ExperienceState streaming / refreshing kinds  
44. WidgetLoading stream bar  
45. Success done scale  
46. `animationEngine` MDL presets + forbidden list  
47. `MOTION_DESIGN_LANGUAGE` export  
48. Reduce-motion coverage for new recipes  

---

## 8. Scores (self-assessment)

| Metric | After EP-02 | After EP-03 |
|--------|-------------|-------------|
| Executive Experience | 8.8 | **8.9** |
| AI Experience | 8.3 | **8.7** |
| UX | 8.3 | **8.5** |
| Visual Excellence | 8.9 | **9.0** |
| Motion | 8.0 | **8.9** |
| Navigation | 8.2 | **8.4** |
| Performance | 8.0 | **8.0** |
| Enterprise Quality Index | 8.8 | **9.0** |
| Production Readiness | 8.3 | **8.4** |

---

## 9. Recommendations for EP-04

1. Sound design language (optional soft cues) aligned to MDL durations — or skip if silent enterprise preference  
2. Focus-order / keyboard choreography pass (motion-free)  
3. Command Palette result grouping with stagger caps (max 6)  
4. Chart value transitions (number tween) behind Reduce Motion  
5. Screenshot QA: Concierge analyzing + City focus + Brief stagger with Reduce Motion on/off  
6. Document motion do/don’t in Builder Academy snippet  

## Files

| Path | Role |
|------|------|
| `src/web/design-system/styles/motion.css` | MDL recipes |
| `src/web/design-system/animation/index.ts` | Preset registry |
| `src/web/src/layouts/FullLayout.tsx` | Route page enter |
| `src/web/src/ai-os-chrome/AiOsExperienceChrome.tsx` | Concierge motion |
| `src/web/src/dashboard/ExecutiveMorningBrief.tsx` | Brief stagger |
| `src/web/src/ui/ExperienceStates.tsx` | Loading family |
| `docs/EP_03_MOTION_DESIGN_LANGUAGE.md` | This spec |
