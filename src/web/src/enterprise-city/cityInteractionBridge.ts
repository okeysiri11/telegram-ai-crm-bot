/**
 * Enterprise City ↔ Interaction Runtime bridge — Sprint 29.6.
 */

import { interactionRuntime, type InteractionTarget, type SelectionState } from "@/runtime/interactionRuntime";
import type { CityBuildingId } from "./cityCatalog";

export function loadInteractionCatalog(): InteractionTarget[] {
  interactionRuntime.startup();
  return interactionRuntime.catalog();
}

export function selectCityBuilding(buildingId: CityBuildingId): InteractionTarget | null {
  interactionRuntime.startup();
  return interactionRuntime.select("building", buildingId);
}

export function openCityBuilding(buildingId: CityBuildingId) {
  interactionRuntime.startup();
  return interactionRuntime.open("building", buildingId);
}

export function loadSelectionState(): SelectionState {
  interactionRuntime.startup();
  return interactionRuntime.selection();
}

export function searchCityObjects(query: string) {
  interactionRuntime.startup();
  return interactionRuntime.search(query);
}
