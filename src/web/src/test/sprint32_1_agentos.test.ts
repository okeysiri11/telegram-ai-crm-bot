/**
 * Sprint 32.1 — Enterprise AgentOS tests.
 * Naming note: External Pilot also uses Sprint 32.1.
 */
import { beforeEach, describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import { DEFAULT_AGENTS, agentsByMarketplaceTag } from "@/enterprise-runtime/defaultAgents";
import { aiAgentRuntime } from "@/enterprise-runtime/aiAgentRuntime";
import { agentOs } from "@/enterprise-runtime/agentOs";
import { jobManager } from "@/enterprise-runtime/jobManager";

describe("Sprint 32.1 Enterprise Multi-Agent OS", () => {
  beforeEach(() => {
    agentOs.resetBus();
  });

  it("web sprint is 33.2 Intelligent Navigation track", () => {
    expect(webConfig.sprint).toBe("33.2.1");
  });

  it("registry covers executive + production roles", () => {
    const roles = DEFAULT_AGENTS.map((a) => a.role);
    for (const required of [
      "owner",
      "ceo",
      "project_manager",
      "developer",
      "architect",
      "lawyer",
      "marketing",
      "sales",
      "support",
      "accountant",
      "production",
      "construction",
      "crypto",
      "medical",
      "research",
      "image",
      "video",
      "audio",
      "prompt",
      "brand",
      "workflow",
      "publishing",
    ]) {
      expect(roles).toContain(required);
    }
    expect(DEFAULT_AGENTS.every((a) => a.version && a.permissions.length)).toBe(true);
    expect(agentsByMarketplaceTag("production").length).toBeGreaterThanOrEqual(5);
    expect(agentOs.registry().length).toBe(DEFAULT_AGENTS.length);
  });

  it("lifecycle phases are observable and resumable", () => {
    const id = "agent_developer";
    agentOs.launch(id, "Build feature");
    expect(aiAgentRuntime.get(id)?.phase).toBe("running");
    agentOs.pause(id);
    expect(aiAgentRuntime.get(id)?.phase).toBe("paused");
    agentOs.resume(id);
    expect(aiAgentRuntime.get(id)?.phase).toBe("running");
    agentOs.complete(id);
    expect(aiAgentRuntime.get(id)?.phase).toBe("idle");
    agentOs.fail(id, "boom");
    expect(aiAgentRuntime.get(id)?.status).toBe("error");
    agentOs.retry(id, "retry build");
    expect(aiAgentRuntime.get(id)?.phase).toBe("running");
    agentOs.cancel(id);
    expect(aiAgentRuntime.get(id)?.phase).toBe("idle");
  });

  it("inter-agent messaging, memory, and collaborative aggregation", () => {
    const run = agentOs.runCollaborative({
      title: "Ship campaign pack",
      leadAgentId: "agent_project_manager",
      workerIds: ["agent_marketing", "agent_brand", "agent_copywriter"],
      viaProduction: true,
    });
    expect(run.status).toBe("completed");
    expect(Object.keys(run.results).length).toBe(3);
    expect(agentOs.listMessages().some((m) => m.type === "delegate")).toBe(true);
    expect(agentOs.recall("agent_marketing", "short").length).toBeGreaterThan(0);
    expect(agentOs.auditTrail(10).length).toBeGreaterThan(0);
    expect(jobManager.list().some((j) => j.title.includes("AgentOS"))).toBe(true);
  });

  it("observability snapshot for Owner", () => {
    agentOs.launch("agent_production", "render");
    const obs = agentOs.observe();
    expect(obs.systemOfRecord).toBe("enterprise_runtime");
    expect(obs.n8nBusinessLogic).toBe(false);
    expect(obs.health.total).toBeGreaterThan(15);
    expect(obs.runningAgents.length).toBeGreaterThan(0);
    expect(typeof obs.costUsd).toBe("number");
  });

  it("exports AgentOsMonitor", async () => {
    expect(typeof (await import("@/ai-runtime/AgentOsMonitor")).AgentOsMonitor).toBe("function");
  }, 15_000);
});
