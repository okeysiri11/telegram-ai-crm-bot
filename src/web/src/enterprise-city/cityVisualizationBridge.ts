/**
 * Enterprise City ↔ Visualization Runtime bridge — Sprint 29.5.
 */

import {
  cityVisualizationRuntime,
  type BuildingVisualState,
  type VisibleCityQuery,
  type CityScene,
} from "@/runtime/cityVisualization";
import type { CityBuildingId, CityDistrictId } from "./cityCatalog";

export function loadCityVisualizationScene(): CityScene {
  cityVisualizationRuntime.startup();
  return cityVisualizationRuntime.scene();
}

export function loadVisibleCityQuery(): VisibleCityQuery {
  cityVisualizationRuntime.startup();
  return cityVisualizationRuntime.visibleQuery();
}

export function loadBuildingVisualState(buildingId: CityBuildingId): BuildingVisualState | undefined {
  cityVisualizationRuntime.startup();
  return cityVisualizationRuntime.buildingState(buildingId);
}

export function loadDistrictVisualActivity(districtId: CityDistrictId) {
  cityVisualizationRuntime.startup();
  return cityVisualizationRuntime.districtState(districtId);
}
