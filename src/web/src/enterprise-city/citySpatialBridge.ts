/**
 * Enterprise City ↔ Spatial Runtime bridge — Sprint 29.4.
 */

import { spatialRuntime, type CitySpatialQuery, type SpatialEntity } from "@/runtime/spatialRuntime";
import type { CityBuildingId, CityDistrictId } from "./cityCatalog";

export function loadCitySpatialQuery(): CitySpatialQuery {
  spatialRuntime.startup();
  return spatialRuntime.cityQuery();
}

export function loadSpatialBuildingsForDistrict(districtId: CityDistrictId): SpatialEntity[] {
  spatialRuntime.startup();
  return spatialRuntime.buildingsByDistrict(districtId);
}

export function loadSpatialEntityForBuilding(buildingId: CityBuildingId): SpatialEntity | undefined {
  spatialRuntime.startup();
  return spatialRuntime.list("building").find((b) => b.cityBuildingId === buildingId);
}

export function routeBetweenCityBuildings(from: CityBuildingId, to: CityBuildingId) {
  spatialRuntime.startup();
  const fromId = spatialRuntime.list("building").find((b) => b.cityBuildingId === from)?.id || `spb_${from}`;
  const toId = spatialRuntime.list("building").find((b) => b.cityBuildingId === to)?.id || `spb_${to}`;
  return spatialRuntime.route(fromId, toId);
}
