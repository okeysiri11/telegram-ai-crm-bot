# City Renderer

**Sprint:** 30.4  
**Files:** `EnterpriseCityPage.tsx` · `index.css` (`.ec-*`) · `graphics/*`

## Model

CSS/DOM renderer — single City surface at `/enterprise-city`.

| Layer | Content |
|-------|---------|
| Grid / plaza ring | Atmosphere |
| District labels | 16 districts, Russian `labelRu` |
| Street SVG | Soft links from `streetGraph()` |
| Building tiles | Status, health, users, AI dots |
| Effects | Selection, hover, district activation, portal |
| Minimap | Viewport rectangle + dots |

## Building cards

Each tile shows:

- Silhouette / icon class  
- Short name  
- Live health label (Онлайн / Предупреждение / Критично / Обслуживание)  
- Active users meta  
- Notifications / tasks badges  

## Right panel (inspector)

Selected building: name, description, owner, status, health, active users, district, recent activity, quick actions, open module.

## Caching

- Viewport session key  
- City focus session key  
- Live status seed + Mission Control merge in `useCityLiveStatus`  
- Graphics quality settings  

## Related

`CITY_ENGINE.md` · `CITY_GRAPHICS_ENGINE.md` · `CITY_RENDER_PIPELINE.md`
