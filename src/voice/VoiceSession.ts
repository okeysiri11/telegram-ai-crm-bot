import type { VoiceSessionState } from "./types.js";

export interface VoiceSessionSnapshot {
  readonly id: string;
  readonly state: VoiceSessionState;
  readonly startedAt: string;
  readonly updatedAt: string;
  readonly active: boolean;
  readonly paused: boolean;
  readonly commandIds: readonly string[];
  readonly lastCommandId: string | null;
}

/**
 * Voice session lifecycle: start / pause / resume / stop + history linkage.
 */
export class VoiceSession {
  readonly id: string;
  readonly startedAt: string;
  private state: VoiceSessionState = "idle";
  private updatedAt: string;
  private readonly commandIds: string[] = [];
  private lastCommandId: string | null = null;

  constructor(id?: string) {
    this.id = id ?? `vs_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    this.startedAt = new Date().toISOString();
    this.updatedAt = this.startedAt;
  }

  get active(): boolean {
    return this.state === "listening" || this.state === "processing" || this.state === "speaking";
  }

  get currentState(): VoiceSessionState {
    return this.state;
  }

  start(): void {
    if (this.state === "stopped") {
      throw new Error("Cannot start a stopped session; create a new one");
    }
    this.setState("listening");
  }

  pause(): void {
    if (this.state !== "listening" && this.state !== "processing") {
      throw new Error(`Cannot pause from state ${this.state}`);
    }
    this.setState("paused");
  }

  resume(): void {
    if (this.state !== "paused") {
      throw new Error(`Cannot resume from state ${this.state}`);
    }
    this.setState("listening");
  }

  stop(): void {
    this.setState("stopped");
  }

  markProcessing(): void {
    if (this.state === "stopped" || this.state === "paused") {
      throw new Error(`Cannot process in state ${this.state}`);
    }
    this.setState("processing");
  }

  markSpeaking(): void {
    this.setState("speaking");
  }

  markListening(): void {
    if (this.state === "stopped") return;
    this.setState("listening");
  }

  recordCommand(commandId: string): void {
    this.commandIds.push(commandId);
    this.lastCommandId = commandId;
    this.updatedAt = new Date().toISOString();
  }

  snapshot(): VoiceSessionSnapshot {
    return {
      id: this.id,
      state: this.state,
      startedAt: this.startedAt,
      updatedAt: this.updatedAt,
      active: this.active,
      paused: this.state === "paused",
      commandIds: [...this.commandIds],
      lastCommandId: this.lastCommandId,
    };
  }

  private setState(state: VoiceSessionState): void {
    this.state = state;
    this.updatedAt = new Date().toISOString();
  }
}

export function createVoiceSession(id?: string): VoiceSession {
  return new VoiceSession(id);
}
