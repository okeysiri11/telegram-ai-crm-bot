/**
 * Asset registry + CRUD — Sprint 29.3.
 */

import type {
  AssetCategory,
  AssetLifecyclePhase,
  AssetLocation,
  AssetOwnership,
  AssetPermissionScope,
  AssetStatus,
  AssetType,
  EnterpriseAsset,
  AssetProfile,
} from "./assetTypes";

const byId = new Map<string, EnterpriseAsset>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export function categoryForType(type: AssetType): AssetCategory {
  switch (type) {
    case "building":
    case "headquarters":
    case "office":
    case "warehouse":
      return "real_estate";
    case "vehicle":
    case "drone":
      return "fleet";
    case "construction_equipment":
    case "machine":
      return "equipment";
    case "computer":
    case "server":
      return "it";
    case "brand":
    case "license":
    case "certificate":
      return "compliance";
    case "ai_model":
    case "knowledge_asset":
      return "intellectual";
    case "document":
    case "digital_product":
      return "digital";
    default:
      return "other";
  }
}

function lifecycle(phase: AssetLifecyclePhase, actorId?: string, detail?: string) {
  const at = new Date().toISOString();
  return {
    phase,
    since: at,
    history: [{ phase, at, actorId, detail }],
  };
}

export const assetRegistry = {
  clear() {
    byId.clear();
  },

  create(input: {
    type: AssetType;
    profile: AssetProfile;
    ownership: AssetOwnership;
    location?: Partial<AssetLocation>;
    permissions?: AssetPermissionScope[];
    metadata?: Record<string, unknown>;
    status?: AssetStatus;
    id?: string;
  }): EnterpriseAsset {
    const now = new Date().toISOString();
    const asset: EnterpriseAsset = {
      id: input.id || uid("ast"),
      type: input.type,
      category: categoryForType(input.type),
      status: input.status || "draft",
      profile: input.profile,
      ownership: input.ownership,
      location: {
        kind: input.location?.kind || "virtual",
        buildingId: input.location?.buildingId,
        districtId: input.location?.districtId,
        warehouseId: input.location?.warehouseId,
        vehicleId: input.location?.vehicleId,
        citizenId: input.location?.citizenId,
        x: input.location?.x,
        y: input.location?.y,
        label: input.location?.label,
      },
      lifecycle: lifecycle("created"),
      permissions: input.permissions || ["owner", "company"],
      metadata: input.metadata || {},
      available: true,
      createdAt: now,
      updatedAt: now,
    };
    byId.set(asset.id, asset);
    return asset;
  },

  get(id: string) {
    return byId.get(id);
  },

  list() {
    return [...byId.values()];
  },

  update(
    id: string,
    patch: Partial<
      Pick<
        EnterpriseAsset,
        | "profile"
        | "status"
        | "ownership"
        | "location"
        | "permissions"
        | "metadata"
        | "assignedCitizenId"
        | "assignedCompanyId"
        | "available"
      >
    >,
  ) {
    const cur = byId.get(id);
    if (!cur) return null;
    const next: EnterpriseAsset = {
      ...cur,
      ...patch,
      profile: patch.profile ? { ...cur.profile, ...patch.profile } : cur.profile,
      ownership: patch.ownership ? { ...cur.ownership, ...patch.ownership } : cur.ownership,
      location: patch.location ? { ...cur.location, ...patch.location } : cur.location,
      metadata: patch.metadata ? { ...cur.metadata, ...patch.metadata } : cur.metadata,
      updatedAt: new Date().toISOString(),
    };
    byId.set(id, next);
    return next;
  },

  setLifecycle(id: string, phase: AssetLifecyclePhase, actorId?: string, detail?: string) {
    const cur = byId.get(id);
    if (!cur) return null;
    const at = new Date().toISOString();
    const statusMap: Partial<Record<AssetLifecyclePhase, AssetStatus>> = {
      created: "draft",
      registered: "registered",
      assigned: "assigned",
      in_use: "in_use",
      maintenance: "maintenance",
      archived: "archived",
      disposed: "disposed",
      transferred: "transferred",
    };
    const next: EnterpriseAsset = {
      ...cur,
      status: statusMap[phase] || cur.status,
      available: !["maintenance", "archived", "disposed"].includes(phase),
      lifecycle: {
        phase,
        since: at,
        history: [{ phase, at, actorId, detail }, ...cur.lifecycle.history].slice(0, 80),
      },
      updatedAt: at,
    };
    byId.set(id, next);
    return next;
  },

  remove(id: string) {
    return byId.delete(id);
  },
};
