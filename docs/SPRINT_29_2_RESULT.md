# Sprint 29.2 — Enterprise Life Engine

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `29.2`  
**Constraint:** Real runtime activity only — City visualizes Life Engine data, not fake simulation.

## Implementation summary

- `src/web/src/runtime/lifeEngine/` — events, timeline, occupancy, movement, meetings, vehicles, projects, business interactions, presence bridge  
- Subscribes to `workflow_update` · `digital_citizen_update` · `business_network_update`  
- Publishes `life_engine_update` + `city_update`  
- City bridge `cityLifeBridge` + `useCityLiveStatus` occupancy tones  
- UI `/life-engine` · REST `/api/enterprise-life/v1`  

## Remaining

- Durable event store  
- Vehicle path rendering in City  
- Cross-tenant life feeds  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **245 passed** |
| build | OK |
