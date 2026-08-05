/**
 * Registered runtime adapters — Sprint 29.8.
 * Wraps existing engines; does not duplicate business logic.
 */

import { businessNetworkEngine, BUSINESS_NETWORK_VERSION } from "@/runtime/businessNetwork";
import { digitalCitizenEngine, DIGITAL_CITIZEN_VERSION } from "@/runtime/digitalCitizen";
import { lifeEngine, LIFE_ENGINE_VERSION } from "@/runtime/lifeEngine";
import { assetRuntime, ASSET_RUNTIME_VERSION } from "@/runtime/assetRuntime";
import { spatialRuntime, SPATIAL_RUNTIME_VERSION } from "@/runtime/spatialRuntime";
import { cityVisualizationRuntime, CITY_VIS_VERSION } from "@/runtime/cityVisualization";
import { interactionRuntime, INTERACTION_RUNTIME_VERSION } from "@/runtime/interactionRuntime";
import { intelligenceRuntime, INTELLIGENCE_RUNTIME_VERSION } from "@/runtime/intelligenceRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import type { RuntimeAdapter, RuntimeHealthReport } from "./orchestratorTypes";
import { runtimeRegistry } from "./RuntimeRegistry";

function now() {
  return new Date().toISOString();
}

function healthFromReady(ready: boolean, details?: Record<string, unknown>): RuntimeHealthReport {
  return {
    status: ready ? "healthy" : "stopped",
    checkedAt: now(),
    details,
  };
}

function probeTry(fn: () => RuntimeHealthReport): RuntimeHealthReport {
  try {
    return fn();
  } catch (e) {
    return {
      status: "error",
      message: e instanceof Error ? e.message : "error",
      checkedAt: now(),
    };
  }
}

export const RUNTIME_ADAPTERS: RuntimeAdapter[] = [
  {
    id: "workflow",
    label: "Workflow Runtime",
    version: "28.x",
    dependencies: [],
    events: ["workflow_update"],
    api: "/api/enterprise-ewf/v1",
    permissions: ["workflow"],
    route: "/workflow-runtime",
    startup: () => workflowRuntime.startup(),
    refresh: () => workflowRuntime.startup(),
    sync: () => workflowRuntime.startup(),
    probeHealth: () =>
      probeTry(() =>
        healthFromReady(true, { sessions: workflowRuntime.listSessions().length }),
      ),
  },
  {
    id: "automation",
    label: "Automation Engine",
    version: "28.9",
    dependencies: ["workflow"],
    events: ["runtime_update"],
    api: "/api/auto/v1",
    permissions: ["automation"],
    route: "/automation",
    startup: () => automationEngine.startup(),
    refresh: () => automationEngine.startup(),
    sync: () => automationEngine.startup(),
    probeHealth: () =>
      probeTry(() =>
        healthFromReady(true, { queue: automationEngine.listQueue().length }),
      ),
  },
  {
    id: "business_network",
    label: "Business Network",
    version: BUSINESS_NETWORK_VERSION,
    dependencies: [],
    events: ["business_network_update"],
    api: "/api/enterprise-ebn/v1",
    permissions: ["ebn", "partners"],
    route: "/business-network",
    startup: () => businessNetworkEngine.startup(),
    reload: () => businessNetworkEngine.startup(),
    refresh: () => businessNetworkEngine.startup(),
    sync: () => businessNetworkEngine.startup(),
    probeHealth: () =>
      probeTry(() => {
        const s = businessNetworkEngine.stats();
        return healthFromReady(true, s as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "digital_citizen",
    label: "Digital Citizens",
    version: DIGITAL_CITIZEN_VERSION,
    dependencies: ["business_network"],
    events: ["digital_citizen_update"],
    api: "/api/enterprise-edc/v1",
    permissions: ["citizen"],
    route: "/digital-citizens",
    startup: () => digitalCitizenEngine.startup(),
    reload: () => digitalCitizenEngine.startup(),
    refresh: () => digitalCitizenEngine.startup(),
    sync: () => digitalCitizenEngine.startup(),
    probeHealth: () =>
      probeTry(() => {
        const s = digitalCitizenEngine.stats();
        return healthFromReady(true, s as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "asset",
    label: "Asset Runtime",
    version: ASSET_RUNTIME_VERSION,
    dependencies: ["digital_citizen", "business_network"],
    events: ["asset_runtime_update"],
    api: "/api/enterprise-assets/v1",
    permissions: ["assets"],
    route: "/assets",
    startup: () => assetRuntime.startup(),
    reload: () => assetRuntime.startup(),
    refresh: () => assetRuntime.startup(),
    sync: () => assetRuntime.startup(),
    probeHealth: () =>
      probeTry(() => {
        const ready = assetRuntime.isReady();
        return healthFromReady(ready, assetRuntime.stats() as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "life",
    label: "Life Engine",
    version: LIFE_ENGINE_VERSION,
    dependencies: ["digital_citizen", "business_network", "asset"],
    events: ["life_engine_update"],
    api: "/api/enterprise-life/v1",
    permissions: ["life"],
    route: "/life-engine",
    startup: () => lifeEngine.startup(),
    reload: () => lifeEngine.startup(),
    refresh: () => lifeEngine.startup(),
    sync: () => lifeEngine.startup(),
    probeHealth: () =>
      probeTry(() => {
        const s = lifeEngine.stats();
        return healthFromReady(true, s as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "spatial",
    label: "Spatial Runtime",
    version: SPATIAL_RUNTIME_VERSION,
    dependencies: ["life", "asset"],
    events: ["spatial_runtime_update"],
    api: "/api/enterprise-spatial/v1",
    permissions: ["spatial"],
    route: "/spatial",
    startup: () => spatialRuntime.startup(),
    reload: () => spatialRuntime.startup(),
    rebuild: () => spatialRuntime.startup(),
    refresh: () => spatialRuntime.startup(),
    warmCache: () => {
      spatialRuntime.startup();
      spatialRuntime.cityQuery();
    },
    probeHealth: () =>
      probeTry(() => {
        const ready = spatialRuntime.isReady();
        return healthFromReady(ready, spatialRuntime.stats() as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "city_visualization",
    label: "City Visualization",
    version: CITY_VIS_VERSION,
    dependencies: ["spatial", "life", "asset"],
    events: ["city_visualization_update"],
    api: "/api/enterprise-city-viz/v1",
    permissions: ["city_viz"],
    route: "/city-visualization",
    startup: () => cityVisualizationRuntime.startup(),
    reload: () => cityVisualizationRuntime.rebuildScene("SceneRebuilt"),
    rebuild: () => cityVisualizationRuntime.rebuildScene("SceneRebuilt"),
    refresh: () => cityVisualizationRuntime.rebuildScene("BuildingUpdated"),
    warmCache: () => {
      cityVisualizationRuntime.startup();
      cityVisualizationRuntime.visibleQuery();
    },
    probeHealth: () =>
      probeTry(() => {
        const ready = cityVisualizationRuntime.isReady();
        return healthFromReady(ready, cityVisualizationRuntime.stats() as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "interaction",
    label: "Interaction Runtime",
    version: INTERACTION_RUNTIME_VERSION,
    dependencies: ["city_visualization", "spatial"],
    events: ["interaction_runtime_update"],
    api: "/api/enterprise-interaction/v1",
    permissions: ["interaction"],
    route: "/interactions",
    startup: () => interactionRuntime.startup(),
    reload: () => interactionRuntime.startup(),
    refresh: () => {
      interactionRuntime.startup();
      interactionRuntime.catalog();
    },
    warmCache: () => interactionRuntime.catalog(),
    probeHealth: () =>
      probeTry(() => {
        const ready = interactionRuntime.isReady();
        return healthFromReady(ready, interactionRuntime.stats() as unknown as Record<string, unknown>);
      }),
  },
  {
    id: "intelligence",
    label: "Intelligence Runtime",
    version: INTELLIGENCE_RUNTIME_VERSION,
    dependencies: ["interaction", "city_visualization", "life", "asset", "business_network"],
    events: ["intelligence_runtime_update"],
    api: "/api/enterprise-intelligence/v1",
    permissions: ["intelligence", "advisory"],
    route: "/intelligence",
    startup: () => intelligenceRuntime.startup(),
    reload: () => intelligenceRuntime.analyze({ force: true }),
    rebuild: () => intelligenceRuntime.analyze({ force: true }),
    refresh: () => intelligenceRuntime.analyze(),
    sync: () => intelligenceRuntime.analyze({ force: true }),
    warmCache: () => intelligenceRuntime.analyze({ force: true }),
    probeHealth: () =>
      probeTry(() => {
        const ready = intelligenceRuntime.isReady();
        const s = intelligenceRuntime.stats();
        return {
          status: ready ? (s.autonomousExecution ? "error" : "healthy") : "stopped",
          checkedAt: now(),
          details: s as unknown as Record<string, unknown>,
          message: ready ? "advisory_only" : "stopped",
        };
      }),
  },
];

export function registerAllRuntimeAdapters() {
  for (const adapter of RUNTIME_ADAPTERS) {
    runtimeRegistry.register(adapter);
  }
  return runtimeRegistry.descriptors();
}
