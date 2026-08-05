# Enterprise City Visualization Runtime

**Sprint:** 29.5  
**Package:** `src/web/src/runtime/cityVisualization`  
**Constraint:** Runtime bridge only — no graphics, no fake simulation.

## Purpose

Single source of truth that future 2D/3D Enterprise City clients consume. All visual state is derived from live Spatial · Life · Citizens · EBN · Assets · Workflow · Automation.

## Core

| Component | Role |
|-----------|------|
| CityVisualizationRuntime | Facade · scene rebuild · query API |
| CityScene | Snapshot of visual entities + layers |
| VisualizationLayer / Registry | Layer enablement + LOD mins |
| VisualizationState | Revision · visibility · LOD |
| CityRendererBridge | Adapter contract for future renderers |
| RuntimeDataProvider | Pulls real runtime modules |
| PerformanceLayer | Scene/spatial cache · visibility · LOD · incremental updates |

## Visual state

- **Buildings:** status · occupancy · business activity · open/closed · meetings · projects · companies · branding hooks  
- **Districts:** activity · population · density · construction · traffic · economic · runtime status  
- **Citizens:** building · workspace · company · presence · role · activity · remote · avatar ref  
- **Assets:** vehicles · equipment · warehouses · HQ · construction · drones · status · availability  

## Events

`BuildingUpdated` · `CitizenMoved` · `MeetingStarted` · `MeetingFinished` · `AssetMoved` · `CompanyUpdated` · `DistrictUpdated` · `WorkflowExecuted` · `SceneRebuilt` · `VisibilityChanged`

EventBus: `city_visualization_update` (+ `city_update`).

## UI / API

- UI: `/city-visualization`
- REST: `/api/enterprise-city-viz/v1`
- Bridge: `enterprise-city/cityVisualizationBridge.ts`
