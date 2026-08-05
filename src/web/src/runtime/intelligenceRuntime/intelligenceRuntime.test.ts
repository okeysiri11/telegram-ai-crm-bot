import { beforeEach, describe, expect, it } from "vitest";
import {
  INTELLIGENCE_RUNTIME_VERSION,
  intelligenceRuntime,
  intelligenceEvents,
  intelligenceRuntimeApi,
  intelligenceCache,
} from "@/runtime/intelligenceRuntime";
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

describe("Sprint 29.7 Enterprise Intelligence Runtime", () => {
  beforeEach(() => {
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
    intelligenceRuntime.startup();
  });

  it("boots advisory analysis cycle with version 29.7", () => {
    expect(INTELLIGENCE_RUNTIME_VERSION).toBe("29.7");
    expect(intelligenceRuntime.policy.autonomousExecution).toBe(false);
    expect(intelligenceRuntime.policy.advisoryOnly).toBe(true);
    const cycle = intelligenceRuntime.cycle();
    expect(cycle.insights.length).toBeGreaterThan(0);
    expect(cycle.recommendations.length).toBeGreaterThan(0);
    expect(cycle.trends.length).toBeGreaterThan(0);
    expect(cycle.analytics.citizenOnline).toBeGreaterThanOrEqual(0);
  });

  it("produces analytics insights and audience recommendations", () => {
    const analytics = intelligenceRuntime.analytics();
    expect(analytics.businessActivity).toBeGreaterThanOrEqual(0);
    expect(intelligenceRuntime.insights("asset").length).toBeGreaterThan(0);
    expect(intelligenceRuntime.recommendations("owner").length).toBeGreaterThan(0);
    expect(intelligenceRuntime.recommendations("manager").length).toBeGreaterThanOrEqual(0);
    expect(intelligenceRuntime.recommendations("partner").length).toBeGreaterThanOrEqual(0);
    expect(intelligenceRuntime.recommendations("citizen").length).toBeGreaterThan(0);
    for (const r of intelligenceRuntime.recommendations()) {
      expect(r.requiresApproval).toBe(true);
    }
  });

  it("detects risks and forbids autonomous execution", () => {
    // Seed maintenance asset pressure via existing seed + force cycle
    const risks = intelligenceRuntime.risks();
    expect(Array.isArray(risks)).toBe(true);
    const blocked = intelligenceRuntime.executeRecommendation("rec_any");
    expect(blocked.ok).toBe(false);
    expect(blocked.error).toBe("autonomous_execution_forbidden");
  });

  it("caches incremental cycles and publishes events", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "intelligence_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    const a = intelligenceRuntime.analyze({ force: true });
    const b = intelligenceRuntime.analyze();
    expect(b.revision).toBe(a.revision);
    expect(intelligenceCache.fingerprintValid).toBeTruthy();
    intelligenceRuntime.analyze({ force: true });
    expect(seen).toContain("InsightCreated");
    expect(seen).toContain("RecommendationCreated");
    expect(intelligenceEvents.list().length).toBeGreaterThan(0);
    unsub();
  });

  it("integrates command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("intelligence_open");
    expect(cmd.ok).toBe(true);
    const inv = await intelligenceRuntimeApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
    expect((inv as { policy?: { autonomousExecution: boolean } }).policy?.autonomousExecution).toBe(
      false,
    );
  });
});
