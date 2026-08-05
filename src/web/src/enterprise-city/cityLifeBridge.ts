/**
 * Enterprise City ↔ Life Engine runtime bridge — Sprint 29.2.
 * City requests live citizens · occupancy · meetings · vehicles · activities · AI · projects.
 */

import { lifeEngine, type CityRuntimeSnapshot, type BuildingOccupancy } from "@/runtime/lifeEngine";
import type { CityBuildingId } from "./cityCatalog";

export function loadCityLifeRuntime(): CityRuntimeSnapshot {
  lifeEngine.startup();
  return lifeEngine.cityRuntime();
}

export function loadBuildingOccupancy(buildingId: CityBuildingId): BuildingOccupancy {
  lifeEngine.startup();
  return lifeEngine.occupancy(buildingId)[0]!;
}

export function cityLifeActivityLabel(buildingId: CityBuildingId): string {
  const occ = loadBuildingOccupancy(buildingId);
  return occ?.activityLabel || "Quiet";
}
