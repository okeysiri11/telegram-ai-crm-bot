import type { AiOrchestrator } from "@ados/orchestrator";
import {
  ExecutionPlanner,
  createExecutionPlanner,
} from "./ExecutionPlanner.js";

type LifecycleState =
  | "Created"
  | "Initialized"
  | "Started"
  | "Paused"
  | "Stopped"
  | "Disposed";

type HealthStatus =
  | "healthy"
  | "degraded"
  | "unhealthy"
  | "unknown"
  | "starting"
  | "stopped";

export interface ExecutionServiceDeps {
  readonly orchestrator: AiOrchestrator;
  readonly autoRun?: boolean;
}

/**
 * Kernel registry adapter — ados.execution
 */
export class ExecutionService {
  readonly id = "ados.execution";
  readonly version = "4.3.0";
  readonly kind = "extension" as const;

  readonly planner: ExecutionPlanner;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;

  constructor(deps: ExecutionServiceDeps) {
    this.planner = createExecutionPlanner({
      orchestrator: deps.orchestrator,
      ...(deps.autoRun !== undefined ? { autoRun: deps.autoRun } : {}),
    });
  }

  setStatusBroadcaster(fn: ((message: unknown) => void) | null): void {
    this.statusBroadcaster = fn;
  }

  getLifecycleState(): LifecycleState {
    return this.state;
  }

  uptimeMs(): number {
    if (this.startedAt === null || this.state !== "Started") return 0;
    return Date.now() - this.startedAt;
  }

  health() {
    const st = this.planner.status();
    return {
      id: this.id,
      status: (this.state === "Started" ? "healthy" : "starting") as HealthStatus,
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        planId: st.currentPlan?.id ?? null,
        progress: st.currentPlan?.progress ?? 0,
        runningAgents: st.runningAgents,
      },
    };
  }

  async initialize(): Promise<void> {
    if (this.state === "Created" || this.state === "Stopped") {
      this.state = "Initialized";
    }
  }

  async start(): Promise<void> {
    if (this.state === "Stopped") this.state = "Initialized";
    if (this.state === "Paused") {
      this.state = "Started";
      this.startedAt = Date.now();
      return;
    }
    if (this.state === "Initialized" || this.state === "Created") {
      this.unsub = this.planner.on((event) => {
        this.statusBroadcaster?.({
          type: event.type,
          payload: event.payload,
        });
      });
      this.state = "Started";
      this.startedAt = Date.now();
    }
  }

  async pause(): Promise<void> {
    if (this.state === "Started") this.state = "Paused";
  }

  async stop(): Promise<void> {
    this.unsub?.();
    this.unsub = null;
    this.state = "Stopped";
    this.startedAt = null;
  }

  async dispose(): Promise<void> {
    if (this.state === "Started" || this.state === "Paused") {
      await this.stop();
    }
    this.state = "Disposed";
  }
}

export function createExecutionService(
  deps: ExecutionServiceDeps,
): ExecutionService {
  return new ExecutionService(deps);
}

export const EXECUTION_SERVICE_ID = "ados.execution";
