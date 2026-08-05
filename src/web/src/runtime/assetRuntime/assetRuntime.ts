/**
 * Enterprise Asset Runtime Engine — Sprint 29.3.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { lifeEngine } from "@/runtime/lifeEngine";
import { ASSET_RUNTIME_VERSION } from "./assetTypes";
import type {
  AssetLifecyclePhase,
  AssetLocation,
  AssetOwnership,
  AssetType,
  CityAssetQuery,
  EnterpriseAsset,
} from "./assetTypes";
import { assetRegistry } from "./assetRegistry";
import { assetOwnershipService } from "./assetOwnershipService";
import { assetLocationService } from "./assetLocationService";
import { assetEvents, publishAssetEvent } from "./assetEvents";
import { assetPermissions } from "./assetPermissions";
import { seedAssets } from "./assetSeed";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "asset_open",
    action: "open_asset_runtime",
    label: "Open Asset Runtime",
    kind: "navigate",
    keywords: ["asset", "inventory", "fleet", "ownership"],
    route: "/assets",
    permission: "*",
  });
  commandRuntime.register({
    id: "asset_assign",
    action: "assign_asset",
    label: "Assign Asset",
    kind: "system",
    keywords: ["asset", "assign"],
    permission: "*",
    handler: async (_ctx, args) => {
      const assetId = String(args.assetId || "ast_van_1");
      const citizenId = String(args.citizenId || EDC_CITIZEN_OWNER);
      const res = assetRuntime.assign(assetId, { citizenId });
      return { ok: res.ok, message: assetId, error: "error" in res ? res.error : undefined };
    },
  });
}

export const assetRuntime = {
  version: ASSET_RUNTIME_VERSION,

  startup() {
    if (booted) {
      return this.stats();
    }
    commandRuntime.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    lifeEngine.startup();
    seedAssets();
    // Align seeded vehicles with Life Engine fleet when present
    for (const v of lifeEngine.vehicles.list()) {
      const existing = assetRegistry.list().find((a) => a.metadata.lifeVehicleId === v.id);
      if (!existing) {
        const a = assetRegistry.create({
          type: "vehicle",
          profile: { name: v.label, tags: ["fleet", "life"] },
          ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
          location: {
            kind: "building",
            buildingId: v.fromBuildingId || v.toBuildingId || "hub",
            vehicleId: v.id,
          },
          metadata: { lifeVehicleId: v.id },
          status: "registered",
        });
        assetRegistry.setLifecycle(a.id, "registered");
        publishAssetEvent("AssetCreated", a.id, { source: "life_vehicle" });
      }
    }
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "asset_runtime", ready: true, version: ASSET_RUNTIME_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  create(input: Parameters<typeof assetRegistry.create>[0]): EnterpriseAsset {
    if (!booted) this.startup();
    const asset = assetRegistry.create(input);
    publishAssetEvent("AssetCreated", asset.id, { type: asset.type });
    return asset;
  },

  register(assetId: string, actorId?: string) {
    if (!booted) this.startup();
    const a = assetRegistry.setLifecycle(assetId, "registered", actorId);
    if (a) publishAssetEvent("AssetRegistered", assetId);
    return a;
  },

  update(id: string, patch: Parameters<typeof assetRegistry.update>[1]) {
    if (!booted) this.startup();
    const a = assetRegistry.update(id, patch);
    if (a) publishAssetEvent("AssetUpdated", id);
    return a;
  },

  get(id: string) {
    if (!booted) this.startup();
    return assetRegistry.get(id);
  },

  list(filter?: { type?: AssetType; buildingId?: string; companyId?: string; available?: boolean }) {
    if (!booted) this.startup();
    let items = assetRegistry.list();
    if (filter?.type) items = items.filter((a) => a.type === filter.type);
    if (filter?.buildingId) items = items.filter((a) => a.location.buildingId === filter.buildingId);
    if (filter?.companyId) items = assetLocationService.byCompany(filter.companyId);
    if (filter?.available !== undefined) items = items.filter((a) => a.available === filter.available);
    return items;
  },

  assign(assetId: string, input: { citizenId?: string; companyId?: string; actorId?: string }) {
    if (!booted) this.startup();
    const asset = assetRegistry.get(assetId);
    const scopes = asset
      ? assetPermissions.scopesForActor({
          asset,
          citizenId: input.actorId || input.citizenId,
          companyId: input.companyId,
          isAdmin: true,
        })
      : undefined;
    return assetOwnershipService.assign({ ...input, assetId, actorScopes: scopes });
  },

  transfer(assetId: string, to: AssetOwnership, actorId?: string, reason?: string) {
    if (!booted) this.startup();
    const asset = assetRegistry.get(assetId);
    const scopes = asset
      ? assetPermissions.scopesForActor({ asset, citizenId: actorId, isAdmin: true })
      : undefined;
    return assetOwnershipService.transfer({ assetId, to, actorId, reason, actorScopes: scopes });
  },

  move(assetId: string, location: AssetLocation, actorId?: string) {
    if (!booted) this.startup();
    return assetLocationService.move(assetId, location, actorId);
  },

  setLifecycle(assetId: string, phase: AssetLifecyclePhase, actorId?: string, detail?: string) {
    if (!booted) this.startup();
    const a = assetRegistry.setLifecycle(assetId, phase, actorId, detail);
    if (!a) return null;
    if (phase === "maintenance") publishAssetEvent("AssetMaintained", assetId, { detail });
    if (phase === "archived") publishAssetEvent("AssetArchived", assetId);
    if (phase === "disposed") publishAssetEvent("AssetRetired", assetId);
    if (phase === "in_use") publishAssetEvent("AssetUpdated", assetId, { phase });
    return a;
  },

  maintain(assetId: string, detail?: string) {
    return this.setLifecycle(assetId, "maintenance", undefined, detail);
  },

  archive(assetId: string) {
    return this.setLifecycle(assetId, "archived");
  },

  dispose(assetId: string) {
    return this.setLifecycle(assetId, "disposed");
  },

  /** City Runtime API */
  cityQuery(): CityAssetQuery {
    if (!booted) this.startup();
    const assets = assetRegistry.list();
    const byBuilding: Record<string, EnterpriseAsset[]> = {};
    const byCompany: Record<string, EnterpriseAsset[]> = {};
    const byCitizen: Record<string, EnterpriseAsset[]> = {};
    const byDistrict: Record<string, EnterpriseAsset[]> = {};
    for (const a of assets) {
      if (a.location.buildingId) {
        (byBuilding[a.location.buildingId] ||= []).push(a);
      }
      if (a.location.districtId) {
        (byDistrict[a.location.districtId] ||= []).push(a);
      }
      const companyId = a.ownership.companyId || a.assignedCompanyId;
      if (companyId) (byCompany[companyId] ||= []).push(a);
      const citizenIds = new Set<string>();
      if (a.ownership.citizenId) citizenIds.add(a.ownership.citizenId);
      if (a.assignedCitizenId) citizenIds.add(a.assignedCitizenId);
      if (a.location.citizenId) citizenIds.add(a.location.citizenId);
      for (const cid of citizenIds) (byCitizen[cid] ||= []).push(a);
    }
    return {
      byBuilding,
      byCompany,
      byCitizen,
      byDistrict,
      totals: {
        assets: assets.length,
        available: assets.filter((a) => a.available).length,
        inUse: assets.filter((a) => a.status === "in_use").length,
        maintenance: assets.filter((a) => a.status === "maintenance").length,
      },
    };
  },

  assetsByBuilding(buildingId: string) {
    if (!booted) this.startup();
    return assetLocationService.byBuilding(buildingId);
  },

  assetsByCompany(companyId: string) {
    if (!booted) this.startup();
    return assetLocationService.byCompany(companyId);
  },

  assetsByCitizen(citizenId: string) {
    if (!booted) this.startup();
    return assetLocationService.byCitizen(citizenId);
  },

  assetsByDistrict(districtId: string) {
    if (!booted) this.startup();
    return assetLocationService.byDistrict(districtId);
  },

  permissions: assetPermissions,
  events: assetEvents,
  ownership: assetOwnershipService,

  stats() {
    if (!booted) this.startup();
    const assets = assetRegistry.list();
    return {
      version: ASSET_RUNTIME_VERSION,
      assets: assets.length,
      available: assets.filter((a) => a.available).length,
      inUse: assets.filter((a) => a.status === "in_use").length,
      maintenance: assets.filter((a) => a.status === "maintenance").length,
      transfers: assetOwnershipService.transfers(200).length,
      types: new Set(assets.map((a) => a.type)).size,
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    return {
      version: ASSET_RUNTIME_VERSION,
      assets: assetRegistry.list(),
      transfers: assetOwnershipService.transfers(20),
      events: assetEvents.list(30),
      city: this.cityQuery(),
      stats: this.stats(),
    };
  },

  __resetForTests() {
    assetRegistry.clear();
    assetOwnershipService.clear();
    assetEvents.clear();
    booted = false;
  },
};
