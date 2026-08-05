# City Buildings

**Sprint:** 30.4  
**Files:** `cityCatalog.ts` · `buildingOps.ts`

## Contract

Every building has:

| Field | Source |
|-------|--------|
| Name | `CityBuilding.label` / `short` |
| Icon | catalog `icon` + silhouette CSS |
| Status | live `CityLiveStatus` + visual state |
| Health | `buildingOps` + `healthFromLiveTone` |
| Owner | `BuildingOpsMeta.owner` |
| Active users | `BuildingOpsMeta.activeUsers` |
| Quick actions | `BuildingOpsMeta.quickActions` |
| Route | existing module path only |

## Ops metadata

`buildingOps(id)` returns Russian-friendly owner, description, health, users, and quick actions for the inspector and Owner Mode.

## Live status tones → health

| Live tone / load | Health |
|------------------|--------|
| `alert` | critical |
| High notifications/tasks | warning |
| Idle + empty | maintenance |
| Otherwise | online |

## Seed

`CITY_STATUS_SEED` must include every `CITY_BUILDINGS` id.

See [CITY_RENDERER.md](./CITY_RENDERER.md), [OWNER_CITY_MODE.md](./OWNER_CITY_MODE.md).
