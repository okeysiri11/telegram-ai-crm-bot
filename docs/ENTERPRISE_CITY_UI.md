# Enterprise City UI

**Sprint:** 31.1 (web Visual Polish track)  
**Canonical surface:** `src/web/src/enterprise-city/`  
**Routes:** `/city`, `/enterprise-city`

## Purpose

Interactive CSS/DOM map of the enterprise. Each building is a real platform module — not a decorative mock.

## Capabilities

| Interaction | Behavior |
|---|---|
| Hover | Lift + border accent + health tooltip |
| Click | Select · camera focus · data-flow on connected links |
| Double-click | Open module route |
| Pan / Zoom | Drag plane · wheel / toolbar |
| Mini-map | Viewport rect + jump-to-building |
| Breadcrumbs | City → District → Building |
| Status | Health · online · AI · notifications · tasks |
| Data flow | Animated `ec-link-line.is-flowing` on focused edges |

## Owner God Mode (in-city)

When role switcher is Owner, the city chrome shows live God Mode metrics (health, runtime, queues, workers, CPU/memory, API/DB/Redis) via `deriveGodModeMetrics()`, plus jump chips for buildings/districts.

## Non-goals

- No parallel WebGL city engine
- `/city-visualization` remains the runtime **inspector**, not a second map
- Do not invent buildings that lack module routes

## Related docs

- `CITY_ENGINE.md`, `OWNER_CITY_MODE.md`, `CITY_NAVIGATION.md`
- `OWNER_GOD_MODE.md` (Sprint 31.1)
- `SPRINT_31_1_RESULT.md`
