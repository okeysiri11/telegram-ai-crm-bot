import type { ChatBridge } from "@ados/chat-bridge";
import { VoiceGateway, createVoiceGateway } from "./VoiceGateway.js";
import type { VoiceSettingsState } from "./VoiceSettings.js";

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

export interface VoiceServiceDeps {
  readonly bridge: ChatBridge;
  readonly settings?: Partial<VoiceSettingsState>;
}

/**
 * Kernel registry adapter — ados.voice
 */
export class VoiceService {
  readonly id = "ados.voice";
  readonly version = "4.1.0";
  readonly kind = "extension" as const;

  readonly gateway: VoiceGateway;

  private state: LifecycleState = "Created";
  private startedAt: number | null = null;
  private unsub: (() => void) | null = null;
  private statusBroadcaster: ((message: unknown) => void) | null = null;

  constructor(deps: VoiceServiceDeps) {
    this.gateway = createVoiceGateway({
      bridge: deps.bridge,
      ...(deps.settings !== undefined ? { settings: deps.settings } : {}),
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
    const st = this.gateway.status();
    return {
      id: this.id,
      status: this.state === "Started" ? "healthy" : "starting",
      uptimeMs: this.uptimeMs(),
      version: this.version,
      checkedAt: new Date().toISOString(),
      details: {
        implemented: st.implemented,
        session: st.session?.id ?? null,
        wakeWord: st.wakeWord,
        historyCount: st.historyCount,
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
    try {
      await this.gateway.stop();
    } catch {
      /* ignore */
    }
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

export function createVoiceService(deps: VoiceServiceDeps): VoiceService {
  return new VoiceService(deps);
}

export const VOICE_SERVICE_ID = "ados.voice";
