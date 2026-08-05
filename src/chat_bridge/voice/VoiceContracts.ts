/**
 * Voice contracts — fulfilled by @ados/voice (ADOS OS 4.1).
 * Kept for ChatBridge compatibility; implementation lives in src/voice.
 */

export interface VoiceCommand {
  readonly id: string;
  readonly transcript: string;
  readonly confidence: number;
  readonly locale?: string;
  readonly at: string;
}

export interface VoiceSession {
  readonly id: string;
  readonly startedAt: string;
  readonly active: boolean;
  readonly lastCommandId?: string;
}

export interface VoiceInputProvider {
  readonly id: string;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  listen(): Promise<VoiceCommand>;
  health(): { status: "OK" | "DOWN"; message?: string };
}

/**
 * Pipeline contract: audio → transcript → ChatBridge task.
 * Implemented by @ados/voice SpeechPipeline.
 */
export interface SpeechPipeline {
  readonly provider: VoiceInputProvider;
  startSession(): Promise<VoiceSession>;
  stopSession(sessionId: string): Promise<void>;
  handleCommand(command: VoiceCommand): Promise<{ taskId: string }>;
}

/** Compatibility factory — Voice Module 4.1 implements these contracts. */
export function createVoiceReadyContracts(): {
  supported: true;
  implemented: true;
  module: "@ados/voice";
  interfaces: readonly string[];
} {
  return {
    supported: true,
    implemented: true,
    module: "@ados/voice",
    interfaces: [
      "VoiceInputProvider",
      "VoiceCommand",
      "VoiceSession",
      "SpeechPipeline",
      "VoiceGateway",
    ],
  };
}
