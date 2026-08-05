import type { IAgent } from "./interfaces/IAgent.js";
import type {
  AgentCapability,
  AgentHealth,
  AgentLiveStatus,
  AgentMetrics,
  AgentSnapshot,
  AgentTaskInput,
  AgentTaskResult,
  ProviderId,
} from "./types.js";

export interface BaseAgentOptions {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly provider?: ProviderId;
  readonly memory?: string;
  readonly version?: string;
  readonly skills?: readonly string[];
  readonly capabilities: readonly AgentCapability[];
  readonly latencyMs?: { min: number; max: number };
}

/**
 * Shared agent runtime: serial queue, metrics, live status.
 */
export abstract class BaseAgent implements IAgent {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly provider: ProviderId;
  readonly memory: string;
  readonly version: string;
  readonly skills: readonly string[];

  private readonly caps: readonly AgentCapability[];
  private readonly latency: { min: number; max: number };
  private live: AgentLiveStatus = "Idle";
  private currentTask: string | null = null;
  private queueDepth = 0;
  private running = 0;
  private chain: Promise<void> = Promise.resolve();
  private tasksCompleted = 0;
  private successes = 0;
  private errors = 0;
  private totalDurationMs = 0;
  private lastDurationMs = 0;
  private lastExecution: string | null = null;
  private offline = false;

  constructor(options: BaseAgentOptions) {
    this.id = options.id;
    this.name = options.name;
    this.role = options.role;
    this.provider = options.provider ?? "local";
    this.memory = options.memory ?? "shared-workflow";
    this.version = options.version ?? "3.0.0";
    this.skills = options.skills ?? [];
    this.caps = options.capabilities;
    this.latency = options.latencyMs ?? { min: 40, max: 120 };
  }

  capabilities(): readonly AgentCapability[] {
    return this.caps;
  }

  status(): AgentLiveStatus {
    if (this.offline) return "Offline";
    return this.live;
  }

  health(): AgentHealth {
    const checkedAt = new Date().toISOString();
    if (this.offline || this.live === "Offline") {
      return { status: "DOWN", message: "Agent offline", checkedAt };
    }
    if (this.live === "Error") {
      return { status: "DEGRADED", message: "Last task failed", checkedAt };
    }
    return { status: "OK", checkedAt };
  }

  metrics(): AgentMetrics {
    return {
      tasksCompleted: this.tasksCompleted,
      successes: this.successes,
      errors: this.errors,
      avgResponseTimeMs:
        this.tasksCompleted === 0
          ? 0
          : Math.round(this.totalDurationMs / this.tasksCompleted),
      load: this.running + this.queueDepth,
      queueSize: this.queueDepth,
      runningTasks: this.running,
    };
  }

  snapshot(): AgentSnapshot {
    return {
      id: this.id,
      name: this.name,
      role: this.role,
      provider: this.provider,
      skills: this.skills,
      status: this.status(),
      memory: this.memory,
      currentTask: this.currentTask,
      queueSize: this.queueDepth,
      runningTasks: this.running,
      responseTimeMs: this.lastDurationMs,
      lastExecution: this.lastExecution,
      version: this.version,
      health: this.health(),
      metrics: this.metrics(),
      capabilities: this.caps,
    };
  }

  setOffline(value: boolean): void {
    this.offline = value;
    this.live = value ? "Offline" : this.running > 0 ? "Running" : "Idle";
  }

  execute(input: AgentTaskInput): Promise<AgentTaskResult> {
    if (this.offline) {
      return Promise.resolve(this.fail(input, "Agent offline", 0));
    }

    this.queueDepth += 1;
    this.live = this.running > 0 || this.queueDepth > 1 ? "Busy" : "Waiting";

    const run = async (): Promise<AgentTaskResult> => {
      this.queueDepth = Math.max(0, this.queueDepth - 1);
      this.running += 1;
      this.live = "Running";
      this.currentTask = `${input.type}:${input.taskId}`;
      const started = Date.now();
      const provider = input.provider ?? this.provider;

      try {
        await sleep(rand(this.latency.min, this.latency.max));
        const output = await this.handle(input, provider);
        const durationMs = Date.now() - started;
        this.recordSuccess(durationMs);
        return {
          taskId: input.taskId,
          agentId: this.id,
          ok: true,
          output,
          durationMs,
          provider,
          completedAt: new Date().toISOString(),
        };
      } catch (error) {
        const durationMs = Date.now() - started;
        const message = error instanceof Error ? error.message : String(error);
        this.recordError(durationMs);
        return this.fail(input, message, durationMs, provider);
      } finally {
        this.running = Math.max(0, this.running - 1);
        this.currentTask = null;
        this.lastExecution = new Date().toISOString();
        if (!this.offline) {
          this.live =
            this.running > 0
              ? "Running"
              : this.queueDepth > 0
                ? "Busy"
                : "Idle";
        }
      }
    };

    const result = this.chain.then(run, run);
    this.chain = result.then(
      () => undefined,
      () => undefined,
    );
    return result;
  }

  protected abstract handle(
    input: AgentTaskInput,
    provider: ProviderId,
  ): Promise<unknown> | unknown;

  private fail(
    input: AgentTaskInput,
    message: string,
    durationMs: number,
    provider?: ProviderId,
  ): AgentTaskResult {
    return {
      taskId: input.taskId,
      agentId: this.id,
      ok: false,
      output: null,
      error: message,
      durationMs,
      provider: provider ?? this.provider,
      completedAt: new Date().toISOString(),
    };
  }

  private recordSuccess(durationMs: number): void {
    this.tasksCompleted += 1;
    this.successes += 1;
    this.totalDurationMs += durationMs;
    this.lastDurationMs = durationMs;
  }

  private recordError(durationMs: number): void {
    this.tasksCompleted += 1;
    this.errors += 1;
    this.totalDurationMs += durationMs;
    this.lastDurationMs = durationMs;
    this.live = "Error";
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function rand(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1));
}
