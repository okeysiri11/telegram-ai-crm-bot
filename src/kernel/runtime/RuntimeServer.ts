import http from "node:http";
import type { IncomingMessage, ServerResponse } from "node:http";
import { WebSocketServer, type WebSocket } from "ws";
import {
  ORCHESTRATOR_SERVICE_ID,
  type OrchestratorService,
} from "@ados/orchestrator";
import {
  PROVIDER_GATEWAY_SERVICE_ID,
  type ProviderGatewayService,
} from "@ados/providers";
import {
  CHAT_BRIDGE_SERVICE_ID,
  type ChatBridgeService,
} from "@ados/chat-bridge";
import {
  VOICE_SERVICE_ID,
  type VoiceService,
} from "@ados/voice";
import {
  MCP_SERVICE_ID,
  type MCPService,
} from "@ados/mcp";
import {
  EXECUTION_SERVICE_ID,
  type ExecutionService,
} from "@ados/execution";
import type { Kernel } from "../Kernel.js";
import { createEnterpriseDeliveryWorkflow } from "../workflow/index.js";
import { RuntimeLogBuffer } from "./RuntimeLogBuffer.js";
import type {
  AgentListItem,
  EventEntry,
  HealthResponse,
  KernelInfoResponse,
  MetricsResponse,
  RuntimeServerOptions,
  ServiceListItem,
  StatusResponse,
  WorkflowListItem,
} from "./types.js";

export const PLATFORM_VERSION = "1.1.0";

/**
 * ADOS Runtime Server — HTTP + WebSocket surface over Kernel services.
 * Orchestrator is resolved from the registry (registered at boot).
 */
export class RuntimeServer {
  readonly host: string;
  readonly port: number;
  readonly platformVersion: string;

  private readonly kernel: Kernel;
  private readonly logs = new RuntimeLogBuffer();
  private readonly events: EventEntry[] = [];
  private readonly bootStartedAt = Date.now();
  private readonly bootStartedIso = new Date().toISOString();
  private cpuBaseline = process.cpuUsage();
  private server: http.Server | null = null;
  private wss: WebSocketServer | null = null;
  private started = false;
  private shuttingDown = false;
  private eventUnsub: { unsubscribe(): void } | null = null;
  private statusTimer: ReturnType<typeof setInterval> | null = null;
  private signalHandlersInstalled = false;

  constructor(kernel: Kernel, options?: RuntimeServerOptions) {
    this.kernel = kernel;
    this.host = options?.host ?? "0.0.0.0";
    this.port = options?.port ?? Number(process.env["ADOS_PORT"] ?? 3000);
    this.platformVersion = options?.platformVersion ?? PLATFORM_VERSION;
  }

  get url(): string {
    const host = this.host === "0.0.0.0" ? "localhost" : this.host;
    return `http://${host}:${this.port}`;
  }

  get isStarted(): boolean {
    return this.started;
  }

  async start(): Promise<void> {
    if (this.started) return;

    this.ensureDefaultWorkflow();
    this.bindEventBus();
    this.logs.push("info", "Runtime Server starting", "runtime");

    this.server = http.createServer((req, res) => {
      void this.handleHttp(req, res);
    });

    this.wss = new WebSocketServer({ server: this.server, path: "/ws" });
    this.wss.on("connection", (socket: WebSocket) => {
      this.logs.push("info", "WebSocket client connected", "runtime");
      socket.send(
        JSON.stringify({
          type: "welcome",
          platform: "ADOS",
          version: this.platformVersion,
          status: "READY",
        }),
      );
      socket.on("message", (raw) => {
        const text = String(raw);
        if (text === "ping") {
          socket.send(JSON.stringify({ type: "pong", at: new Date().toISOString() }));
        }
      });
    });

    await new Promise<void>((resolve, reject) => {
      const server = this.server;
      if (!server) {
        reject(new Error("HTTP server was not created"));
        return;
      }
      server.once("error", reject);
      server.listen(this.port, this.host, () => {
        server.off("error", reject);
        resolve();
      });
    });

    this.started = true;
    this.installSignalHandlers();
    this.statusTimer = setInterval(() => {
      this.broadcast({ type: "status", payload: this.buildStatus() });
    }, 2000);
    if (
      typeof this.statusTimer === "object" &&
      this.statusTimer !== null &&
      "unref" in this.statusTimer
    ) {
      (this.statusTimer as NodeJS.Timeout).unref();
    }

    this.logs.push("info", `Runtime listening on ${this.url}`, "runtime");
    console.log(`[ADOS Runtime] listening on ${this.url}`);

    const orch = this.getOrchestratorService();
    orch?.setStatusBroadcaster((message) => this.broadcast(message));
    const providers = this.getProviderGatewayService();
    providers?.setStatusBroadcaster((message) => this.broadcast(message));
    const chat = this.getChatBridgeService();
    chat?.setStatusBroadcaster((message) => this.broadcast(message));
    const voice = this.getVoiceService();
    voice?.setStatusBroadcaster((message) => this.broadcast(message));
    const mcp = this.getMCPService();
    mcp?.setStatusBroadcaster((message) => this.broadcast(message));
    mcp?.setRuntimeInvoker(async (method, path, body, search) =>
      this.dispatch(method, path, body, search),
    );
    const execution = this.getExecutionService();
    execution?.setStatusBroadcaster((message) => this.broadcast(message));
  }

  /** Public WS fan-out for platform modules (Orchestrator live status). */
  broadcastPublic(message: unknown): void {
    this.broadcast(message);
  }

  async stop(): Promise<void> {
    if (!this.started || this.shuttingDown) return;
    this.shuttingDown = true;
    this.logs.push("info", "Runtime graceful shutdown", "runtime");
    console.log("[ADOS Runtime] graceful shutdown…");

    if (this.statusTimer) {
      clearInterval(this.statusTimer);
      this.statusTimer = null;
    }
    this.eventUnsub?.unsubscribe();
    this.eventUnsub = null;
    this.getOrchestratorService()?.setStatusBroadcaster(null);
    this.getProviderGatewayService()?.setStatusBroadcaster(null);
    this.getChatBridgeService()?.setStatusBroadcaster(null);
    this.getVoiceService()?.setStatusBroadcaster(null);
    this.getMCPService()?.setStatusBroadcaster(null);
    this.getMCPService()?.setRuntimeInvoker(null);
    this.getExecutionService()?.setStatusBroadcaster(null);

    if (this.wss) {
      for (const client of this.wss.clients) {
        client.close(1001, "ADOS shutting down");
      }
      await new Promise<void>((resolve) => {
        this.wss?.close(() => resolve());
      });
      this.wss = null;
    }

    if (this.server) {
      await new Promise<void>((resolve, reject) => {
        this.server?.close((err) => (err ? reject(err) : resolve()));
      });
      this.server = null;
    }

    this.started = false;
    this.shuttingDown = false;
    console.log("[ADOS Runtime] stopped");
  }

  async handleRequestForTest(
    method: string,
    pathname: string,
    body?: unknown,
  ): Promise<{ status: number; body: unknown }> {
    return this.dispatch(method.toUpperCase(), pathname, body);
  }

  private ensureDefaultWorkflow(): void {
    if (!this.kernel.workflowEngine.getDefinition("enterprise.delivery")) {
      const def = createEnterpriseDeliveryWorkflow();
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
        this.kernel.workflowEngine.registerHandler(id, async () => true);
      }
      this.kernel.workflowEngine.register(def);
      this.logs.push("info", "Registered enterprise.delivery workflow", "workflow");
    }
  }

  private bindEventBus(): void {
    this.eventUnsub = this.kernel.enterpriseEventBus.subscribe("*", (event) => {
      const entry: EventEntry = {
        id: event.id,
        type: event.type,
        at: event.timestamp,
        payload: event.payload,
      };
      this.events.push(entry);
      if (this.events.length > 2_000) this.events.shift();
      this.broadcast({ type: "event", payload: entry });
    });
  }

  private broadcast(message: unknown): void {
    if (!this.wss) return;
    const raw = JSON.stringify(message);
    for (const client of this.wss.clients) {
      if (client.readyState === 1) client.send(raw);
    }
  }

  private async handleHttp(
    req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    this.applyCors(res);
    if ((req.method ?? "GET").toUpperCase() === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    try {
      const method = (req.method ?? "GET").toUpperCase();
      const host = req.headers.host ?? `localhost:${this.port}`;
      const url = new URL(req.url ?? "/", `http://${host}`);
      const body =
        method === "POST" || method === "PUT" || method === "PATCH"
          ? await readJsonBody(req)
          : undefined;
      const result = await this.dispatch(method, url.pathname, body, url.searchParams);
      this.sendJson(res, result.status, result.body);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.logs.push("error", message, "runtime");
      this.sendJson(res, 500, { error: message });
    }
  }

  private async dispatch(
    method: string,
    pathname: string,
    body?: unknown,
    search?: URLSearchParams,
  ): Promise<{ status: number; body: unknown }> {
    if (method === "GET" && pathname === "/health") {
      const payload: HealthResponse = { status: "ok" };
      return { status: 200, body: payload };
    }

    if (method === "GET" && pathname === "/status") {
      return { status: 200, body: this.buildStatus() };
    }

    if (method === "GET" && pathname === "/metrics") {
      return { status: 200, body: this.buildMetrics() };
    }

    if (method === "GET" && pathname === "/kernel") {
      return { status: 200, body: this.buildKernelInfo() };
    }

    if (method === "GET" && pathname === "/services") {
      const services = await this.listServices();
      return { status: 200, body: { services } };
    }

    if (method === "POST" && pathname.startsWith("/services/") && pathname.endsWith("/stop")) {
      const id = pathname.slice("/services/".length, -"/stop".length);
      return this.controlService(id, "stop");
    }

    if (method === "POST" && pathname.startsWith("/services/") && pathname.endsWith("/restart")) {
      const id = pathname.slice("/services/".length, -"/restart".length);
      return this.controlService(id, "restart");
    }

    if (method === "GET" && pathname === "/workflow") {
      const workflows: WorkflowListItem[] = this.kernel.workflowEngine
        .listDefinitions()
        .map((d) => ({
          id: d.id,
          name: d.name,
          version: d.version,
          start: d.start,
          steps: d.listSteps().length,
        }));
      const instances = this.kernel.workflowEngine.listInstances().map((i) => ({
        id: i.id,
        definitionId: i.definitionId,
        status: i.status,
        activeSteps: i.activeSteps,
        updatedAt: i.updatedAt,
      }));
      const collab = this.getCollaboration();
      return {
        status: 200,
        body: {
          workflows,
          instances,
          collaboration: collab?.list() ?? [],
          templates: collab?.listTemplates() ?? [],
          overview: collab?.overview() ?? null,
        },
      };
    }

    if (method === "POST" && pathname.startsWith("/workflow/") && pathname.endsWith("/run")) {
      const id = pathname.slice("/workflow/".length, -"/run".length);
      const instance = await this.kernel.workflowEngine.start(id);
      this.logs.push("info", `Workflow started: ${id} → ${instance.id}`, "workflow");
      return { status: 200, body: instance.toJSON() };
    }

    if (method === "POST" && pathname.startsWith("/workflow/instances/") && pathname.endsWith("/pause")) {
      const id = pathname.slice("/workflow/instances/".length, -"/pause".length);
      const instance = await this.kernel.workflowEngine.pause(id);
      this.logs.push("warn", `Workflow paused: ${id}`, "workflow");
      return { status: 200, body: instance.toJSON() };
    }

    if (method === "POST" && pathname.startsWith("/workflow/instances/") && pathname.endsWith("/resume")) {
      const id = pathname.slice("/workflow/instances/".length, -"/resume".length);
      const instance = await this.kernel.workflowEngine.resume(id);
      return { status: 200, body: instance.toJSON() };
    }

    if (method === "POST" && pathname.startsWith("/workflow/instances/") && pathname.endsWith("/cancel")) {
      const id = pathname.slice("/workflow/instances/".length, -"/cancel".length);
      const instance = await this.kernel.workflowEngine.cancel(id, "Cancelled from Control Center");
      return { status: 200, body: instance.toJSON() };
    }

    if (method === "GET" && pathname.startsWith("/workflow/instances/") && pathname.endsWith("/history")) {
      const id = pathname.slice("/workflow/instances/".length, -"/history".length);
      return { status: 200, body: { history: this.kernel.workflowEngine.history(id) } };
    }

    // --- Multi-Agent Collaboration Engine (ADOS OS 3.0) ---
    if (method === "POST" && pathname === "/workflow/start") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      const req = (body ?? {}) as {
        templateId?: string;
        name?: string;
        payload?: unknown;
        priority?: number;
      };
      try {
        const snap = await collab.start(req);
        this.logs.push("info", `Collaboration workflow started ${snap.id}`, "collaboration");
        return { status: 200, body: snap };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/workflow/history") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      return { status: 200, body: { workflows: collab.history() } };
    }

    if (method === "GET" && pathname === "/workflow/templates") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      return { status: 200, body: { templates: collab.listTemplates() } };
    }

    if (
      method === "GET" &&
      pathname.startsWith("/workflow/") &&
      pathname !== "/workflow/history" &&
      pathname !== "/workflow/templates" &&
      !pathname.includes("/instances/") &&
      !pathname.endsWith("/run")
    ) {
      const id = pathname.slice("/workflow/".length);
      if (id && !id.includes("/")) {
        const collab = this.getCollaboration();
        const snap = collab?.get(id);
        if (snap) return { status: 200, body: snap };
        // fallback kernel instance
        const instance = this.kernel.workflowEngine.getInstance(id);
        if (instance) return { status: 200, body: instance.toJSON() };
        return { status: 404, body: { error: `Workflow not found: ${id}` } };
      }
    }

    if (method === "POST" && pathname === "/workflow/pause") {
      const collab = this.getCollaboration();
      const req = (body ?? {}) as { id?: string };
      if (!collab || !req.id) {
        return { status: 400, body: { error: "id required" } };
      }
      return { status: 200, body: await collab.pause(req.id) };
    }

    if (method === "POST" && pathname === "/workflow/resume") {
      const collab = this.getCollaboration();
      const req = (body ?? {}) as { id?: string };
      if (!collab || !req.id) {
        return { status: 400, body: { error: "id required" } };
      }
      return { status: 200, body: await collab.resume(req.id) };
    }

    if (method === "POST" && pathname === "/workflow/cancel") {
      const collab = this.getCollaboration();
      const req = (body ?? {}) as { id?: string };
      if (!collab || !req.id) {
        return { status: 400, body: { error: "id required" } };
      }
      return { status: 200, body: await collab.cancel(req.id) };
    }

    if (method === "GET" && pathname === "/collaboration/overview") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      return { status: 200, body: collab.overview() };
    }

    if (method === "GET" && pathname === "/memory") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      return { status: 200, body: { memories: collab.listMemory() } };
    }

    if (method === "GET" && pathname.startsWith("/memory/")) {
      const collab = this.getCollaboration();
      const id = pathname.slice("/memory/".length);
      if (!collab || !id) {
        return { status: 404, body: { error: "Not found" } };
      }
      try {
        return { status: 200, body: collab.getContext(id) };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 404, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/timeline") {
      const collab = this.getCollaboration();
      if (!collab) {
        return { status: 503, body: { error: "Collaboration engine not available" } };
      }
      const workflowId = search?.get("workflowId") ?? undefined;
      const agentId = search?.get("agentId") ?? undefined;
      const limit = Number(search?.get("limit") ?? 200);
      return {
        status: 200,
        body: {
          events: collab.timeline.list({
            ...(workflowId ? { workflowId } : {}),
            ...(agentId ? { agentId } : {}),
            limit,
          }),
        },
      };
    }

    if (method === "GET" && pathname === "/queue") {
      const agents = this.listAgents();
      return {
        status: 200,
        body: {
          queues: agents.map((a) => ({
            agentId: a.id,
            name: a.name,
            status: a.status,
            queueLength: a.queueSize,
            runningTask: a.currentTask,
            avgResponseMs: a.responseTimeMs,
          })),
          totalQueued: agents.reduce((n, a) => n + a.queueSize, 0),
        },
      };
    }

    if (method === "GET" && pathname === "/tasks") {
      const collab = this.getCollaboration();
      const workflows = collab?.list() ?? [];
      const tasks = workflows.flatMap((w) =>
        w.steps.map((s) => ({
          workflowId: w.id,
          workflowName: w.name,
          stepId: s.id,
          agentId: s.agentId,
          status: s.status,
          durationMs: s.durationMs,
          error: s.error,
        })),
      );
      return {
        status: 200,
        body: {
          running: tasks.filter((t) => t.status === "running"),
          completed: tasks.filter((t) => t.status === "completed"),
          failed: tasks.filter((t) => t.status === "failed"),
          all: tasks,
        },
      };
    }

    if (method === "GET" && pathname === "/events") {
      const q = search?.get("q")?.toLowerCase();
      const limit = Number(search?.get("limit") ?? 100);
      let rows = [...this.events].reverse();
      if (q) rows = rows.filter((e) => e.type.toLowerCase().includes(q));
      return { status: 200, body: { events: rows.slice(0, limit) } };
    }

    if (method === "GET" && pathname === "/logs") {
      const level = search?.get("level") as "info" | "warn" | "error" | null;
      const q = search?.get("q") ?? undefined;
      const limit = Number(search?.get("limit") ?? 200);
      return {
        status: 200,
        body: {
          logs: this.logs.list({
            ...(level ? { level } : {}),
            ...(q ? { q } : {}),
            limit,
          }),
        },
      };
    }

    if (method === "GET" && pathname === "/agents") {
      const agents = this.listAgents();
      const orch = this.getOrchestrator()?.getStatus();
      return {
        status: 200,
        body: {
          agents,
          orchestrator: orch ?? null,
        },
      };
    }

    if (method === "GET" && pathname === "/agents/status") {
      const orch = this.getOrchestrator();
      if (!orch) {
        return { status: 503, body: { error: "AI Orchestrator not registered" } };
      }
      return { status: 200, body: orch.agentsStatus() };
    }

    if (method === "GET" && pathname === "/agents/logs") {
      const orch = this.getOrchestrator();
      if (!orch) {
        return { status: 503, body: { error: "AI Orchestrator not registered" } };
      }
      const agentId = search?.get("agentId") ?? undefined;
      const level = search?.get("level") as "info" | "warn" | "error" | null;
      const limit = Number(search?.get("limit") ?? 200);
      return {
        status: 200,
        body: {
          logs: orch.logs.list({
            ...(agentId ? { agentId } : {}),
            ...(level ? { level } : {}),
            limit,
          }),
        },
      };
    }

    if (method === "GET" && pathname === "/agents/metrics") {
      const orch = this.getOrchestrator();
      if (!orch) {
        return { status: 503, body: { error: "AI Orchestrator not registered" } };
      }
      return { status: 200, body: orch.aggregateMetrics() };
    }

    if (method === "POST" && pathname === "/agents/run") {
      const orch = this.getOrchestrator();
      if (!orch) {
        return { status: 503, body: { error: "AI Orchestrator not registered" } };
      }
      const req = (body ?? {}) as {
        agentId?: string;
        type?: string;
        task?: string;
        payload?: unknown;
        provider?: "local" | "cursor" | "openai" | "claude" | "github" | "telegram";
      };
      if (!req.agentId) {
        return { status: 400, body: { error: "agentId is required" } };
      }
      try {
        const result = await orch.runAgent(req.agentId, {
          ...(req.type !== undefined ? { type: req.type } : {}),
          ...(req.task !== undefined ? { task: req.task } : {}),
          ...(req.payload !== undefined ? { payload: req.payload } : {}),
          ...(req.provider !== undefined ? { provider: req.provider } : {}),
        });
        this.logs.push("info", `Agent run ${req.agentId} → ${result.ok}`, "orchestrator");
        return { status: 200, body: result };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/orchestrator/task") {
      const orch = this.getOrchestrator();
      if (!orch) {
        return { status: 503, body: { error: "AI Orchestrator not registered" } };
      }
      const req = (body ?? {}) as {
        task?: string;
        type?: string;
        payload?: unknown;
        preferredAgent?: string;
        capability?: string;
        provider?: "local" | "cursor" | "openai" | "claude" | "github" | "telegram";
      };
      try {
        const result = await orch.submitTask({
          ...(req.task !== undefined ? { task: req.task } : {}),
          ...(req.type !== undefined ? { type: req.type } : {}),
          ...(req.payload !== undefined ? { payload: req.payload } : {}),
          ...(req.preferredAgent !== undefined
            ? { preferredAgent: req.preferredAgent }
            : {}),
          ...(req.capability !== undefined ? { capability: req.capability } : {}),
          ...(req.provider !== undefined ? { provider: req.provider } : {}),
        });
        this.logs.push(
          "info",
          `Orchestrator task ${result.taskId} → ${result.agentId}`,
          "orchestrator",
        );
        return { status: 200, body: result };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/providers") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      return {
        status: 200,
        body: {
          gateway: gw.getStatus(),
          providers: gw.listProviders(),
          metrics: gw.aggregateMetrics(),
        },
      };
    }

    if (method === "GET" && pathname === "/providers/status") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      return {
        status: 200,
        body: {
          gateway: gw.getStatus(),
          providers: gw.listProviders().map((p) => ({
            id: p.id,
            name: p.name,
            status: p.status,
            connected: p.connected,
            health: p.health,
          })),
        },
      };
    }

    if (method === "GET" && pathname === "/providers/capabilities") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      return { status: 200, body: { capabilities: gw.capabilities() } };
    }

    if (method === "POST" && pathname === "/providers/connect") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      const req = (body ?? {}) as { providerId?: string };
      try {
        const providers = await gw.connect(req.providerId);
        this.logs.push(
          "info",
          `Provider connect ${req.providerId ?? "all"}`,
          "providers",
        );
        return { status: 200, body: { providers } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/providers/disconnect") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      const req = (body ?? {}) as { providerId?: string };
      try {
        const providers = await gw.disconnect(req.providerId);
        this.logs.push(
          "warn",
          `Provider disconnect ${req.providerId ?? "all"}`,
          "providers",
        );
        return { status: 200, body: { providers } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/providers/execute") {
      const gw = this.getProviderGateway();
      if (!gw) {
        return { status: 503, body: { error: "Provider Gateway not registered" } };
      }
      const req = (body ?? {}) as {
        providerId?: string;
        preferredAlias?: string;
        capability?: string;
        payload?: unknown;
      };
      if (!req.capability) {
        return { status: 400, body: { error: "capability is required" } };
      }
      try {
        const result = await gw.execute({
          ...(req.providerId !== undefined ? { providerId: req.providerId } : {}),
          ...(req.preferredAlias !== undefined
            ? { preferredAlias: req.preferredAlias }
            : {}),
          capability: req.capability,
          ...(req.payload !== undefined ? { payload: req.payload } : {}),
        });
        return { status: 200, body: result };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    // ── ChatGPT Bridge ──────────────────────────────────────────────
    if (method === "POST" && pathname === "/chat/task") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const req = (body ?? {}) as {
        prompt?: string;
        attachments?: Parameters<typeof bridge.createTask>[0]["attachments"];
        provider?: string;
        projectContext?: Parameters<typeof bridge.createTask>[0]["projectContext"];
        autoRun?: boolean;
        sessionId?: string;
      };
      if (!req.prompt?.trim()) {
        return { status: 400, body: { error: "prompt required" } };
      }
      try {
        const input: Parameters<typeof bridge.createTask>[0] = {
          prompt: req.prompt,
          autoRun: req.autoRun ?? false,
        };
        if (req.provider !== undefined) input.provider = req.provider;
        if (req.sessionId !== undefined) input.sessionId = req.sessionId;
        if (req.projectContext !== undefined) {
          input.projectContext = req.projectContext;
        }
        if (req.attachments !== undefined) input.attachments = req.attachments;
        const task = bridge.createTask(input);
        this.logs.push("info", `Chat task created: ${task.id}`, "chat");
        return { status: 200, body: { task } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/chat/run") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const req = (body ?? {}) as { taskId?: string };
      try {
        const task = await bridge.run(req.taskId);
        this.logs.push(
          "info",
          `Chat task ${task.id} → ${task.status}`,
          "chat",
        );
        return { status: 200, body: { task } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/chat/history") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const limit = Number(search?.get("limit") ?? 100);
      return { status: 200, body: { history: bridge.history.list(limit) } };
    }

    if (method === "GET" && pathname === "/chat/tasks") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const statusFilter = search?.get("status") ?? undefined;
      const snap = bridge.queue.snapshot();
      const tasks = statusFilter
        ? snap.tasks.filter((t) => t.status === statusFilter)
        : snap.tasks;
      return {
        status: 200,
        body: {
          queue: {
            total: snap.total,
            queued: snap.queued,
            running: snap.running,
            waiting: snap.waiting,
            review: snap.review,
            done: snap.done,
            failed: snap.failed,
            cancelled: snap.cancelled,
          },
          tasks,
        },
      };
    }

    if (method === "GET" && pathname === "/chat/session") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const id = search?.get("id") ?? undefined;
      try {
        return { status: 200, body: { session: bridge.sessions.get(id) } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 404, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/chat/status") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      return { status: 200, body: bridge.status() };
    }

    if (method === "POST" && pathname === "/chat/cancel") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const req = (body ?? {}) as { taskId?: string };
      if (!req.taskId) {
        return { status: 400, body: { error: "taskId required" } };
      }
      try {
        const task = await bridge.cancel(req.taskId);
        return { status: 200, body: { task } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/chat/rollback") {
      const bridge = this.getChatBridge();
      if (!bridge) {
        return { status: 503, body: { error: "ChatGPT Bridge not available" } };
      }
      const req = (body ?? {}) as { taskId?: string };
      if (!req.taskId) {
        return { status: 400, body: { error: "taskId required" } };
      }
      try {
        const task = await bridge.rollback(req.taskId);
        return { status: 200, body: { task } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    // ── Enterprise Voice Module ─────────────────────────────────────
    if (method === "POST" && pathname === "/voice/start") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      const req = (body ?? {}) as { language?: string };
      try {
        const session = await voice.start(
          req.language ? { language: req.language } : undefined,
        );
        this.logs.push("info", "Voice session started", "voice");
        return { status: 200, body: { session } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/voice/stop") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      const req = (body ?? {}) as { sessionId?: string };
      try {
        const session = await voice.stop(req.sessionId);
        this.logs.push("info", "Voice session stopped", "voice");
        return { status: 200, body: { session } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/voice/process") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      const req = (body ?? {}) as {
        text?: string;
        audioBase64?: string;
        language?: string;
        sessionId?: string;
        bypassWakeWord?: boolean;
        autoExecute?: boolean;
      };
      if (!req.text?.trim() && !req.audioBase64) {
        return {
          status: 400,
          body: { error: "text or audioBase64 required" },
        };
      }
      try {
        const input: Parameters<typeof voice.process>[0] = {};
        if (req.text !== undefined) input.text = req.text;
        if (req.audioBase64 !== undefined) input.audioBase64 = req.audioBase64;
        if (req.language !== undefined) input.language = req.language;
        if (req.sessionId !== undefined) input.sessionId = req.sessionId;
        if (req.bypassWakeWord !== undefined) {
          input.bypassWakeWord = req.bypassWakeWord;
        }
        if (req.autoExecute !== undefined) input.autoExecute = req.autoExecute;
        const result = await voice.process(input);
        this.logs.push(
          "info",
          `Voice ${result.intent} → ${result.command.status}`,
          "voice",
        );
        return { status: 200, body: result };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/voice/history") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      const limit = Number(search?.get("limit") ?? 100);
      return { status: 200, body: { history: voice.history(limit) } };
    }

    if (method === "GET" && pathname === "/voice/settings") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      return { status: 200, body: { settings: voice.getSettings() } };
    }

    if (method === "POST" && pathname === "/voice/settings") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      try {
        const settings = voice.updateSettings(
          (body ?? {}) as Parameters<typeof voice.updateSettings>[0],
        );
        return { status: 200, body: { settings } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/voice/status") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      return { status: 200, body: voice.status() };
    }

    if (method === "POST" && pathname === "/voice/pause") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      try {
        return { status: 200, body: { session: voice.pause() } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "POST" && pathname === "/voice/resume") {
      const voice = this.getVoiceGateway();
      if (!voice) {
        return { status: 503, body: { error: "Voice Module not available" } };
      }
      try {
        return { status: 200, body: { session: voice.resume() } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    // ── Enterprise MCP Gateway ──────────────────────────────────────
    if (method === "GET" && pathname === "/mcp/status") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      return { status: 200, body: mcp.status() };
    }

    if (method === "GET" && pathname === "/mcp/tools") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      return {
        status: 200,
        body: {
          tools: mcp.listTools().map((t) => ({
            name: t.name,
            description: t.description,
            permission: t.permission,
          })),
        },
      };
    }

    if (method === "GET" && pathname === "/mcp/resources") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      return {
        status: 200,
        body: {
          resources: mcp.listResources().map((r) => ({
            uri: r.uri,
            name: r.name,
            description: r.description,
            permission: r.permission,
          })),
        },
      };
    }

    if (method === "GET" && pathname === "/mcp/prompts") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      return {
        status: 200,
        body: {
          prompts: mcp.listPrompts().map((p) => ({
            name: p.name,
            description: p.description,
            permission: p.permission,
          })),
        },
      };
    }

    if (method === "POST" && pathname === "/mcp/rpc") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      const tokenHeader = mcp.getConfig().authentication.tokenHeader;
      // Token may arrive via body for Control Center convenience
      const req = (body ?? {}) as {
        jsonrpc?: string;
        id?: string | number | null;
        method?: string;
        params?: unknown;
        token?: string;
      };
      if (!req.method) {
        return { status: 400, body: { error: "JSON-RPC method required" } };
      }
      const result = await mcp.handleRpc(
        {
          jsonrpc: "2.0",
          id: req.id ?? null,
          method: req.method,
          ...(req.params !== undefined ? { params: req.params } : {}),
        },
        { token: req.token ?? null, clientId: "runtime-http" },
      );
      void tokenHeader;
      return { status: 200, body: result };
    }

    if (method === "POST" && pathname === "/mcp/connect") {
      const mcp = this.getMCPGateway();
      if (!mcp) {
        return { status: 503, body: { error: "MCP Gateway not available" } };
      }
      const req = (body ?? {}) as { clientId?: string; token?: string };
      try {
        const session = mcp.connectClient({
          clientId: req.clientId ?? "control-center",
          token: req.token ?? mcp.getConfig().authentication.defaultAdminToken,
          transport: "http",
        });
        return { status: 200, body: { session } };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 401, body: { error: message } };
      }
    }

    // ── Enterprise Execution Planner ────────────────────────────────
    if (method === "POST" && pathname === "/execution/plan") {
      const planner = this.getExecutionPlanner();
      if (!planner) {
        return {
          status: 503,
          body: { error: "Execution Planner not available" },
        };
      }
      const req = (body ?? {}) as {
        specification?: unknown;
        autoRun?: boolean;
        mission?: string;
        objective?: string;
        requirements?: string[];
        files?: string[];
        modules?: string[];
        tests?: string[];
        acceptanceCriteria?: string[];
        raw?: string;
      };
      const input =
        req.specification ??
        (req.mission || req.objective || req.raw
          ? {
              mission: req.mission ?? "Mission",
              objective: req.objective ?? req.mission ?? "Objective",
              requirements: req.requirements ?? [],
              files: req.files ?? [],
              modules: req.modules ?? [],
              tests: req.tests ?? [],
              acceptanceCriteria: req.acceptanceCriteria ?? [],
              ...(req.raw !== undefined ? { raw: req.raw } : {}),
            }
          : null);
      if (!input) {
        return {
          status: 400,
          body: { error: "specification (or mission fields) required" },
        };
      }
      try {
        const result = await planner.plan(
          input as Parameters<typeof planner.plan>[0],
          req.autoRun !== undefined ? { autoRun: req.autoRun } : undefined,
        );
        this.logs.push(
          "info",
          `Execution plan ${result.plan.id} → ${result.plan.status}`,
          "execution",
        );
        return { status: 200, body: result };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return { status: 400, body: { error: message } };
      }
    }

    if (method === "GET" && pathname === "/execution/status") {
      const planner = this.getExecutionPlanner();
      if (!planner) {
        return {
          status: 503,
          body: { error: "Execution Planner not available" },
        };
      }
      return { status: 200, body: planner.status() };
    }

    if (method === "GET" && pathname === "/execution/history") {
      const planner = this.getExecutionPlanner();
      if (!planner) {
        return {
          status: 503,
          body: { error: "Execution Planner not available" },
        };
      }
      const limit = Number(search?.get("limit") ?? 50);
      return { status: 200, body: { history: planner.listHistory(limit) } };
    }

    if (method === "GET" && pathname === "/execution/report") {
      const planner = this.getExecutionPlanner();
      if (!planner) {
        return {
          status: 503,
          body: { error: "Execution Planner not available" },
        };
      }
      const planId = search?.get("planId") ?? undefined;
      const report = planner.getReport(planId);
      if (!report) {
        return { status: 404, body: { error: "No execution report available" } };
      }
      return { status: 200, body: { report } };
    }

    if (method === "GET" && pathname === "/") {
      return {
        status: 200,
        body: {
          name: "ADOS Enterprise Operating System",
          version: this.platformVersion,
          endpoints: [
            "/health",
            "/status",
            "/metrics",
            "/kernel",
            "/services",
            "/workflow",
            "/events",
            "/logs",
            "/agents",
            "/agents/status",
            "/agents/logs",
            "/agents/metrics",
            "/agents/run",
            "/orchestrator/task",
            "/workflow/start",
            "/workflow/history",
            "/workflow/templates",
            "/collaboration/overview",
            "/memory",
            "/timeline",
            "/queue",
            "/tasks",
            "/providers",
            "/providers/status",
            "/providers/capabilities",
            "/providers/connect",
            "/providers/disconnect",
            "/providers/execute",
            "/chat/task",
            "/chat/run",
            "/chat/history",
            "/chat/tasks",
            "/chat/session",
            "/chat/status",
            "/voice/start",
            "/voice/stop",
            "/voice/process",
            "/voice/history",
            "/voice/settings",
            "/voice/status",
            "/mcp/status",
            "/mcp/tools",
            "/mcp/resources",
            "/mcp/prompts",
            "/execution/plan",
            "/execution/status",
            "/execution/history",
            "/execution/report",
            "/ws",
          ],
        },
      };
    }

    void body;
    return { status: 404, body: { error: "Not found", path: pathname } };
  }

  private buildStatus(): StatusResponse {
    const services = this.kernel.registry.list().length;
    const kernelOk = this.kernel.getState() === "Started";
    const orch = this.getOrchestrator();
    const orchStatus = orch?.getStatus();
    const gw = this.getProviderGateway();
    const gwStatus = gw?.getStatus();
    const chat = this.getChatBridge();
    const voice = this.getVoiceGateway();
    const mcp = this.getMCPGateway();
    const execution = this.getExecutionPlanner();
    return {
      version: this.platformVersion,
      kernel: "OK",
      eventBus: "OK",
      serviceMesh: "OK",
      workflowEngine: "OK",
      runtimeServer: "OK",
      orchestrator: orch ? "OK" : "DOWN",
      providerGateway: gw ? "OK" : "DOWN",
      chatBridge: chat ? "OK" : "DOWN",
      voice: voice ? "OK" : "DOWN",
      mcp: mcp ? "OK" : "DOWN",
      execution: execution ? "OK" : "DOWN",
      services,
      agents: orchStatus?.agents ?? 0,
      providers: gwStatus?.providers ?? 0,
      providersConnected: gwStatus?.connected ?? 0,
      runningTasks: orchStatus?.runningTasks ?? 0,
      queueSize: orchStatus?.queueSize ?? 0,
      systemStatus:
        kernelOk &&
        this.started &&
        orch &&
        gw &&
        chat &&
        voice &&
        mcp &&
        execution
          ? "READY"
          : "DEGRADED",
    };
  }

  private buildMetrics(): MetricsResponse {
    const mem = process.memoryUsage();
    const cpu = process.cpuUsage(this.cpuBaseline);
    return {
      uptimeSec: Math.floor((Date.now() - this.bootStartedAt) / 1000),
      memory: {
        rss: mem.rss,
        heapUsed: mem.heapUsed,
        heapTotal: mem.heapTotal,
        external: mem.external,
      },
      cpu: {
        userMicros: cpu.user,
        systemMicros: cpu.system,
      },
      startedAt: this.bootStartedIso,
    };
  }

  private buildKernelInfo(): KernelInfoResponse {
    const services = this.kernel.registry.list();
    return {
      version: this.kernel.version,
      platformVersion: this.platformVersion,
      state: this.kernel.getState(),
      startedAt: this.bootStartedIso,
      uptimeMs: Date.now() - this.bootStartedAt,
      modules: services.map((s) => s.id),
      services: services.length,
      health: this.kernel.getState() === "Started" ? "healthy" : "degraded",
    };
  }

  private async listServices(): Promise<ServiceListItem[]> {
    const rows: ServiceListItem[] = [];
    for (const s of this.kernel.registry.list()) {
      const health = await Promise.resolve(s.health());
      const mesh = this.kernel.serviceMesh.discovery.get(s.id);
      rows.push({
        id: s.id,
        version: s.version,
        kind: s.kind,
        lifecycle: s.getLifecycleState(),
        uptimeMs: s.uptimeMs(),
        health: health.status,
        dependencies: (mesh?.dependencies ?? [])
          .map((d) => d.serviceId ?? d.capability ?? "")
          .filter(Boolean),
      });
    }
    return rows;
  }

  private async controlService(
    id: string,
    action: "stop" | "restart",
  ): Promise<{ status: number; body: unknown }> {
    if (!this.kernel.registry.exists(id)) {
      return { status: 404, body: { error: `Service not found: ${id}` } };
    }
    const service = this.kernel.registry.resolve(id);
    try {
      if (action === "stop") {
        await service.stop();
        this.logs.push("warn", `Service stopped: ${id}`, "services");
      } else {
        const state = service.getLifecycleState();
        if (state === "Started" || state === "Paused") await service.stop();
        if (service.getLifecycleState() === "Stopped") await service.initialize();
        await service.start();
        this.logs.push("info", `Service restarted: ${id}`, "services");
      }
      const health = await Promise.resolve(service.health());
      return {
        status: 200,
        body: {
          id,
          lifecycle: service.getLifecycleState(),
          health: health.status,
        },
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.logs.push("error", `Service ${action} failed (${id}): ${message}`, "services");
      return { status: 500, body: { error: message } };
    }
  }

  private listAgents(): AgentListItem[] {
    const orch = this.getOrchestrator();
    if (orch) {
      return orch.listAgents().map((s) => ({
        id: s.id,
        name: s.name,
        role: s.role,
        status: s.status,
        provider: s.provider,
        memory: s.memory,
        skills: s.skills,
        version: s.version,
        lastExecution: s.lastExecution,
        currentTask: s.currentTask,
        queueSize: s.queueSize,
        runningTasks: s.runningTasks,
        responseTimeMs: s.responseTimeMs,
        health: s.health.status,
        metrics: {
          tasksCompleted: s.metrics.tasksCompleted,
          successes: s.metrics.successes,
          errors: s.metrics.errors,
          avgResponseTimeMs: s.metrics.avgResponseTimeMs,
          load: s.metrics.load,
        },
      }));
    }

    // Fallback: plugin host ids only (pre-orchestrator)
    const pluginHost = this.kernel.registry.exists("ados.plugin_host")
      ? this.kernel.registry.resolve("ados.plugin_host")
      : null;
    const pluginIds =
      pluginHost && "listPluginIds" in pluginHost
        ? (
            pluginHost as { listPluginIds: () => readonly string[] }
          ).listPluginIds()
        : [];

    return pluginIds.map((id) => ({
      id,
      name: id,
      role: "plugin-agent",
      status: "Idle",
      provider: "ados.plugin_host",
      memory: "shared",
      currentTask: null,
      queueSize: 0,
      runningTasks: 0,
      responseTimeMs: 0,
      health: "OK",
      metrics: {
        tasksCompleted: 0,
        successes: 0,
        errors: 0,
        avgResponseTimeMs: 0,
        load: 0,
      },
    }));
  }

  private getOrchestratorService(): OrchestratorService | null {
    if (!this.kernel.registry.exists(ORCHESTRATOR_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      ORCHESTRATOR_SERVICE_ID,
    ) as unknown as OrchestratorService;
  }

  private getOrchestrator() {
    return this.getOrchestratorService()?.orchestrator ?? null;
  }

  private getCollaboration() {
    return this.getOrchestratorService()?.collaboration ?? null;
  }

  private getProviderGatewayService(): ProviderGatewayService | null {
    if (!this.kernel.registry.exists(PROVIDER_GATEWAY_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      PROVIDER_GATEWAY_SERVICE_ID,
    ) as unknown as ProviderGatewayService;
  }

  private getProviderGateway() {
    return this.getProviderGatewayService()?.gateway ?? null;
  }

  private getChatBridgeService(): ChatBridgeService | null {
    if (!this.kernel.registry.exists(CHAT_BRIDGE_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      CHAT_BRIDGE_SERVICE_ID,
    ) as unknown as ChatBridgeService;
  }

  private getChatBridge() {
    return this.getChatBridgeService()?.bridge ?? null;
  }

  private getVoiceService(): VoiceService | null {
    if (!this.kernel.registry.exists(VOICE_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      VOICE_SERVICE_ID,
    ) as unknown as VoiceService;
  }

  private getVoiceGateway() {
    return this.getVoiceService()?.gateway ?? null;
  }

  private getMCPService(): MCPService | null {
    if (!this.kernel.registry.exists(MCP_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      MCP_SERVICE_ID,
    ) as unknown as MCPService;
  }

  private getMCPGateway() {
    return this.getMCPService()?.gateway ?? null;
  }

  private getExecutionService(): ExecutionService | null {
    if (!this.kernel.registry.exists(EXECUTION_SERVICE_ID)) return null;
    return this.kernel.registry.resolve(
      EXECUTION_SERVICE_ID,
    ) as unknown as ExecutionService;
  }

  private getExecutionPlanner() {
    return this.getExecutionService()?.planner ?? null;
  }

  /** Sprint 37.2 — CORS fail-closed in production/staging unless ADOS_CORS_ORIGIN is set. */
  private corsOrigin(): string | null {
    const configured = (process.env["ADOS_CORS_ORIGIN"] || "").trim();
    if (configured === "off" || configured === "none") return null;
    if (configured) return configured;
    const env = (
      process.env["ENVIRONMENT"] ||
      process.env["NODE_ENV"] ||
      "development"
    ).toLowerCase();
    if (env === "production" || env === "prod" || env === "staging") {
      return null;
    }
    return "*";
  }

  private applyCors(res: ServerResponse): void {
    const origin = this.corsOrigin();
    if (origin) {
      res.setHeader("Access-Control-Allow-Origin", origin);
    }
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  }

  private sendJson(
    res: ServerResponse,
    status: number,
    body: unknown,
  ): void {
    const payload = JSON.stringify(body);
    const headers: Record<string, string | number> = {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Length": Buffer.byteLength(payload),
    };
    const origin = this.corsOrigin();
    if (origin) {
      headers["Access-Control-Allow-Origin"] = origin;
    }
    res.writeHead(status, headers);
    res.end(payload);
  }

  private installSignalHandlers(): void {
    if (this.signalHandlersInstalled) return;
    if (process.env["VITEST"] === "true" || process.env["ADOS_NO_SIGNALS"] === "1") {
      return;
    }
    this.signalHandlersInstalled = true;
    const onSignal = (signal: string) => {
      console.log(`[ADOS Runtime] received ${signal}`);
      void this.shutdownProcess();
    };
    process.once("SIGINT", () => onSignal("SIGINT"));
    process.once("SIGTERM", () => onSignal("SIGTERM"));
  }

  private async shutdownProcess(): Promise<void> {
    try {
      await this.stop();
      await this.kernel.dispose();
      process.exit(0);
    } catch (error) {
      console.error("[ADOS Runtime] shutdown error:", error);
      process.exit(1);
    }
  }
}

export function createRuntimeServer(
  kernel: Kernel,
  options?: RuntimeServerOptions,
): RuntimeServer {
  return new RuntimeServer(kernel, options);
}

async function readJsonBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  if (chunks.length === 0) return undefined;
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw.trim()) return undefined;
  return JSON.parse(raw) as unknown;
}
