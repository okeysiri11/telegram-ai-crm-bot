/**
 * Enterprise City Visualization Runtime — Sprint 29.5.
 * Single source of truth for future 2D/3D City clients (no graphics).
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { lifeEngine } from "@/runtime/lifeEngine";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import {
  CITY_VIS_VERSION,
  type CityScene,
  type CityVisEventName,
  type LodTier,
  type VisualizationLayerId,
  type VisibleCityQuery,
} from "./cityVisualizationTypes";
import { cityVisualizationEvents, publishCityVisEvent } from "./cityVisualizationEvents";
import { visualizationRegistry } from "./visualizationRegistry";
import { runtimeDataProvider } from "./runtimeDataProvider";
import { performanceLayer } from "./performanceLayer";
import { cityRendererBridge } from "./cityRendererBridge";

let booted = false;
let busUnsub: (() => void) | null = null;
let sceneSeq = 0;
let rebuilding = false;

function registerCommands() {
  commandRuntime.register({
    id: "city_viz_open",
    action: "open_city_visualization",
    label: "Open City Visualization Runtime",
    kind: "navigate",
    keywords: ["visualization", "city viz", "digital twin", "scene"],
    route: "/city-visualization",
    permission: "*",
  });
  commandRuntime.register({
    id: "city_viz_rebuild",
    action: "rebuild_city_scene",
    label: "Rebuild City Scene",
    kind: "system",
    keywords: ["scene", "rebuild", "visualization"],
    permission: "*",
    handler: async () => {
      const scene = cityVisualizationRuntime.rebuildScene("SceneRebuilt");
      return { ok: true, message: `rev ${scene.version}` };
    },
  });
}

function subscribeRuntimeBuses() {
  busUnsub?.();
  busUnsub = enterpriseEventBus.subscribe((event) => {
    if (!booted || rebuilding) return;
    const t = event.type;
    if (t === "life_engine_update") {
      const name = String(event.payload?.event || "");
      if (name.includes("meeting") && String(event.payload?.status || "").includes("active")) {
        cityVisualizationRuntime.rebuildScene("MeetingStarted");
      } else if (name.includes("meeting") && String(event.payload?.status || "").includes("ended")) {
        cityVisualizationRuntime.rebuildScene("MeetingFinished");
      } else if (name.includes("move") || name.includes("presence") || name.includes("arrive")) {
        cityVisualizationRuntime.rebuildScene("CitizenMoved");
      } else {
        cityVisualizationRuntime.rebuildScene("BuildingUpdated");
      }
      return;
    }
    if (t === "asset_runtime_update") {
      cityVisualizationRuntime.rebuildScene("AssetMoved");
      return;
    }
    if (t === "business_network_update") {
      cityVisualizationRuntime.rebuildScene("CompanyUpdated");
      return;
    }
    if (t === "spatial_runtime_update" || t === "digital_citizen_update") {
      const ev = String(event.payload?.event || "");
      if (ev === "LocationChanged" || ev === "EnteredBuilding" || ev.includes("Moved")) {
        cityVisualizationRuntime.rebuildScene("CitizenMoved");
      } else {
        cityVisualizationRuntime.rebuildScene("DistrictUpdated");
      }
      return;
    }
    if (t === "workflow_update") {
      const status = String(event.payload?.status || "");
      if (status === "completed" || status === "failed" || status === "running") {
        cityVisualizationRuntime.rebuildScene("WorkflowExecuted");
      }
    }
  });
}

function buildScene(): CityScene {
  runtimeDataProvider.ensureDeps();
  const meta = runtimeDataProvider.cityMeta();
  sceneSeq += 1;
  return {
    id: `scene_${meta.cityId}_${sceneSeq}`,
    cityId: meta.cityId,
    cityName: meta.cityName,
    version: CITY_VIS_VERSION,
    generatedAt: new Date().toISOString(),
    layers: visualizationRegistry.list(),
    buildings: runtimeDataProvider.buildings(),
    districts: runtimeDataProvider.districts(),
    citizens: runtimeDataProvider.citizens(),
    companies: runtimeDataProvider.companies(),
    assets: runtimeDataProvider.assets(),
    activities: runtimeDataProvider.activities(),
  };
}

function spatialKeyFromScene(scene: CityScene) {
  return [
    scene.buildings.length,
    scene.districts.length,
    scene.citizens.map((c) => `${c.citizenId}:${c.buildingId}:${c.presence}`).join("|"),
    scene.assets.map((a) => `${a.assetId}:${a.buildingId}:${a.status}`).join("|"),
    scene.activities.slice(0, 10).map((a) => `${a.id}:${a.status}`).join("|"),
  ].join("::");
}

export const cityVisualizationRuntime = {
  version: CITY_VIS_VERSION,

  startup() {
    if (booted) {
      return this.stats();
    }
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    lifeEngine.startup();
    assetRuntime.startup();
    spatialRuntime.startup();
    visualizationRegistry.reset();
    performanceLayer.clear();
    cityRendererBridge.clear();
    registerCommands();
    subscribeRuntimeBuses();
    this.rebuildScene("SceneRebuilt");
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "city_visualization", ready: true, version: CITY_VIS_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  rebuildScene(event: CityVisEventName = "SceneRebuilt") {
    if (!booted && event !== "SceneRebuilt") this.startup();
    if (rebuilding) return performanceLayer.getSceneCache() || buildScene();
    rebuilding = true;
    try {
      const prev = performanceLayer.getSceneCache();
      const scene = buildScene();
      const key = spatialKeyFromScene(scene);
      const incremental = performanceLayer.incrementalFromDiff(prev, scene, event);
      performanceLayer.putScene(scene, key);
      const query = performanceLayer.filterVisible(scene);
      cityRendererBridge.publish({
        scene,
        state: performanceLayer.getState(),
        query,
        incremental,
      });
      publishCityVisEvent(event, {
        subjectId: scene.id,
        revision: incremental.revision,
        buildings: scene.buildings.length,
        citizens: scene.citizens.length,
      });
      return scene;
    } finally {
      rebuilding = false;
    }
  },

  scene(): CityScene {
    if (!booted) this.startup();
    return performanceLayer.getSceneCache() || this.rebuildScene();
  },

  state() {
    if (!booted) this.startup();
    return performanceLayer.getState();
  },

  visibleQuery(lod?: LodTier): VisibleCityQuery {
    if (!booted) this.startup();
    const scene = this.scene();
    if (lod) performanceLayer.setLod(lod);
    return performanceLayer.filterVisible(scene, lod || performanceLayer.getState().lod);
  },

  setLod(tier: LodTier) {
    if (!booted) this.startup();
    performanceLayer.setLod(tier);
    const query = performanceLayer.filterVisible(this.scene(), tier);
    publishCityVisEvent("VisibilityChanged", { lod: tier, revision: query.revision });
    cityRendererBridge.publish({
      scene: this.scene(),
      state: performanceLayer.getState(),
      query,
      incremental: performanceLayer.lastIncremental() || undefined,
    });
    return query;
  },

  setLayerEnabled(id: VisualizationLayerId, enabled: boolean) {
    if (!booted) this.startup();
    visualizationRegistry.setEnabled(id, enabled);
    return this.setLod(performanceLayer.getState().lod);
  },

  layers() {
    if (!booted) this.startup();
    return visualizationRegistry.list();
  },

  /** City Query API */
  visibleBuildings(lod?: LodTier) {
    return this.visibleQuery(lod).buildings;
  },
  visibleCitizens(lod?: LodTier) {
    return this.visibleQuery(lod).citizens;
  },
  visibleCompanies(lod?: LodTier) {
    return this.visibleQuery(lod).companies;
  },
  visibleAssets(lod?: LodTier) {
    return this.visibleQuery(lod).assets;
  },
  visibleActivities(lod?: LodTier) {
    return this.visibleQuery(lod).activities;
  },
  visibleDistricts(lod?: LodTier) {
    return this.visibleQuery(lod).districts;
  },

  buildingState(buildingId: string) {
    return this.scene().buildings.find((b) => b.buildingId === buildingId);
  },
  districtState(districtId: string) {
    return this.scene().districts.find((d) => d.districtId === districtId);
  },
  citizenState(citizenId: string) {
    return this.scene().citizens.find((c) => c.citizenId === citizenId);
  },
  assetState(assetId: string) {
    return this.scene().assets.find((a) => a.assetId === assetId);
  },

  performance: performanceLayer,
  registry: visualizationRegistry,
  renderer: cityRendererBridge,
  events: cityVisualizationEvents,
  provider: runtimeDataProvider,

  stats() {
    if (!booted) this.startup();
    const scene = this.scene();
    const cache = performanceLayer.cacheStats();
    return {
      version: CITY_VIS_VERSION,
      city: scene.cityName,
      buildings: scene.buildings.length,
      districts: scene.districts.length,
      citizens: scene.citizens.length,
      companies: scene.companies.length,
      assets: scene.assets.length,
      activities: scene.activities.length,
      revision: cache.revision,
      lod: cache.lod,
      adapters: cityRendererBridge.list().length,
      events: cityVisualizationEvents.list(200).length,
      cache,
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    const query = this.visibleQuery();
    return {
      version: CITY_VIS_VERSION,
      scene: this.scene(),
      state: this.state(),
      query,
      layers: this.layers(),
      events: cityVisualizationEvents.list(30),
      stats: this.stats(),
      adapters: cityRendererBridge.list(),
    };
  },

  __resetForTests() {
    busUnsub?.();
    busUnsub = null;
    cityVisualizationEvents.clear();
    visualizationRegistry.reset();
    performanceLayer.clear();
    cityRendererBridge.clear();
    sceneSeq = 0;
    booted = false;
  },
};
