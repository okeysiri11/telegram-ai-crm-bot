import { beforeEach, describe, expect, it } from "vitest";
import {
  ORCHESTRATOR_RUNTIME_VERSION,
  enterpriseOrchestrator,
  runtimeDependencyGraph,
  CircularDependencyError,
  runtimeRegistry,
  orchestratorApi,
  orchestratorEvents,
} from "@/runtime/orchestrator";
import { intelligenceRuntime } from "@/runtime/intelligenceRuntime";
import { interactionRuntime } from "@/runtime/interactionRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.8 Enterprise Orchestrator Runtime", () => {
  beforeEach(() => {
    enterpriseOrchestrator.__resetForTests();
    intelligenceRuntime.__resetForTests();
    interactionRuntime.__resetForTests();
    cityVisualizationRuntime.__resetForTests();
    spatialRuntime.__resetForTests();
    assetRuntime.__resetForTests();
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    enterpriseOrchestrator.startup();
  });

  it("registers all enterprise runtimes with version 29.8", () => {
    expect(ORCHESTRATOR_RUNTIME_VERSION).toBe("29.8");
    const ids = runtimeRegistry.ids();
    expect(ids).toContain("business_network");
    expect(ids).toContain("digital_citizen");
    expect(ids).toContain("asset");
    expect(ids).toContain("life");
    expect(ids).toContain("spatial");
    expect(ids).toContain("city_visualization");
    expect(ids).toContain("interaction");
    expect(ids).toContain("intelligence");
    expect(enterpriseOrchestrator.runtimes().length).toBeGreaterThanOrEqual(8);
  });

  it("builds acyclic dependency order matching canonical chain", () => {
    const order = enterpriseOrchestrator.dependencyOrder();
    expect(order.indexOf("business_network")).toBeLessThan(order.indexOf("digital_citizen"));
    expect(order.indexOf("digital_citizen")).toBeLessThan(order.indexOf("life"));
    expect(order.indexOf("spatial")).toBeLessThan(order.indexOf("city_visualization"));
    expect(order.indexOf("interaction")).toBeLessThan(order.indexOf("intelligence"));
    expect(() => runtimeDependencyGraph.assertAcyclic()).not.toThrow();

    // Inject circular dep and ensure detector throws
    const intel = runtimeRegistry.get("intelligence")!;
    const prev = [...intel.dependencies];
    runtimeRegistry.register({
      ...intel,
      dependencies: [...prev, "business_network"],
    });
    // business → … → intelligence → business would require editing business too
    runtimeRegistry.register({
      ...runtimeRegistry.get("business_network")!,
      dependencies: ["intelligence"],
    });
    expect(() => runtimeDependencyGraph.assertAcyclic()).toThrow(CircularDependencyError);
    // restore via full reset path on next test
  });

  it("aggregates platform health and schedules orchestration ops", () => {
    const health = enterpriseOrchestrator.platformHealth();
    expect(health.total).toBeGreaterThanOrEqual(8);
    expect(health.healthy + health.starting + health.busy + health.error + health.stopped + health.maintenance).toBe(
      health.total,
    );
    const job = enterpriseOrchestrator.schedule("refresh", "intelligence");
    expect(job.ok).toBe(true);
    expect(enterpriseOrchestrator.queue().length).toBeGreaterThan(0);
  });

  it("routes EventBus events through workflow coordinator", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "orchestrator_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    enterpriseOrchestrator.coordinator.route(
      { type: "life_engine_update", payload: { event: "test" } },
      { refresh: false },
    );
    expect(enterpriseOrchestrator.routedEvents().some((r) => r.busType === "life_engine_update")).toBe(
      true,
    );
    expect(seen).toContain("EventRouted");
    expect(orchestratorEvents.list().length).toBeGreaterThan(0);
    unsub();
  });

  it("integrates command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("orchestrator_open");
    expect(cmd.ok).toBe(true);
    const inv = await orchestratorApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
