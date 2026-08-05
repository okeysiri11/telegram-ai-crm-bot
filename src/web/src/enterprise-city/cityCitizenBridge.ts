/**
 * Enterprise City ↔ Digital Citizen runtime bridge — Sprint 29.1.
 */

import {
  digitalCitizenEngine,
  EDC_CITIZEN_OWNER,
  EDC_CITIZEN_DEV,
  type CityCitizenFacade,
} from "@/runtime/digitalCitizen";
import type { CityBuildingId } from "./cityCatalog";

export const CITY_CITIZEN_MAP: Partial<Record<CityBuildingId, string>> = {
  hub: EDC_CITIZEN_OWNER,
  digital_citizens: EDC_CITIZEN_OWNER,
  hr: EDC_CITIZEN_OWNER,
  ai_studio: EDC_CITIZEN_DEV,
  developer: EDC_CITIZEN_DEV,
};

export function loadCityCitizenFacade(buildingId: CityBuildingId): CityCitizenFacade | null {
  digitalCitizenEngine.startup();
  const citizenId = CITY_CITIZEN_MAP[buildingId];
  if (!citizenId) return null;
  return digitalCitizenEngine.cityFacade(citizenId);
}
