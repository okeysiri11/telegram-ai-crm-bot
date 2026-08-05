import { MCPGateway, createMCPGateway } from "./MCPGateway.js";
import type { McpConfigState } from "./MCPConfig.js";
import type { RuntimeInvoker } from "./types.js";

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

export interface MCPServiceDeps {
  readonly config?: Partial<McpConfigState>;
  readonly loadDiskConfig?: boolean;
}

/**
 * Kernel registry adapter — ados.mcp
 */
export class MCPService {
  readonly id = "ados.mcp";
  readonly version = "4.2.0";
  readonly kind = "extension" as const;

  readonly gateway: MCPGateway;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;

  constructor(deps: MCPServiceDeps = {}) {
    this.gateway = createMCPGateway({
      loadDiskConfig: deps.loadDiskConfig ?? true,
      ...(deps.config !== undefined ? { config: deps.config } : {}),
    });
  }

  setStatusBroadcaster(fn: ((message: unknown) => void) | null): void {
    this.statusBroadcaster = fn;
  }

  setRuntimeInvoker(invoker: RuntimeInvoker | null): void {
    this.gateway.setRuntimeInvoker(invoker);
  }

  getLifecycleState(): LifecycleState {
    return this.state;
  }

  uptimeMs(): number {
    if (this.startedAt === null || this.state !== "Started") return 0;
    return Date.now() - this.startedAt;
  }

  health() {
    const st = this.gateway.status();
    return {
      id: this.id,
      status: (this.state === "Started"
        ? st.enabled
          ? "healthy"
          : "degraded"
        : "starting") as HealthStatus,
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        tools: st.tools,
        resources: st.resources,
        prompts: st.prompts,
        connectedClients: st.connectedClients,
        runtimeBound: st.runtimeBound,
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
    this.gateway.setRuntimeInvoker(null);
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

export function createMCPService(deps?: MCPServiceDeps): MCPService {
  return new MCPService(deps);
}

export const MCP_SERVICE_ID = "ados.mcp";
