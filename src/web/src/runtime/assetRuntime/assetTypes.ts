/**
 * Enterprise Asset Runtime types — Sprint 29.3.
 */

export const ASSET_RUNTIME_VERSION = "29.3";
export const ASSET_PERSIST_KEY = "ews_asset_runtime_v1";
export const ASSET_API_PREFIX = "/api/enterprise-assets/v1";

export type AssetType =
  | "building"
  | "headquarters"
  | "office"
  | "warehouse"
  | "vehicle"
  | "construction_equipment"
  | "machine"
  | "computer"
  | "server"
  | "drone"
  | "document"
  | "brand"
  | "license"
  | "certificate"
  | "ai_model"
  | "knowledge_asset"
  | "digital_product";

export type AssetCategory =
  | "real_estate"
  | "fleet"
  | "equipment"
  | "it"
  | "intellectual"
  | "digital"
  | "compliance"
  | "other";

export type AssetStatus =
  | "draft"
  | "registered"
  | "assigned"
  | "in_use"
  | "maintenance"
  | "archived"
  | "disposed"
  | "transferred";

export type AssetLifecyclePhase =
  | "created"
  | "registered"
  | "assigned"
  | "in_use"
  | "maintenance"
  | "archived"
  | "disposed"
  | "transferred";

export type OwnershipKind =
  | "citizen"
  | "company"
  | "shared"
  | "department"
  | "partner"
  | "rental"
  | "lease"
  | "temporary";

export type AssetPermissionScope =
  | "owner"
  | "assignee"
  | "department"
  | "company"
  | "partner"
  | "public"
  | "enterprise_admin";

export type AssetLocationKind =
  | "building"
  | "district"
  | "warehouse"
  | "vehicle"
  | "citizen"
  | "remote"
  | "virtual";

export type AssetEventName =
  | "AssetCreated"
  | "AssetAssigned"
  | "AssetMoved"
  | "AssetTransferred"
  | "AssetMaintained"
  | "AssetArchived"
  | "AssetRetired"
  | "AssetRegistered"
  | "AssetUpdated";

export type AssetOwnership = {
  kind: OwnershipKind;
  citizenId?: string;
  companyId?: string;
  departmentId?: string;
  partnerCompanyId?: string;
  sharePct?: number;
  /** Co-owners for shared ownership */
  coOwners?: { citizenId?: string; companyId?: string; sharePct?: number }[];
  leaseEndsAt?: string;
  notes?: string;
};

export type AssetLocation = {
  kind: AssetLocationKind;
  buildingId?: string;
  districtId?: string;
  warehouseId?: string;
  vehicleId?: string;
  citizenId?: string;
  /** Enterprise City plane coords 0–100 */
  x?: number;
  y?: number;
  label?: string;
};

export type AssetLifecycle = {
  phase: AssetLifecyclePhase;
  since: string;
  history: { phase: AssetLifecyclePhase; at: string; actorId?: string; detail?: string }[];
};

export type AssetProfile = {
  name: string;
  description?: string;
  serialNumber?: string;
  sku?: string;
  manufacturer?: string;
  tags?: string[];
  valueEstimate?: number;
  currency?: string;
};

export type EnterpriseAsset = {
  id: string;
  type: AssetType;
  category: AssetCategory;
  status: AssetStatus;
  profile: AssetProfile;
  ownership: AssetOwnership;
  location: AssetLocation;
  lifecycle: AssetLifecycle;
  permissions: AssetPermissionScope[];
  metadata: Record<string, unknown>;
  assignedCitizenId?: string;
  assignedCompanyId?: string;
  available: boolean;
  createdAt: string;
  updatedAt: string;
};

export type AssetTransferRecord = {
  id: string;
  assetId: string;
  from: AssetOwnership;
  to: AssetOwnership;
  at: string;
  actorId?: string;
  reason?: string;
};

export type CityAssetQuery = {
  byBuilding: Record<string, EnterpriseAsset[]>;
  byCompany: Record<string, EnterpriseAsset[]>;
  byCitizen: Record<string, EnterpriseAsset[]>;
  byDistrict: Record<string, EnterpriseAsset[]>;
  totals: {
    assets: number;
    available: number;
    inUse: number;
    maintenance: number;
  };
};
