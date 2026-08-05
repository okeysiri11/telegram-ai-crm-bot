import { describe, expect, it, beforeEach } from "vitest";
import {
  createAiOrchestrator,
  createOrchestratorService,
  ORCHESTRATOR_SERVICE_ID,
} from "../index.js";

describe("AiOrchestrator", () => {
  const orch = createAiOrchestrator();

  beforeEach(() => {
    orch.registry.clear();
    orch.logs.clear();
    orch.stop();
  });

  it("auto-registers collaboration agents on start", () => {
    orch.start(true);
    const ids = orch.listAgents().map((a) => a.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "agent.developer",
        "agent.research",
        "agent.business",
        "agent.architect",
        "agent.reviewer",
        "agent.qa",
        "agent.automation",
      ]),
    );
    expect(orch.getStatus().health).toBe("OK");
    expect(orch.getStatus().agents).toBe(7);
  });

  it("routes tasks only through orchestrator", async () => {
    orch.start(true);
    const res = await orch.submitTask({
      type: "code.implement",
      payload: { feature: "login" },
    });
    expect(res.agentId).toBe("agent.developer");
    expect(res.status).toBe("completed");
    expect(res.result?.ok).toBe(true);

    const arch = await orch.submitTask({
      type: "architecture.design",
      payload: { system: "crm" },
    });
    expect(arch.agentId).toBe("agent.architect");
  });

  it("runs preferred agent via runAgent", async () => {
    orch.start(true);
    const result = await orch.runAgent("agent.qa", {
      type: "qa.test",
      payload: { suite: "smoke" },
    });
    expect(result.agentId).toBe("agent.qa");
    expect(result.ok).toBe(true);
    expect(orch.logs.list({ agentId: "agent.qa" }).length).toBeGreaterThan(0);
  });

  it("exposes aggregate metrics", async () => {
    orch.start(true);
    await orch.submitTask({ type: "research.analyze", payload: {} });
    const m = orch.aggregateMetrics();
    expect(m.tasksCompleted).toBeGreaterThanOrEqual(1);
    expect(m.successes).toBeGreaterThanOrEqual(1);
  });
});

describe("CollaborationEngine", () => {
  it("runs CRM multi-agent workflow through orchestrator", async () => {
    const svc = createOrchestratorService();
    await svc.initialize();
    await svc.start();
    const started = await svc.collaboration.start({
      templateId: "tpl.crm_generation",
      name: "CRM for construction company",
      payload: { industry: "construction" },
    });
    expect(started.status).toBe("Running");
    // wait for completion
    for (let i = 0; i < 80; i++) {
      const snap = svc.collaboration.get(started.id);
      if (snap && (snap.status === "Completed" || snap.status === "Failed")) {
        expect(snap.status).toBe("Completed");
        expect(snap.steps.every((s) => s.status === "completed")).toBe(true);
        const ctx = svc.collaboration.getContext(started.id);
        expect(ctx.artifacts.length).toBeGreaterThan(0);
        expect(svc.collaboration.timeline.list({ workflowId: started.id }).length).toBeGreaterThan(0);
        break;
      }
      await new Promise((r) => setTimeout(r, 100));
    }
    await svc.stop();
  }, 30_000);

  it("supports pause and resume", async () => {
    const svc = createOrchestratorService();
    await svc.initialize();
    await svc.start();
    const started = await svc.collaboration.start({
      templateId: "tpl.bug_fix",
      payload: { bug: "null-ref" },
    });
    await svc.collaboration.pause(started.id);
    expect(svc.collaboration.get(started.id)?.status).toBe("Paused");
    await svc.collaboration.resume(started.id);
    for (let i = 0; i < 60; i++) {
      const snap = svc.collaboration.get(started.id);
      if (snap?.status === "Completed") break;
      await new Promise((r) => setTimeout(r, 100));
    }
    expect(svc.collaboration.get(started.id)?.status).toBe("Completed");
    await svc.stop();
  }, 30_000);
});

describe("OrchestratorService", () => {
  it("implements kernel service lifecycle and registers agents", async () => {
    const svc = createOrchestratorService();
    expect(svc.id).toBe(ORCHESTRATOR_SERVICE_ID);
    await svc.initialize();
    await svc.start();
    expect(svc.getLifecycleState()).toBe("Started");
    expect(svc.orchestrator.listAgents().length).toBe(7);
    expect(svc.collaboration.listTemplates().length).toBeGreaterThanOrEqual(10);
    expect(svc.health().status).toBe("healthy");
    await svc.stop();
    expect(svc.getLifecycleState()).toBe("Stopped");
  });
});
