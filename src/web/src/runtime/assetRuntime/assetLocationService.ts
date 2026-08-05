/**
 * Asset location tracking — Sprint 29.3.
 */

import type { AssetLocation, EnterpriseAsset } from "./assetTypes";
import { assetRegistry } from "./assetRegistry";
import { publishAssetEvent } from "./assetEvents";

export const assetLocationService = {
  move(assetId: string, location: AssetLocation, actorId?: string) {
    const cur = assetRegistry.get(assetId);
    if (!cur) return null;
    const next = assetRegistry.update(assetId, { location });
    publishAssetEvent("AssetMoved", assetId, {
      from: cur.location,
      to: location,
      actorId,
    });
    return next;
  },

  byBuilding(buildingId: string): EnterpriseAsset[] {
    return assetRegistry.list().filter((a) => a.location.buildingId === buildingId);
  },

  byDistrict(districtId: string): EnterpriseAsset[] {
    return assetRegistry.list().filter((a) => a.location.districtId === districtId);
  },

  byCitizen(citizenId: string): EnterpriseAsset[] {
    return assetRegistry
      .list()
      .filter(
        (a) =>
          a.location.citizenId === citizenId ||
          a.assignedCitizenId === citizenId ||
          a.ownership.citizenId === citizenId,
      );
  },

  byCompany(companyId: string): EnterpriseAsset[] {
    return assetRegistry
      .list()
      .filter(
        (a) =>
          a.ownership.companyId === companyId ||
          a.assignedCompanyId === companyId ||
          a.ownership.partnerCompanyId === companyId,
      );
  },

  byVehicle(vehicleId: string): EnterpriseAsset[] {
    return assetRegistry.list().filter((a) => a.location.vehicleId === vehicleId);
  },
};
