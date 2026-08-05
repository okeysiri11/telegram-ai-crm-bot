import { describe, expect, it, beforeEach, afterEach } from "vitest";
import { createKernel, BootLoader } from "../index.js";
import {
  createRuntimeServer,
  PLATFORM_VERSION,
  RuntimeServer,
} from "../runtime/index.js";
import { createEnterpriseDeliveryWorkflow } from "../workflow/index.js";
import { createOrchestratorService } from "@ados/orchestrator";
import { createProviderGatewayService } from "@ados/providers";
import { createChatBridgeService } from "@ados/chat-bridge";
import { createVoiceService } from "@ados/voice";
import { createMCPService } from "@ados/mcp";
import { createExecutionService } from "@ados/execution";

describe("RuntimeServer", () => {
  let kernel: ReturnType<typeof createKernel>;
  let runtime: RuntimeServer;

  beforeEach(async () => {
    const providerService = createProviderGatewayService();
    const orchService = createOrchestratorService();
    orchService.orchestrator.setProviderGateway(providerService.gateway);
    const chatService = createChatBridgeService({
      orchestrator: orchService.orchestrator,
      gateway: providerService.gateway,
    });
    const voiceService = createVoiceService({
      bridge: chatService.bridge,
    });
    const mcpService = createMCPService({
      loadDiskConfig: false,
      config: {
        enabled: true,
        authentication: {
          required: true,
          tokenHeader: "x-ados-mcp-token",
          defaultAdminToken: "test-admin-token",
        },
      },
    });
    const executionService = createExecutionService({
      orchestrator: orchService.orchestrator,
    });
    kernel = createKernel({
      config: { environment: "test", failFast: true },
      bootLoader: new BootLoader({
        extraServices: [
          providerService,
          orchService,
          chatService,
          voiceService,
          mcpService,
          executionService,
        ],
      }),
    });
    await kernel.start();
    kernel.workflowEngine.register(createEnterpriseDeliveryWorkflow());
    for (const id of [
      "agent.architect",
      "agent.backend",
      "agent.database",
      "agent.frontend",
      "agent.qa",
      "agent.docs",
      "agent.knowledge",
      "agent.devops",
      "agent.release",
      "agent.architect.compensate",
    ]) {
      kernel.workflowEngine.registerHandler(id, async () => true);
    }
    runtime = createRuntimeServer(kernel, {
      host: "127.0.0.1",
      port: 0,
      platformVersion: PLATFORM_VERSION,
    });
  });

  afterEach(async () => {
    if (runtime.isStarted) {
      await runtime.stop();
    }
    await kernel.dispose();
  });

  it("starts and stops cleanly", async () => {
    const live = createRuntimeServer(kernel, {
      host: "127.0.0.1",
      port: 34567,
    });
    await live.start();
    expect(live.isStarted).toBe(true);
    expect(live.url).toContain("34567");
    await live.stop();
    expect(live.isStarted).toBe(false);
  });

  it("GET /health returns ok", async () => {
    const res = await runtime.handleRequestForTest("GET", "/health");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: "ok" });
  });

  it("GET /status returns READY components including Orchestrator", async () => {
    await runtime.start();
    const res = await runtime.handleRequestForTest("GET", "/status");
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      version: PLATFORM_VERSION,
      kernel: "OK",
      eventBus: "OK",
      serviceMesh: "OK",
      workflowEngine: "OK",
      runtimeServer: "OK",
      orchestrator: "OK",
      providerGateway: "OK",
      chatBridge: "OK",
      voice: "OK",
      mcp: "OK",
      execution: "OK",
      systemStatus: "READY",
    });
    expect((res.body as { agents: number }).agents).toBe(7);
    expect((res.body as { providers: number }).providers).toBe(6);
  });

  it("POST /chat/task and /chat/run execute ChatGPT bridge", async () => {
    await runtime.start();
    const created = await runtime.handleRequestForTest("POST", "/chat/task", {
      prompt: "Implement export for chat history in src/chat_bridge/export.ts",
      autoRun: false,
    });
    expect(created.status).toBe(200);
    const taskId = (created.body as { task: { id: string } }).task.id;
    expect(taskId).toBeTruthy();

    const ran = await runtime.handleRequestForTest("POST", "/chat/run", {
      taskId,
    });
    expect(ran.status).toBe(200);
    const status = (ran.body as { task: { status: string } }).task.status;
    expect(["Done", "PartialSuccess"]).toContain(status);

    const history = await runtime.handleRequestForTest("GET", "/chat/history");
    expect(history.status).toBe(200);
    expect(
      (history.body as { history: unknown[] }).history.length,
    ).toBeGreaterThan(0);

    const session = await runtime.handleRequestForTest("GET", "/chat/session");
    expect(session.status).toBe(200);
  }, 30_000);

  it("POST /voice/process runs Enterprise Voice pipeline", async () => {
    await runtime.start();
    await runtime.handleRequestForTest("POST", "/voice/start", {});
    const processed = await runtime.handleRequestForTest(
      "POST",
      "/voice/process",
      {
        text: "Generate code for voice center page",
        bypassWakeWord: true,
        autoExecute: true,
      },
    );
    expect(processed.status).toBe(200);
    const body = processed.body as {
      intent: string;
      executed: boolean;
      chatTaskId?: string;
    };
    expect(body.intent).toBe("generate_code");
    expect(body.executed).toBe(true);
    expect(body.chatTaskId).toBeTruthy();

    const hist = await runtime.handleRequestForTest("GET", "/voice/history");
    expect(hist.status).toBe(200);
    expect(
      (hist.body as { history: unknown[] }).history.length,
    ).toBeGreaterThan(0);

    const settings = await runtime.handleRequestForTest(
      "GET",
      "/voice/settings",
    );
    expect(settings.status).toBe(200);
  }, 30_000);

  it("GET /mcp/* and POST /mcp/rpc expose Runtime via MCP Gateway", async () => {
    await runtime.start();
    const status = await runtime.handleRequestForTest("GET", "/mcp/status");
    expect(status.status).toBe(200);
    expect((status.body as { runtimeBound: boolean }).runtimeBound).toBe(true);
    expect((status.body as { tools: number }).tools).toBeGreaterThanOrEqual(16);

    const tools = await runtime.handleRequestForTest("GET", "/mcp/tools");
    expect(tools.status).toBe(200);

    const rpc = await runtime.handleRequestForTest("POST", "/mcp/rpc", {
      method: "tools/call",
      id: 1,
      token: "test-admin-token",
      params: { name: "system.health", arguments: {} },
    });
    expect(rpc.status).toBe(200);
    expect((rpc.body as { error?: unknown }).error).toBeUndefined();
    expect(JSON.stringify((rpc.body as { result: unknown }).result)).toContain(
      "ok",
    );
  });

  it("POST /execution/plan runs Execution Planner via Orchestrator", async () => {
    await runtime.start();
    const planned = await runtime.handleRequestForTest(
      "POST",
      "/execution/plan",
      {
        autoRun: true,
        mission: "Deliver execution planner",
        objective: "Execute ChatGPT engineering specs",
        requirements: ["Split tasks", "Parallel waves"],
        files: ["src/execution/ExecutionPlanner.ts", "platform_console/src/App.tsx"],
        modules: ["src/execution"],
        tests: ["unit"],
        acceptanceCriteria: ["Report generated"],
      },
    );
    expect(planned.status).toBe(200);
    const body = planned.body as {
      plan: { id: string; status: string; tasks: unknown[] };
      report: { summary: string } | null;
    };
    expect(body.plan.tasks.length).toBeGreaterThan(0);
    expect(["completed", "partial"]).toContain(body.plan.status);
    expect(body.report?.summary).toBeTruthy();

    const status = await runtime.handleRequestForTest("GET", "/execution/status");
    expect(status.status).toBe(200);

    const report = await runtime.handleRequestForTest("GET", "/execution/report");
    expect(report.status).toBe(200);

    const history = await runtime.handleRequestForTest(
      "GET",
      "/execution/history",
    );
    expect(history.status).toBe(200);
    expect(
      (history.body as { history: unknown[] }).history.length,
    ).toBeGreaterThan(0);
  }, 30_000);

  it("GET /services returns registry entries", async () => {
    const res = await runtime.handleRequestForTest("GET", "/services");
    expect(res.status).toBe(200);
    const body = res.body as { services: Array<{ id: string }> };
    expect(body.services.length).toBe(kernel.registry.list().length);
    expect(body.services.some((s) => s.id === "ados.event_bus")).toBe(true);
    expect(body.services.some((s) => s.id === "ados.orchestrator")).toBe(true);
    expect(body.services.some((s) => s.id === "ados.provider_gateway")).toBe(
      true,
    );
  });

  it("GET /workflow returns registered workflows", async () => {
    const res = await runtime.handleRequestForTest("GET", "/workflow");
    expect(res.status).toBe(200);
    const body = res.body as {
      workflows: Array<{ id: string; steps: number }>;
    };
    expect(body.workflows.some((w) => w.id === "enterprise.delivery")).toBe(
      true,
    );
  });

  it("GET /agents lists orchestrator agents", async () => {
    const res = await runtime.handleRequestForTest("GET", "/agents");
    expect(res.status).toBe(200);
    const body = res.body as { agents: Array<{ id: string; health: string }> };
    expect(body.agents.length).toBe(7);
    expect(body.agents.every((a) => a.health === "OK")).toBe(true);
  });

  it("POST /orchestrator/task routes to developer", async () => {
    const res = await runtime.handleRequestForTest(
      "POST",
      "/orchestrator/task",
      {
        type: "code.implement",
        payload: { feature: "x" },
      },
    );
    expect(res.status).toBe(200);
    const body = res.body as { agentId: string; status: string };
    expect(body.agentId).toBe("agent.developer");
    expect(body.status).toBe("completed");
  });

  it("GET /providers lists mock providers", async () => {
    const res = await runtime.handleRequestForTest("GET", "/providers");
    expect(res.status).toBe(200);
    const body = res.body as {
      providers: Array<{ id: string; connected: boolean }>;
      gateway: { health: string };
    };
    expect(body.gateway.health).toBe("OK");
    expect(body.providers.length).toBe(6);
    expect(body.providers.every((p) => p.connected)).toBe(true);
  });

  it("POST /providers/execute uses gateway", async () => {
    const res = await runtime.handleRequestForTest("POST", "/providers/execute", {
      preferredAlias: "claude",
      capability: "chat",
      payload: { prompt: "hi" },
    });
    expect(res.status).toBe(200);
    const body = res.body as { ok: boolean; providerId: string };
    expect(body.ok).toBe(true);
    expect(body.providerId).toBe("provider.claude");
  });

  it("POST /workflow/start runs multi-agent CRM collaboration", async () => {
    const res = await runtime.handleRequestForTest("POST", "/workflow/start", {
      templateId: "tpl.crm_generation",
      name: "CRM for construction company",
      payload: { industry: "construction" },
    });
    expect(res.status).toBe(200);
    const body = res.body as { id: string; status: string; templateId: string };
    expect(body.templateId).toBe("tpl.crm_generation");
    expect(["Running", "Completed"]).toContain(body.status);

    for (let i = 0; i < 80; i++) {
      const get = await runtime.handleRequestForTest("GET", `/workflow/${body.id}`);
      const snap = get.body as { status: string };
      if (snap.status === "Completed" || snap.status === "Failed") {
        expect(snap.status).toBe("Completed");
        break;
      }
      await new Promise((r) => setTimeout(r, 100));
    }
  }, 30_000);

  it("live HTTP /health and /status after listen", async () => {
    const live = createRuntimeServer(kernel, {
      host: "127.0.0.1",
      port: 34568,
    });
    await live.start();
    try {
      const health = await fetch("http://127.0.0.1:34568/health");
      expect(health.status).toBe(200);
      expect(await health.json()).toEqual({ status: "ok" });

      const status = await fetch("http://127.0.0.1:34568/status");
      expect(status.status).toBe(200);
      const json = (await status.json()) as {
        version: string;
        kernel: string;
        orchestrator: string;
      };
      expect(json.version).toBe(PLATFORM_VERSION);
      expect(json.kernel).toBe("OK");
      expect(json.orchestrator).toBe("OK");
      expect(
        (json as { providerGateway: string }).providerGateway,
      ).toBe("OK");
    } finally {
      await live.stop();
    }
  });
});
