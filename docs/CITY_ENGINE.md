# City Engine

**Sprint:** 30.4 (extends 27.8)  
**Files:** `src/web/src/enterprise-city/cityEngine.ts` · `graphics/cameraEngine.ts` · `EnterpriseCityPage.tsx`

## What it is

Presentation camera + viewport controller for the interactive Enterprise City map. Not a business runtime.

## Responsibilities

| Concern | API |
|---------|-----|
| Viewport | `CityViewport { x, y, zoom }` |
| Clamp | `clampViewport`, zoom/pan bounds |
| Focus | `panToBuilding(building)` |
| Zoom | `zoomBy(viewport, delta)` |
| Pan | `applyPanDelta(viewport, dxPct, dyPct)` |
| Memory | `readViewport` / `writeViewport` → `ews_city_viewport_v1` |
| Minimap | `viewportRect(viewport)` |
| Smooth motion | Graphics `animateViewportTo` / `focusBuildingAnimated` |

## Interactions (Beta)

- Drag empty map → pan  
- Wheel → zoom  
- Toolbar +/− / Reset  
- Click building → select + camera focus  
- Double-click / «Открыть модуль» → navigate to module route  
- «Домой» → Central Plaza  
- Session restore on reload  

## Performance

- Viewport writes cached in session storage  
- Camera tweens via graphics runtime (quality / reduced-motion aware)  
- Lazy module open only after portal cue (or immediate under Low quality)

## Non-goals

- Physics / pathfinding  
- Server-side camera sync  
- Parallel WebGL city (visualization runtime stays at `/city-visualization`)

See [CITY_RENDERER.md](./CITY_RENDERER.md), [CITY_NAVIGATION.md](./CITY_NAVIGATION.md).
