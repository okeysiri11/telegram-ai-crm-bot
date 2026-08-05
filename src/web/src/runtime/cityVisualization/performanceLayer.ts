/**
 * Performance layer — scene/spatial cache, visibility, LOD, incremental updates.
 * Sprint 29.5 — no graphics.
 */

import type {
  CityScene,
  IncrementalUpdate,
  LodDescriptor,
  LodTier,
  VisibleCityQuery,
  VisualizationState,
  BuildingVisualState,
  DistrictVisualState,
  CitizenVisualState,
  CompanyVisualState,
  AssetVisualState,
  ActivityVisualState,
  CityVisEventName,
  VisualizationLayerId,
} from "./cityVisualizationTypes";
import { visualizationRegistry } from "./visualizationRegistry";

const LOD_TABLE: Record<LodTier, LodDescriptor> = {
  far: {
    tier: "far",
    includeCitizens: false,
    includeAssets: false,
    includeActivities: false,
    includeBranding: false,
    maxEntities: 40,
  },
  medium: {
    tier: "medium",
    includeCitizens: false,
    includeAssets: true,
    includeActivities: false,
    includeBranding: true,
    maxEntities: 120,
  },
  near: {
    tier: "near",
    includeCitizens: true,
    includeAssets: true,
    includeActivities: true,
    includeBranding: true,
    maxEntities: 300,
  },
  detail: {
    tier: "detail",
    includeCitizens: true,
    includeAssets: true,
    includeActivities: true,
    includeBranding: true,
    maxEntities: 1000,
  },
};

let sceneCache: CityScene | null = null;
let spatialCacheKey = "";
let revision = 0;
let state: VisualizationState = {
  sceneId: "",
  revision: 0,
  dirtyLayers: [],
  visibleBuildingIds: [],
  visibleCitizenIds: [],
  visibleCompanyIds: [],
  visibleAssetIds: [],
  visibleActivityIds: [],
  visibleDistrictIds: [],
  lod: "near",
};
let lastIncremental: IncrementalUpdate | null = null;

function layerEnabled(id: VisualizationLayerId, lod: LodTier) {
  return visualizationRegistry.enabledForLod(lod).some((l) => l.id === id);
}

export const performanceLayer = {
  clear() {
    sceneCache = null;
    spatialCacheKey = "";
    revision = 0;
    lastIncremental = null;
    state = {
      sceneId: "",
      revision: 0,
      dirtyLayers: [],
      visibleBuildingIds: [],
      visibleCitizenIds: [],
      visibleCompanyIds: [],
      visibleAssetIds: [],
      visibleActivityIds: [],
      visibleDistrictIds: [],
      lod: "near",
    };
  },

  lodDescriptor(tier: LodTier = state.lod) {
    return LOD_TABLE[tier];
  },

  setLod(tier: LodTier) {
    state = { ...state, lod: tier };
    return this.lodDescriptor(tier);
  },

  setViewportHint(hint?: VisualizationState["viewportHint"]) {
    state = { ...state, viewportHint: hint };
  },

  getState() {
    return { ...state };
  },

  getSceneCache() {
    return sceneCache;
  },

  spatialCacheValid(key: string) {
    return spatialCacheKey === key && !!sceneCache;
  },

  putScene(scene: CityScene, spatialKey: string) {
    sceneCache = scene;
    spatialCacheKey = spatialKey;
    revision += 1;
    state = {
      ...state,
      sceneId: scene.id,
      revision,
      dirtyLayers: [],
    };
    return revision;
  },

  /** Visibility filtering — LOD + layer + optional viewport (plane coords via branding/district). */
  filterVisible(scene: CityScene, lod: LodTier = state.lod): VisibleCityQuery {
    const desc = LOD_TABLE[lod];
    const buildings = layerEnabled("buildings", lod)
      ? scene.buildings.slice(0, desc.maxEntities)
      : [];
    const districts = layerEnabled("districts", lod) ? scene.districts : [];
    const companies = layerEnabled("companies", lod) ? scene.companies : [];
    const assets =
      layerEnabled("assets", lod) && desc.includeAssets
        ? scene.assets.slice(0, desc.maxEntities)
        : [];
    const citizens =
      layerEnabled("citizens", lod) && desc.includeCitizens
        ? scene.citizens.slice(0, desc.maxEntities)
        : [];
    const activities =
      layerEnabled("activities", lod) && desc.includeActivities
        ? scene.activities.slice(0, Math.min(80, desc.maxEntities))
        : [];

    // Lazy: strip branding at far LOD
    const buildingsOut = desc.includeBranding
      ? buildings
      : buildings.map((b) => ({ ...b, branding: undefined }));

    state = {
      ...state,
      lod,
      revision,
      visibleBuildingIds: buildingsOut.map((b) => b.buildingId),
      visibleCitizenIds: citizens.map((c) => c.citizenId),
      visibleCompanyIds: companies.map((c) => c.companyId),
      visibleAssetIds: assets.map((a) => a.assetId),
      visibleActivityIds: activities.map((a) => a.id),
      visibleDistrictIds: districts.map((d) => d.districtId),
    };

    return {
      buildings: buildingsOut,
      citizens,
      companies,
      assets,
      activities,
      districts,
      revision,
      lod,
    };
  },

  incrementalFromDiff(
    prev: CityScene | null,
    next: CityScene,
    event?: CityVisEventName,
  ): IncrementalUpdate {
    const prevBuildings = new Map((prev?.buildings || []).map((b) => [b.buildingId, b]));
    const upsertBuildings: BuildingVisualState[] = [];
    for (const b of next.buildings) {
      const old = prevBuildings.get(b.buildingId);
      if (!old || old.status !== b.status || old.occupancy !== b.occupancy || old.meetingCount !== b.meetingCount) {
        upsertBuildings.push(b);
      }
    }

    const prevDistricts = new Map((prev?.districts || []).map((d) => [d.districtId, d]));
    const upsertDistricts: DistrictVisualState[] = [];
    for (const d of next.districts) {
      const old = prevDistricts.get(d.districtId);
      if (!old || old.activity !== d.activity || old.population !== d.population || old.runtimeStatus !== d.runtimeStatus) {
        upsertDistricts.push(d);
      }
    }

    const prevCitizens = new Map((prev?.citizens || []).map((c) => [c.citizenId, c]));
    const upsertCitizens: CitizenVisualState[] = [];
    for (const c of next.citizens) {
      const old = prevCitizens.get(c.citizenId);
      if (!old || old.buildingId !== c.buildingId || old.presence !== c.presence) {
        upsertCitizens.push(c);
      }
    }

    const prevAssets = new Map((prev?.assets || []).map((a) => [a.assetId, a]));
    const upsertAssets: AssetVisualState[] = [];
    for (const a of next.assets) {
      const old = prevAssets.get(a.assetId);
      if (!old || old.buildingId !== a.buildingId || old.status !== a.status || old.available !== a.available) {
        upsertAssets.push(a);
      }
    }

    const prevActs = new Set((prev?.activities || []).map((a) => a.id));
    const upsertActivities: ActivityVisualState[] = next.activities.filter(
      (a) => !prevActs.has(a.id) || a.status !== prev?.activities.find((x) => x.id === a.id)?.status,
    );

    revision += 1;
    const inc: IncrementalUpdate = {
      revision,
      event,
      upsertBuildings,
      upsertDistricts,
      upsertCitizens,
      upsertAssets,
      upsertActivities,
      removeIds: [],
      at: new Date().toISOString(),
    };
    lastIncremental = inc;
    state = { ...state, revision, lastEvent: event };
    return inc;
  },

  lastIncremental() {
    return lastIncremental;
  },

  cacheStats() {
    return {
      hasScene: !!sceneCache,
      spatialKey: spatialCacheKey,
      revision,
      lod: state.lod,
      visible: {
        buildings: state.visibleBuildingIds.length,
        citizens: state.visibleCitizenIds.length,
        companies: state.visibleCompanyIds.length,
        assets: state.visibleAssetIds.length,
        activities: state.visibleActivityIds.length,
        districts: state.visibleDistrictIds.length,
      },
    };
  },
};
