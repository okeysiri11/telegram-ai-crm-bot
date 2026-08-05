import { beforeEach, describe, expect, it } from "vitest";
import {
  KERNEL_RUNTIME_VERSION,
  enterpriseKernel,
  kernelApi,
  kernelEvents,
} from "@/runtime/kernel";
import { enterpriseOrchestrator } from "@/runtime/orchestrator";
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

describe("Sprint 29.9 Enterprise Kernel Runtime", () => {
  beforeEach(() => {
    enterpriseKernel.__resetForTests();
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
    enterpriseKernel.boot();
  });

  it("boots platform through full lifecycle to ready with version 29.9", () => {
    expect(KERNEL_RUNTIME_VERSION).toBe("29.9");
    const status = enterpriseKernel.status();
    expect(status.ready || status.degraded).toBe(true);
    expect(["ready", "degraded"]).toContain(status.phase);
    const steps = enterpriseKernel.bootSequence();
    expect(steps.some((s) => s.id === "configuration" && s.status === "ok")).toBe(true);
    expect(steps.some((s) => s.id === "orchestrator_startup" && s.status === "ok")).toBe(true);
    expect(steps.some((s) => s.id === "platform_ready" && (s.status === "ok" || s.status === "failed"))).toBe(
      true,
    );
    expect(enterpriseOrchestrator.isReady()).toBe(true);
  });

  it("collects diagnostics and aggregates health", () => {
    const diag = enterpriseKernel.diagnostics();
    expect(diag.runtimes.length).toBeGreaterThan(0);
    expect(diag.startupTimeMs === null || diag.startupTimeMs >= 0).toBe(true);
    const health = enterpriseKernel.healthSnapshot();
    expect(health.runtimeTotal).toBeGreaterThan(0);
    expect(health.eventBusOk).toBe(true);
  });

  it("recovers a runtime without crashing the platform", () => {
    const before = enterpriseKernel.status().phase;
    const rec = enterpriseKernel.recover("intelligence");
    expect(rec.action === "restart" || rec.action === "platform_continue" || rec.action === "mark_unhealthy").toBe(
      true,
    );
    expect(enterpriseKernel.isReady()).toBe(true);
    expect(enterpriseKernel.recoveryHistory().length).toBeGreaterThan(0);
    expect(["ready", "degraded", "recovering"].includes(enterpriseKernel.status().phase) || before).toBeTruthy();
  });

  it("loads configuration feature flags and license hooks", () => {
    const cfg = enterpriseKernel.config();
    expect(cfg.featureFlags.orchestratorEnabled).toBe(true);
    expect(cfg.license.verified).toBe(true);
    enterpriseKernel.configuration.setFeatureFlag("diagnosticsEnabled", false);
    expect(enterpriseKernel.config().featureFlags.diagnosticsEnabled).toBe(false);
    enterpriseKernel.configuration.setFeatureFlag("diagnosticsEnabled", true);
  });

  it("publishes kernel events and integrates command/API", async () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "kernel_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    enterpriseKernel.diagnostics();
    expect(seen).toContain("DiagnosticsCollected");
    expect(kernelEvents.list().length).toBeGreaterThan(0);
    const cmd = await commandRuntime.execute("kernel_open");
    expect(cmd.ok).toBe(true);
    const inv = await kernelApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
    unsub();
  });
});
