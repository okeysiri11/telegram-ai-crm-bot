import { Lifecycle } from "../Lifecycle.js";
import type { IService } from "../interfaces/IService.js";
import type {
  HealthSnapshot,
  HealthStatus,
  LifecycleState,
  ServiceKind,
} from "../interfaces/types.js";

export interface InfrastructureServiceOptions {
  readonly id: string;
  readonly version?: string;
  readonly kind: ServiceKind;
  readonly critical?: boolean;
}

/**
 * Base infrastructure service used by BootLoader hosts.
 * No business vertical knowledge.
 */
export class InfrastructureService implements IService {
  readonly id: string;
  readonly version: string;
  readonly kind: ServiceKind;
  readonly critical: boolean;

  protected readonly lifecycle = new Lifecycle("Created");
  private startedAt: number | null = null;
  private forcedStatus: HealthStatus | null = null;

  constructor(options: InfrastructureServiceOptions) {
    this.id = options.id;
    this.version = options.version ?? "1.0.0";
    this.kind = options.kind;
    this.critical = options.critical ?? true;
  }

  getLifecycleState(): LifecycleState {
    return this.lifecycle.state;
  }

  uptimeMs(): number {
    if (this.startedAt === null || this.lifecycle.state !== "Started") {
      return 0;
    }
    return Date.now() - this.startedAt;
  }

  health(): HealthSnapshot {
    const status = this.forcedStatus ?? this.deriveStatus();
    const snapshot: HealthSnapshot = {
      id: this.id,
      status,
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: { kind: this.kind, critical: this.critical },
    };
    if (status !== "healthy") {
      return {
        ...snapshot,
        message: `Service ${this.id} is ${status}`,
      };
    }
    return snapshot;
  }

  /** Test / ops seam — not for business modules. */
  setForcedStatus(status: HealthStatus | null): void {
    this.forcedStatus = status;
  }

  async initialize(): Promise<void> {
    this.lifecycle.assertState("Created", "Stopped");
    if (this.lifecycle.state === "Stopped") {
      this.lifecycle.transition("Initialized");
    } else {
      this.lifecycle.transition("Initialized");
    }
  }

  async start(): Promise<void> {
    this.lifecycle.assertState("Initialized", "Paused", "Stopped");
    if (this.lifecycle.state === "Stopped") {
      this.lifecycle.transition("Initialized");
    }
    if (this.lifecycle.state === "Paused") {
      this.lifecycle.transition("Started");
    } else if (this.lifecycle.state === "Initialized") {
      this.lifecycle.transition("Started");
    }
    this.startedAt = Date.now();
  }

  async pause(): Promise<void> {
    this.lifecycle.assertState("Started");
    this.lifecycle.transition("Paused");
  }

  async stop(): Promise<void> {
    this.lifecycle.assertState("Started", "Paused", "Initialized");
    if (this.lifecycle.state === "Initialized") {
      this.lifecycle.transition("Stopped");
    } else {
      this.lifecycle.transition("Stopped");
    }
    this.startedAt = null;
  }

  async dispose(): Promise<void> {
    if (this.lifecycle.state === "Disposed") {
      return;
    }
    if (
      this.lifecycle.state === "Started" ||
      this.lifecycle.state === "Paused"
    ) {
      this.lifecycle.transition("Stopped");
    }
    if (
      this.lifecycle.state === "Created" ||
      this.lifecycle.state === "Initialized" ||
      this.lifecycle.state === "Stopped"
    ) {
      this.lifecycle.transition("Disposed");
    }
    this.startedAt = null;
  }

  private deriveStatus(): HealthStatus {
    switch (this.lifecycle.state) {
      case "Started":
        return "healthy";
      case "Paused":
        return "degraded";
      case "Initialized":
      case "Created":
        return "starting";
      case "Stopped":
      case "Disposed":
        return "stopped";
      default: {
        const _exhaustive: never = this.lifecycle.state;
        return _exhaustive;
      }
    }
  }
}
