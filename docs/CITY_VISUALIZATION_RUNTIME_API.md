# City Visualization Runtime API

**Prefix:** `/api/enterprise-city-viz/v1`  
**Sprint:** 29.5  
**In-process:** `cityVisualizationRuntime` / `cityVisualizationApi`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health |
| GET | `/inventory` | Endpoint catalog |
| GET | `/scene` | Full CityScene snapshot |
| GET | `/visible?lod=` | Visibility-filtered query |
| GET | `/buildings` | Visible buildings |
| GET | `/citizens` | Visible citizens |
| GET | `/companies` | Visible companies |
| GET | `/assets` | Visible assets |
| GET | `/activities` | Visible activities |
| GET | `/districts` | Visible districts |

## Client

```ts
import { cityVisualizationRuntime, cityVisualizationApi } from "@/runtime/cityVisualization";

cityVisualizationRuntime.startup();
const scene = cityVisualizationRuntime.scene();
const visible = cityVisualizationRuntime.visibleQuery("near");
cityRendererBridge.register({ id: "future_3d", label: "3D", onPayload: (p) => { /* consume */ } });
```

Vite plugin serves stub JSON; live data comes from the in-process engine.
