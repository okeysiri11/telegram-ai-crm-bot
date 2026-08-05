# City Navigation

**Sprint:** 30.4  
**Files:** `cityNavigation.ts` · `EnterpriseCityPage.tsx` · `cityInteractionBridge.ts`

## Interactions

| Action | Behavior |
|--------|----------|
| Pan | Drag map background |
| Zoom | Wheel / toolbar |
| Click | Select building, focus camera, update inspector |
| Double-click | Open module route |
| Hover | Hover effect + `hoverId` |
| Selection | Focus id + Interaction Runtime `selectCityBuilding` |
| Breadcrumbs | Город предприятия → район → здание |
| Домой | Focus Central Plaza (`returnHome`) |
| District jump | Pan to first building in district |

## Memory

- History / Recent — `localStorage`  
- Favorites — city key + `favoritesManager`  
- Viewport — `ews_city_viewport_v1`  
- Focus — city visual language focus key  

## Search

City search selects on result click; Enter opens the first hit (module navigation).

See [CITY_ENGINE.md](./CITY_ENGINE.md).
