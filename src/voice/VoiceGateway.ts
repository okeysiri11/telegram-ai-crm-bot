import type { ChatBridge } from "@ados/chat-bridge";
import {
  SpeechPipeline,
  createSpeechPipeline,
  type ProcessVoiceInput,
  type ProcessVoiceResult,
} from "./SpeechPipeline.js";
import type { VoiceSettingsState } from "./VoiceSettings.js";
import type { VoiceEventListener } from "./VoiceEvents.js";

export interface VoiceGatewayOptions {
  readonly bridge: ChatBridge;
  readonly settings?: Partial<VoiceSettingsState>;
}

/**
 * First-class Voice interface for ADOS — equal to Web / Telegram / API.
 * Facade over SpeechPipeline → ChatGPT Bridge → Orchestrator.
 */
export class VoiceGateway {
  readonly pipeline: SpeechPipeline;

  constructor(options: VoiceGatewayOptions) {
    this.pipeline = createSpeechPipeline(options.bridge, options.settings);
  }

  on(listener: VoiceEventListener): () => void {
    return this.pipeline.events.on(listener);
  }

  async start(sessionHint?: { language?: string }): Promise<unknown> {
    if (sessionHint?.language) {
      this.pipeline.updateSettings({ language: sessionHint.language });
    }
    const session = await this.pipeline.startSession();
    return session.snapshot();
  }

  async stop(sessionId?: string): Promise<unknown> {
    await this.pipeline.stopSession(sessionId);
    return this.pipeline.getSession()?.snapshot() ?? { stopped: true };
  }

  pause(): unknown {
    this.pipeline.pauseSession();
    return this.pipeline.getSession()?.snapshot() ?? null;
  }

  resume(): unknown {
    this.pipeline.resumeSession();
    return this.pipeline.getSession()?.snapshot() ?? null;
  }

  async process(input: ProcessVoiceInput): Promise<ProcessVoiceResult> {
    return this.pipeline.process(input);
  }

  history(limit = 100) {
    return this.pipeline.history.list(limit);
  }

  getSettings(): VoiceSettingsState {
    return this.pipeline.settings.get();
  }

  updateSettings(patch: Partial<VoiceSettingsState>): VoiceSettingsState {
    return this.pipeline.updateSettings(patch);
  }

  status() {
    return this.pipeline.status();
  }

  context() {
    return this.pipeline.context.get();
  }
}

export function createVoiceGateway(options: VoiceGatewayOptions): VoiceGateway {
  return new VoiceGateway(options);
}
