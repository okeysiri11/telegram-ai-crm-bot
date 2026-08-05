import { beforeEach, describe, expect, it } from "vitest";
import {
  CITY_VIS_VERSION,
  cityVisualizationRuntime,
  cityVisualizationEvents,
  cityVisualizationApi,
  cityRendererBridge,
  performanceLayer,
  visualizationRegistry,
} from "@/runtime/cityVisualization";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.5 Enterprise City Visualization Runtime", () => {
  beforeEach(() => {
    cityVisualizationRuntime.__resetForTests();
    spatialRuntime.__resetForTests();
    assetRuntime.__resetForTests();
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    cityVisualizationRuntime.startup();
  });

  it("boots scene from real runtimes with version 29.5", () => {
    expect(CITY_VIS_VERSION).toBe("29.5");
    const scene = cityVisualizationRuntime.scene();
    expect(scene.cityName).toBe("Odessa");
    expect(scene.buildings.length).toBeGreaterThan(0);
    expect(scene.districts.length).toBeGreaterThan(0);
    expect(scene.citizens.length).toBeGreaterThan(0);
    expect(scene.assets.length).toBeGreaterThan(0);
    expect(scene.companies.length).toBeGreaterThan(0);
    expect(cityVisualizationRuntime.stats().revision).toBeGreaterThan(0);
  });

  it("bridges building district citizen and asset visual state", () => {
    const hub = cityVisualizationRuntime.buildingState("hub");
    expect(hub).toBeTruthy();
    expect(hub!.openState).toBeTruthy();
    expect(["idle", "active", "busy", "alert", "offline", "maintenance"]).toContain(hub!.status);

    const enterprise = cityVisualizationRuntime.districtState("enterprise");
    expect(enterprise?.buildingIds.length).toBeGreaterThan(0);
    expect(enterprise?.population).toBeGreaterThanOrEqual(0);

    const citizen = cityVisualizationRuntime.citizenState(EDC_CITIZEN_OWNER);
    expect(citizen?.presence).toBeTruthy();
    expect(citizen?.avatarRef).toBeTruthy();

    const assets = cityVisualizationRuntime.visibleAssets();
    expect(assets.some((a) => a.isHeadquarters || a.isVehicle || a.isDrone)).toBe(true);
  });

  it("filters visibility by LOD and layers (performance)", () => {
    const near = cityVisualizationRuntime.setLod("near");
    expect(near.citizens.length).toBeGreaterThan(0);
    expect(near.assets.length).toBeGreaterThan(0);

    const far = cityVisualizationRuntime.setLod("far");
    expect(far.citizens.length).toBe(0);
    expect(far.assets.length).toBe(0);
    expect(far.buildings.length).toBeGreaterThan(0);

    cityVisualizationRuntime.setLayerEnabled("buildings", false);
    const hidden = cityVisualizationRuntime.visibleQuery("near");
    expect(hidden.buildings.length).toBe(0);
    cityVisualizationRuntime.setLayerEnabled("buildings", true);

    const cache = performanceLayer.cacheStats();
    expect(cache.hasScene).toBe(true);
    expect(visualizationRegistry.list().length).toBeGreaterThanOrEqual(6);
  });

  it("publishes visualization events and renderer bridge payloads", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "city_visualization_update") seen.push(String(e.payload?.event || ""));
    });
    let payloads = 0;
    cityRendererBridge.register({
      id: "test_adapter",
      label: "Test",
      onPayload: () => {
        payloads += 1;
      },
    });
    cityVisualizationRuntime.rebuildScene("BuildingUpdated");
    expect(seen).toContain("BuildingUpdated");
    expect(payloads).toBeGreaterThan(0);
    expect(cityVisualizationEvents.list().some((e) => e.name === "SceneRebuilt" || e.name === "BuildingUpdated")).toBe(
      true,
    );
    unsub();
  });

  it("integrates workflow events into WorkflowExecuted", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "city_visualization_update") seen.push(String(e.payload?.event || ""));
    });
    enterpriseEventBus.publish({
      type: "workflow_update",
      source: "system",
      payload: { status: "completed", sessionId: "wf_test", definitionId: "def_test" },
    });
    expect(seen).toContain("WorkflowExecuted");
    unsub();
  });

  it("integrates command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("city_viz_open");
    expect(cmd.ok).toBe(true);
    const inv = await cityVisualizationApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
