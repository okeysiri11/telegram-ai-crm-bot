import { AgentLogBuffer } from "./AgentLogBuffer.js";
import { AgentRegistry } from "./AgentRegistry.js";
import { createBuiltinAgents } from "./agents/builtin.js";
import type { IAgent } from "./interfaces/IAgent.js";
import type { ProviderGatewayPort } from "./interfaces/ProviderGatewayPort.js";
import type {
  AgentLiveStatus,
  AgentSnapshot,
  AgentTaskInput,
  AgentTaskResult,
  OrchestratorStatus,
  OrchestratorTaskRequest,
  OrchestratorTaskResponse,
  ProviderId,
} from "./types.js";

export type OrchestratorListener = (event: {
  type: "agent.status" | "agent.task" | "agent.log";
  payload: unknown;
}) => void;

/**
 * Central brain — all agent communication routes through here.
 * External AI calls go only through Provider Gateway (never direct).
 */
export class AiOrchestrator {
  readonly registry = new AgentRegistry();
  readonly logs = new AgentLogBuffer();
  private readonly listeners = new Set<OrchestratorListener>();
  private started = false;
  private taskSeq = 0;
  private providerGateway: ProviderGatewayPort | null = null;

  /** Wire Provider Gateway — required for production provider selection. */
  setProviderGateway(gateway: ProviderGatewayPort | null): void {
    this.providerGateway = gateway;
  }

  start(registerBuiltins = true): void {
    if (this.started) return;
    if (registerBuiltins && this.registry.list().length === 0) {
      for (const agent of createBuiltinAgents()) {
        this.registry.register(agent);
        this.logs.push({
          agentId: agent.id,
          level: "info",
          message: `Registered ${agent.name}`,
        });
      }
    }
    this.started = true;
    this.logs.push({
      agentId: "ados.orchestrator",
      level: "info",
      message: "AI Orchestrator started",
    });
    this.emit("agent.status", this.getStatus());
  }

  stop(): void {
    this.started = false;
    this.logs.push({
      agentId: "ados.orchestrator",
      level: "info",
      message: "AI Orchestrator stopped",
    });
  }

  on(listener: OrchestratorListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getStatus(): OrchestratorStatus {
    const snaps = this.registry.snapshots();
    const runningTasks = snaps.reduce((n, s) => n + s.runningTasks, 0);
    const queueSize = snaps.reduce((n, s) => n + s.queueSize, 0);
    const unhealthy = snaps.filter((s) => s.health.status !== "OK").length;
    let liveStatus: AgentLiveStatus | "Ready" = "Ready";
    if (runningTasks > 0) liveStatus = "Running";
    else if (queueSize > 0) liveStatus = "Busy";
    else if (unhealthy === snaps.length && snaps.length > 0) liveStatus = "Error";

    return {
      id: "ados.orchestrator",
      name: "AI Orchestrator",
      health: unhealthy === 0 ? "OK" : unhealthy < snaps.length ? "DEGRADED" : "DOWN",
      agents: snaps.length,
      runningTasks,
      queueSize,
      liveStatus,
    };
  }

  listAgents(): AgentSnapshot[] {
    return this.registry.snapshots();
  }

  agentsStatus(): {
    orchestrator: OrchestratorStatus;
    agents: AgentSnapshot[];
  } {
    return {
      orchestrator: this.getStatus(),
      agents: this.listAgents(),
    };
  }

  /** Direct run against a specific agent (still via Orchestrator). */
  async runAgent(
    agentId: string,
    body: {
      type?: string;
      task?: string;
      payload?: unknown;
      provider?: ProviderId;
    },
  ): Promise<AgentTaskResult> {
    const agent = this.registry.require(agentId);
    const taskId = this.nextTaskId();
    const input: AgentTaskInput = {
      taskId,
      type: body.type ?? body.task ?? "manual",
      payload: body.payload ?? { task: body.task },
      ...(body.provider !== undefined ? { provider: body.provider } : {}),
    };
    return this.executeOn(agent, input);
  }

  /** Route a platform task to the best agent. */
  async submitTask(
    request: OrchestratorTaskRequest,
  ): Promise<OrchestratorTaskResponse> {
    const agent = this.resolveAgent(request);
    const taskId = this.nextTaskId();
    const input: AgentTaskInput = {
      taskId,
      type: request.type ?? request.task ?? "generic",
      payload: request.payload ?? { task: request.task },
      ...(request.provider !== undefined ? { provider: request.provider } : {}),
    };

    this.logs.push({
      agentId: "ados.orchestrator",
      level: "info",
      message: `Routed task ${taskId} → ${agent.id}`,
      taskId,
      meta: { capability: request.capability, preferred: request.preferredAgent },
    });

    const result = await this.executeOn(agent, input);
    return {
      taskId,
      agentId: agent.id,
      status: result.ok ? "completed" : "failed",
      result,
      ...(result.error !== undefined ? { error: result.error } : {}),
    };
  }

  aggregateMetrics(): {
    tasksCompleted: number;
    successes: number;
    errors: number;
    avgResponseTimeMs: number;
    agents: Record<string, AgentSnapshot["metrics"]>;
  } {
    const snaps = this.listAgents();
    let tasksCompleted = 0;
    let successes = 0;
    let errors = 0;
    let totalWeighted = 0;
    const agents: Record<string, AgentSnapshot["metrics"]> = {};
    for (const s of snaps) {
      agents[s.id] = s.metrics;
      tasksCompleted += s.metrics.tasksCompleted;
      successes += s.metrics.successes;
      errors += s.metrics.errors;
      totalWeighted += s.metrics.avgResponseTimeMs * s.metrics.tasksCompleted;
    }
    return {
      tasksCompleted,
      successes,
      errors,
      avgResponseTimeMs:
        tasksCompleted === 0 ? 0 : Math.round(totalWeighted / tasksCompleted),
      agents,
    };
  }

  private resolveAgent(request: OrchestratorTaskRequest): IAgent {
    if (request.preferredAgent) {
      return this.registry.require(request.preferredAgent);
    }
    if (request.capability) {
      const byCap = this.registry.findByCapability(request.capability);
      if (byCap) return byCap;
    }
    const type = (request.type ?? request.task ?? "").toLowerCase();
    const map: Array<[RegExp, string]> = [
      [/code|dev|implement|fix|api/, "agent.developer"],
      [/business|ops|strategy|crm|sales/, "agent.business"],
      [/research|analyze|study/, "agent.research"],
      [/architect|design|adr/, "agent.architect"],
      [/review|approve/, "agent.reviewer"],
      [/qa|test|validate/, "agent.qa"],
      [/automat|deploy|release|pipeline/, "agent.automation"],
    ];
    for (const [re, id] of map) {
      if (re.test(type)) return this.registry.require(id);
    }
    return this.registry.require("agent.developer");
  }

  private async executeOn(
    agent: IAgent,
    input: AgentTaskInput,
  ): Promise<AgentTaskResult> {
    this.emit("agent.status", {
      agentId: agent.id,
      status: "Running",
      taskId: input.taskId,
    });
    this.logs.push({
      agentId: agent.id,
      level: "info",
      message: `Executing ${input.type}`,
      taskId: input.taskId,
    });

    let providerResult: unknown = null;
    let resolvedProvider: ProviderId = input.provider ?? agent.provider;

    if (this.providerGateway) {
      const selected = this.providerGateway.selectProvider({
        preferredAlias: String(input.provider ?? agent.provider),
        capability: capabilityForAgent(agent, input.type),
      });
      this.logs.push({
        agentId: agent.id,
        level: "info",
        message: `Provider Gateway selected ${selected.id} (${selected.name})`,
        taskId: input.taskId,
      });
      const gw = await this.providerGateway.execute({
        preferredAlias: String(input.provider ?? agent.provider),
        capability: capabilityForAgent(agent, input.type),
        payload: {
          taskId: input.taskId,
          type: input.type,
          agentId: agent.id,
          input: input.payload,
        },
      });
      providerResult = gw.output;
      resolvedProvider = aliasFromProviderId(gw.providerId);
      if (!gw.ok) {
        this.logs.push({
          agentId: agent.id,
          level: "error",
          message: `Provider error: ${gw.error ?? "unknown"}`,
          taskId: input.taskId,
        });
      }
    }

    const result = await agent.execute({
      ...input,
      provider: resolvedProvider,
      payload: {
        ...(typeof input.payload === "object" && input.payload !== null
          ? (input.payload as Record<string, unknown>)
          : { value: input.payload }),
        providerResult,
      },
    });

    this.logs.push({
      agentId: agent.id,
      level: result.ok ? "info" : "error",
      message: result.ok
        ? `Completed in ${result.durationMs}ms via ${result.provider}`
        : `Failed: ${result.error ?? "unknown"}`,
      taskId: input.taskId,
      meta: { durationMs: result.durationMs, ok: result.ok, providerResult },
    });
    this.emit("agent.task", result);
    this.emit("agent.status", {
      agentId: agent.id,
      status: agent.status(),
      snapshot: agent.snapshot(),
      orchestrator: this.getStatus(),
    });
    return result;
  }

  private nextTaskId(): string {
    this.taskSeq += 1;
    return `task_${Date.now().toString(36)}_${this.taskSeq}`;
  }

  private emit(
    type: "agent.status" | "agent.task" | "agent.log",
    payload: unknown,
  ): void {
    for (const listener of this.listeners) {
      try {
        listener({ type, payload });
      } catch {
        /* ignore listener errors */
      }
    }
  }
}

function capabilityForAgent(agent: IAgent, type: string): string {
  const caps = agent.capabilities();
  if (caps[0]) return caps[0].id;
  if (/code|dev|implement/.test(type)) return "code.complete";
  if (/search|repo|pr/.test(type)) return "search";
  return "chat";
}

function aliasFromProviderId(id: string): ProviderId {
  if (id.includes("cursor")) return "cursor";
  if (id.includes("openai")) return "openai";
  if (id.includes("claude")) return "claude";
  if (id.includes("github")) return "github";
  return "local";
}

export function createAiOrchestrator(): AiOrchestrator {
  return new AiOrchestrator();
}
