import {
  createProviderGateway,
  ProviderGateway,
} from "./ProviderGateway.js";

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
 * Kernel-registry adapter. Structural IService — id: ados.provider_gateway
 */
export class ProviderGatewayService {
  readonly id = "ados.provider_gateway";
  readonly version = "2.2.0";
  readonly kind = "extension" as const;

  readonly gateway: ProviderGateway;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;

  constructor(gateway?: ProviderGateway) {
    this.gateway = gateway ?? createProviderGateway();
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
    details?: Readonly<Record<string, unknown>>;
  } {
    const g = this.gateway.getStatus();
    const status: HealthStatus =
      this.state !== "Started"
        ? this.state === "Created" || this.state === "Initialized"
          ? "starting"
          : "stopped"
        : g.health === "OK"
          ? "healthy"
          : g.health === "DEGRADED"
            ? "degraded"
            : "unhealthy";
    return {
      id: this.id,
      status,
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        providers: g.providers,
        connected: g.connected,
        currentRequests: g.currentRequests,
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
      this.gateway.start(true);
      // Auto-connect all mock providers on boot
      await this.gateway.connect();
      this.unsub = this.gateway.on((event) => {
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
    await this.gateway.disconnect();
    this.gateway.stop();
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

export function createProviderGatewayService(
  gateway?: ProviderGateway,
): ProviderGatewayService {
  return new ProviderGatewayService(gateway);
}

export const PROVIDER_GATEWAY_SERVICE_ID = "ados.provider_gateway";
