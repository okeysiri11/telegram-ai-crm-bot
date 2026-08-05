/**
 * Enterprise City ↔ EBN runtime bridge — Sprint 29.0.
 * Buildings can load Business Profile · Status · Trust · Relationship Count · HQ.
 */

import {
  businessNetworkEngine,
  EBN_HOME_PROFILE_ID,
  EBN_PARTNER_PROFILE_ID,
  type CityBusinessFacade,
} from "@/runtime/businessNetwork";
import type { CityBuildingId } from "./cityCatalog";

/** Building id → business profile id (runtime map, no graphics). */
export const CITY_EBN_PROFILE_MAP: Partial<Record<CityBuildingId, string>> = {
  hub: EBN_HOME_PROFILE_ID,
  business_network: EBN_HOME_PROFILE_ID,
  marketplace: EBN_PARTNER_PROFILE_ID,
};

export function loadCityBusinessFacade(buildingId: CityBuildingId): CityBusinessFacade | null {
  businessNetworkEngine.startup();
  const profileId = CITY_EBN_PROFILE_MAP[buildingId];
  if (!profileId) return null;
  return businessNetworkEngine.cityFacade(profileId);
}
