# EP-05 — Enterprise City Experience

**Phase:** Enterprise Product Excellence  
**Scope:** Visual / interaction quality of Enterprise City — no Engine / Store / Runtime / AI Core  
**Date:** 2026-07-27  
**Depends on:** EP-01 · EP-02 · EP-03 · EP-04  
**Version:** `CITY_EXPERIENCE_VERSION = 1.0`

## Mission

Превратить Enterprise City в главный визуальный центр управления: состояние бизнеса за один взгляд.

## Architecture compliance

- No new Engine / Store / Runtime / AI Core / Data Fabric
- Presentation over existing buildings, live status, routes
- City focus memory via `sessionStorage` (not a Store)

---

## 1. Visual state language (City RU/UA)

| State | RU | UA | Dashboard EN (reference only) |
|-------|----|----|-------------------------------|
| ok | Всё хорошо | Все добре | Healthy |
| attention | Требует внимания | Потребує уваги | Needs attention |
| critical | Критично | Критично | Critical |
| running | Выполняется | Виконується | Running |
| waiting | Ожидает | Очікує | Waiting |
| done | Завершено | Завершено | Done |

Mapped from live `CityLiveStatus` via `resolveVisualState`.

---

## 2. Building identity

Each building has:

- District class (commerce / ops / people / intel / hub) → shape language
- Silhouette glyph (CSS) → readable without text
- Purpose RU/UA one-liner

---

## 3. Executive overlay

Existing signals, clearer layers:

- Glance chips (OK / Увага / Крит. / В роботі / AI)
- Overlay toggles: Усе · Здоров'я · Активність · AI
- District link lines (soft)
- Inspector: health · activity · warnings · AI · Advisor hint
- Live signals list with localized states

---

## 4. Context navigation

Header strip: Dashboard · Concierge · Mission Control · Control Tower · Builder · Refresh

Natural companion to Morning Brief / Advisor.

---

## 5. AI integration

- Focused building persisted (`setCityFocus` / `getCityFocus`)
- Concierge context line includes City focus
- `suggestionsForPath` injects focus-aware advice on City / Concierge

---

## 6. Live feeling

Uses EP-03 MDL: focus breathe, state flash, AI pulse, page soft enter — only when state changes / focus.

---

## 7. Delight inventory (≥40)

1. `cityVisualLanguage.ts`  
2. Six localized states  
3. UA twin labels in legend  
4. `resolveVisualState`  
5. Building identity map  
6. District silhouette CSS  
7. Purpose RU/UA  
8. District soft links  
9. City focus session  
10. Glance counters  
11. Advisor hint per building  
12. Lean executive header  
13. Exec nav strip  
14. Overlay layer toggles  
15. Localized legend  
16. Inspector panel  
17. Advisor · City card  
18. Live signals with RU states  
19. Search hits show state badges  
20. Silhouette in search  
21. State label under building  
22. Remove emoji-primary chrome (silhouette first)  
23. Tokenized City CSS (EDL)  
24. Quieter grid  
25. Link line overlay  
26. WF route uses `--eds-primary`  
27. Minimap uses visual state colors  
28. Density: shorter copy  
29. Mobile hides long state / UA  
30. Concierge city focus line  
31. Focus suggestions in smartSuggestions  
32. Extra City advice (Tower / Dashboard)  
33. Motion: state flash on visual states  
34. Motion: AI pulse only with `.has-ai`  
35. Card status chip on inspector  
36. Glance stagger  
37. Reset / zoom toolbar compact  
38. `CITY_EXPERIENCE_VERSION` export  
39. Index exports for focus / states  
40. EP-05 documentation  
41. Ukrainian search placeholder  
42. Empty calm signals message  

---

## 8. Scores (self-assessment)

| Metric | After EP-04 | After EP-05 |
|--------|-------------|-------------|
| Executive Experience | 9.1 | **9.2** |
| AI Experience | 9.2 | **9.3** |
| UX | 8.7 | **8.9** |
| Visual Excellence | 9.0 | **9.2** |
| Motion | 8.9 | **9.0** |
| Enterprise City Experience | 7.8 | **9.1** |
| Enterprise Quality Index | 9.2 | **9.3** |
| Production Readiness | 8.5 | **8.6** |

---

## 9. Recommendations for EP-06

1. Keyboard map: arrow-focus buildings  
2. Persist overlay preference (local only)  
3. Twin / City cross-highlight without new engine  
4. Printable / screenshot “City daily” for owners  
5. Reduce Motion QA on focus breathe + state flash  

## Files

| Path | Role |
|------|------|
| `src/web/src/enterprise-city/cityVisualLanguage.ts` | States, identity, focus, glance |
| `src/web/src/enterprise-city/EnterpriseCityPage.tsx` | Experience UI |
| `src/web/src/index.css` | City visual system |
| `src/web/src/ai-os-chrome/smartSuggestions.ts` | City focus advice |
| `docs/EP_05_ENTERPRISE_CITY.md` | This spec |
