import { AiOrchestrator, createAiOrchestrator } from "./AiOrchestrator.js";
import {
  CollaborationEngine,
  createCollaborationEngine,
} from "./collaboration/CollaborationEngine.js";

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

/**
 * Kernel-registry adapter. Structural IService — Kernel never imports agent logic.
 * Service id: ados.orchestrator
 */
export class OrchestratorService {
  readonly id = "ados.orchestrator";
  readonly version = "3.0.0";
  readonly kind = "extension" as const;

  readonly orchestrator: AiOrchestrator;
  readonly collaboration: CollaborationEngine;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private collabUnsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;

  constructor(orchestrator?: AiOrchestrator) {
    this.orchestrator = orchestrator ?? createAiOrchestrator();
    this.collaboration = createCollaborationEngine(this.orchestrator);
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

  health(): {
    id: string;
    status: HealthStatus;
    uptimeMs: number;
    version: string;
    checkedAt: string;
    message?: string;
    details?: Readonly<Record<string, unknown>>;
  } {
    const orch = this.orchestrator.getStatus();
    const status: HealthStatus =
      this.state !== "Started"
        ? this.state === "Created" || this.state === "Initialized"
          ? "starting"
          : "stopped"
        : orch.health === "OK"
          ? "healthy"
          : orch.health === "DEGRADED"
            ? "degraded"
            : "unhealthy";
    return {
      id: this.id,
      status,
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        agents: orch.agents,
        runningTasks: orch.runningTasks,
        queueSize: orch.queueSize,
        liveStatus: orch.liveStatus,
        collaboration: this.collaboration.overview(),
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
      this.orchestrator.start(true);
      this.unsub = this.orchestrator.on((event) => {
        this.statusBroadcaster?.({
          type: event.type,
          payload: event.payload,
        });
      });
      this.collabUnsub = this.collaboration.on((event) => {
        this.statusBroadcaster?.({
          type: event.type,
          payload: event.payload,
        });
      });
      for (const agent of this.orchestrator.listAgents()) {
        this.statusBroadcaster?.({
          type: "agent.online",
          payload: { agentId: agent.id, status: agent.status },
        });
      }
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
    this.collabUnsub?.();
    this.collabUnsub = null;
    this.orchestrator.stop();
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

export function createOrchestratorService(
  orchestrator?: AiOrchestrator,
): OrchestratorService {
  return new OrchestratorService(orchestrator);
}

export const ORCHESTRATOR_SERVICE_ID = "ados.orchestrator";
