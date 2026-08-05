import type { AiOrchestrator } from "@ados/orchestrator";
import type { ProviderGateway } from "@ados/providers";
import { ChatBridge, createChatBridge } from "./ChatBridge.js";

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

export interface ChatBridgeServiceDeps {
  readonly orchestrator: AiOrchestrator;
  readonly gateway: ProviderGateway;
}

/**
 * Kernel registry adapter — ados.chat_bridge
 */
export class ChatBridgeService {
  readonly id = "ados.chat_bridge";
  readonly version = "4.0.0";
  readonly kind = "extension" as const;

  readonly bridge: ChatBridge;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;
  private readonly deps: ChatBridgeServiceDeps;

  constructor(deps: ChatBridgeServiceDeps) {
    this.deps = deps;
    this.bridge = createChatBridge({
      orchestrator: deps.orchestrator,
      gateway: deps.gateway,
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

  health(): {
    id: string;
    status: HealthStatus;
    uptimeMs: number;
    version: string;
    checkedAt: string;
    details?: Readonly<Record<string, unknown>>;
  } {
    const st = this.bridge.status();
    return {
      id: this.id,
      status: this.state === "Started" ? "healthy" : "starting",
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        queue: st.queue,
        voiceReady: st.voiceReady,
        sessionId: st.sessionId,
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
      // Ensure gateway/orchestrator already running (boot order)
      void this.deps;
      this.unsub = this.bridge.on((event) => {
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

export function createChatBridgeService(
  deps: ChatBridgeServiceDeps,
): ChatBridgeService {
  return new ChatBridgeService(deps);
}

export const CHAT_BRIDGE_SERVICE_ID = "ados.chat_bridge";
