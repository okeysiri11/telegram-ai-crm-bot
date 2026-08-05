# Spatial Runtime API

**Prefix:** `/api/enterprise-spatial/v1`  
**Sprint:** 29.4  
**In-process:** `spatialRuntime` / `spatialRuntimeApi`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + Odessa twin marker |
| GET | `/inventory` | Endpoint catalog + version |
| GET | `/hierarchy` | Country → workspace hierarchy |
| GET | `/districts?kind=` | District runtime (optional kind filter) |
| GET | `/buildings` | Building entities |
| GET | `/route?from=&to=` | Route foundation (distance · travel time · path) |
| GET | `/city` | City Spatial Query aggregate |

## City Query shape

```ts
{
  buildingsByDistrict: Record<string, SpatialEntity[]>;
  companiesByBuilding: Record<string, string[]>;
  citizensByLocation: Record<string, string[]>;
  assetsByBuilding: Record<string, string[]>;
  projectsByArea: Record<string, string[]>;
  meetingsByOffice: Record<string, string[]>;
  districts: SpatialEntity[];
  stats: { entities; buildings; districts; routesCached; assignments };
}
```

## Client

```ts
import { spatialRuntimeApi, spatialRuntime } from "@/runtime/spatialRuntime";

await spatialRuntimeApi.health();
spatialRuntime.cityQuery();
spatialRuntime.route("spb_hub", "spb_developer");
```

Vite plugin serves stub JSON in local/dev; live data comes from the in-process engine.
