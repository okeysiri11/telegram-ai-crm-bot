/**
 * Enterprise City ↔ Asset Runtime bridge — Sprint 29.3.
 */

import { assetRuntime, type CityAssetQuery, type EnterpriseAsset } from "@/runtime/assetRuntime";
import type { CityBuildingId, CityDistrictId } from "./cityCatalog";

export function loadCityAssetQuery(): CityAssetQuery {
  assetRuntime.startup();
  return assetRuntime.cityQuery();
}

export function loadAssetsForBuilding(buildingId: CityBuildingId): EnterpriseAsset[] {
  assetRuntime.startup();
  return assetRuntime.assetsByBuilding(buildingId);
}

export function loadAssetsForDistrict(districtId: CityDistrictId): EnterpriseAsset[] {
  assetRuntime.startup();
  return assetRuntime.assetsByDistrict(districtId);
}

export function buildingAssetAvailability(buildingId: CityBuildingId): {
  total: number;
  available: number;
  inUse: number;
  maintenance: number;
} {
  const list = loadAssetsForBuilding(buildingId);
  return {
    total: list.length,
    available: list.filter((a) => a.available).length,
    inUse: list.filter((a) => a.status === "in_use").length,
    maintenance: list.filter((a) => a.status === "maintenance").length,
  };
}
