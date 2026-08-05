import type { ChatBridge } from "@ados/chat-bridge";
import type { VoiceCommand } from "./types.js";
import { CommandInterpreter, createCommandInterpreter } from "./CommandInterpreter.js";
import { IntentDetector, createIntentDetector } from "./IntentDetector.js";
import { VoiceContext, createVoiceContext } from "./VoiceContext.js";
import { VoiceEvents, createVoiceEvents } from "./VoiceEvents.js";
import { VoiceHistory, createVoiceHistory } from "./VoiceHistory.js";
import { VoiceRecorder, createVoiceRecorder } from "./VoiceRecorder.js";
import {
  createSpeechRecognizer,
} from "./SpeechRecognizer.js";
import {
  createSpeechSynthesizer,
  type SynthesisResult,
} from "./SpeechSynthesizer.js";
import { VoiceProvider, createVoiceProvider } from "./VoiceProvider.js";
import { VoiceSession, createVoiceSession } from "./VoiceSession.js";
import {
  VoiceSettings,
  createVoiceSettings,
  type VoiceSettingsState,
} from "./VoiceSettings.js";
import { WakeWord, createWakeWord } from "./WakeWord.js";

export interface ProcessVoiceInput {
  /** Spoken / typed transcript override (skips STT when set alone with no audio). */
  text?: string;
  /** Base64 PCM audio for STT. */
  audioBase64?: string;
  language?: string;
  sessionId?: string;
  /** Force wake-word bypass for Push-to-Talk. */
  bypassWakeWord?: boolean;
  autoExecute?: boolean;
}

export interface ProcessVoiceResult {
  readonly command: VoiceCommand;
  readonly transcription: {
    text: string;
    confidence: number;
    providerId: string;
  };
  readonly intent: VoiceCommand["intent"];
  readonly confidence: number;
  readonly navigation?: { path: string; label: string };
  readonly chatTaskId?: string;
  readonly executed: boolean;
  readonly responseText: string;
  readonly speech?: SynthesisResult;
  readonly session: ReturnType<VoiceSession["snapshot"]>;
}

/**
 * End-to-end: Mic → NR/VAD → STT → Intent → Chat Bridge → TTS.
 * Implements chat-bridge SpeechPipeline contract.
 */
export class SpeechPipeline {
  readonly events: VoiceEvents;
  readonly settings: VoiceSettings;
  readonly history: VoiceHistory;
  readonly context: VoiceContext;
  readonly recorder: VoiceRecorder;
  readonly wakeWord: WakeWord;
  readonly intentDetector: IntentDetector;
  provider: VoiceProvider;

  private readonly interpreter: CommandInterpreter;
  private session: VoiceSession | null = null;
  private activeSttId: string;
  private activeTtsId: string;

  constructor(bridge: ChatBridge, settings?: Partial<VoiceSettingsState>) {
    this.events = createVoiceEvents();
    this.settings = createVoiceSettings(settings);
    this.history = createVoiceHistory();
    this.context = createVoiceContext();
    this.recorder = createVoiceRecorder();
    const s = this.settings.get();
    this.wakeWord = createWakeWord(s.wakeWord, s.wakeWordEnabled);
    this.intentDetector = createIntentDetector();
    this.activeSttId = s.speechProvider;
    this.activeTtsId = s.ttsProvider;
    const stt = createSpeechRecognizer(s.speechProvider);
    const tts = createSpeechSynthesizer(s.ttsProvider);
    this.provider = createVoiceProvider({
      id: s.voiceProvider,
      recognizer: stt,
      synthesizer: tts,
    });
    this.interpreter = createCommandInterpreter(bridge, this.context);
  }

  /** chat-bridge SpeechPipeline compatibility */
  get chatBridgeProvider() {
    return this.provider;
  }

  async startSession(): Promise<VoiceSession> {
    const s = this.settings.get();
    await this.provider.connect();
    await this.recorder.requestPermission();
    this.recorder.configure({
      microphoneId: s.microphoneId,
      noiseReduction: s.noiseReduction,
      vadEnabled: s.vadEnabled,
    });
    this.wakeWord.configure(s.wakeWord, s.wakeWordEnabled);
    this.session = createVoiceSession();
    this.session.start();
    this.recorder.start();
    this.events.emit("voice.started", this.session.snapshot());
    this.events.emit("voice.status", {
      session: this.session.snapshot(),
      mic: this.recorder.snapshot(),
    });
    return this.session;
  }

  async stopSession(sessionId?: string): Promise<void> {
    if (!this.session) return;
    if (sessionId && this.session.id !== sessionId) {
      throw new Error(`Session mismatch: ${sessionId}`);
    }
    this.recorder.stop();
    this.session.stop();
    this.events.emit("voice.stopped", this.session.snapshot());
    this.events.emit("voice.status", {
      session: this.session.snapshot(),
      mic: this.recorder.snapshot(),
    });
  }

  pauseSession(): void {
    this.session?.pause();
    this.events.emit("voice.status", {
      session: this.session?.snapshot() ?? null,
      mic: this.recorder.snapshot(),
    });
  }

  resumeSession(): void {
    this.session?.resume();
    if (!this.recorder.snapshot().recording) {
      this.recorder.start();
    }
    this.events.emit("voice.status", {
      session: this.session?.snapshot() ?? null,
      mic: this.recorder.snapshot(),
    });
  }

  /**
   * chat-bridge SpeechPipeline.handleCommand — transcript → ingest path.
   */
  async handleCommand(command: {
    id: string;
    transcript: string;
    confidence: number;
    locale?: string;
    at: string;
  }): Promise<{ taskId: string }> {
    const input: ProcessVoiceInput = {
      text: command.transcript,
      bypassWakeWord: true,
    };
    if (command.locale !== undefined) input.language = command.locale;
    const result = await this.process(input);
    if (!result.chatTaskId) {
      throw new Error("Command did not produce a chat task");
    }
    return { taskId: result.chatTaskId };
  }

  async process(input: ProcessVoiceInput): Promise<ProcessVoiceResult> {
    const started = Date.now();
    const settings = this.settings.get();

    if (!this.session || this.session.currentState === "stopped") {
      await this.startSession();
    }
    if (this.session!.currentState === "paused") {
      throw new Error("Voice session is paused");
    }

    // Validate session + security
    const security = this.securityState();
    if (!security.microphone.granted) {
      throw new Error("Microphone permission denied");
    }
    if (!security.providerAuthenticated) {
      throw new Error("Voice provider not authenticated");
    }
    if (!security.sessionValid) {
      throw new Error("Voice session invalid");
    }

    this.session!.markProcessing();

    // Audio path
    let frames = this.recorder.stop();
    if (input.audioBase64) {
      if (!this.recorder.snapshot().recording) this.recorder.start();
      const vad = this.recorder.pushBase64(input.audioBase64);
      if (vad.voiceDetected) {
        this.events.emit("voice.detected", { energy: true });
      }
      frames = this.recorder.stop();
      if (settings.continuousListening || settings.pushToTalk) {
        this.recorder.start();
      }
    }

    this.events.emit("voice.partial", {
      sessionId: this.session!.id,
      hint: input.text ?? null,
    });

    // Reconnect STT/TTS if settings changed provider ids
    await this.ensureProviders(settings);

    const transcription = await this.provider.transcribe({
      frames,
      ...(input.text !== undefined ? { textHint: input.text } : {}),
      language: input.language ?? settings.language,
    });

    this.events.emit("voice.transcribed", transcription);
    this.events.emit("voice.final", transcription);

    const bypass =
      input.bypassWakeWord === true ||
      settings.pushToTalk ||
      !settings.wakeWordEnabled;

    const wake = bypass
      ? { matched: true, remainder: transcription.text }
      : this.wakeWord.match(transcription.text);

    if (!wake.matched) {
      const ignored = this.makeCommand({
        text: transcription.text,
        intent: "unknown",
        confidence: transcription.confidence,
        language: transcription.language,
        provider: transcription.providerId,
        status: "ignored",
        wakeWordMatched: false,
      });
      ignored.durationMs = Date.now() - started;
      this.history.push({
        sessionId: ignored.sessionId,
        text: ignored.text,
        intent: ignored.intent,
        confidence: ignored.confidence,
        status: ignored.status,
        provider: ignored.provider,
      });
      this.session!.markListening();
      return {
        command: ignored,
        transcription: {
          text: transcription.text,
          confidence: transcription.confidence,
          providerId: transcription.providerId,
        },
        intent: "unknown",
        confidence: transcription.confidence,
        executed: false,
        responseText: `Wake word "${this.wakeWord.getPhrase()}" not detected.`,
        session: this.session!.snapshot(),
      };
    }

    const command = this.makeCommand({
      text: wake.remainder,
      intent: "unknown",
      confidence: transcription.confidence,
      language: transcription.language,
      provider: transcription.providerId,
      status: "transcribed",
      wakeWordMatched: wake.matched,
    });
    this.session!.recordCommand(command.id);

    const match = this.intentDetector.detect(command.text);
    this.events.emit("voice.intent", {
      intent: match.intent,
      confidence: match.confidence,
      entities: match.entities,
      commandId: command.id,
    });

    const autoExecute = input.autoExecute ?? settings.autoExecute;
    const interpreted = await this.interpreter.interpret(command, match, {
      autoExecute,
    });

    this.events.emit("voice.execution", {
      commandId: command.id,
      chatTaskId: interpreted.chatTaskId ?? null,
      executed: interpreted.executed,
    });
    this.events.emit("voice.executed", {
      commandId: command.id,
      chatTaskId: interpreted.chatTaskId ?? null,
    });

    this.session!.markSpeaking();
    const speech = await this.provider.speak(interpreted.responseText, {
      speed: settings.voiceSpeed,
      volume: settings.voiceVolume,
    });
    this.events.emit("voice.response", {
      text: interpreted.responseText,
      speechProvider: speech.providerId,
    });

    command.durationMs = Date.now() - started;
    this.history.push({
      sessionId: command.sessionId,
      text: command.text,
      intent: command.intent,
      confidence: command.confidence,
      status: command.status,
      provider: command.provider,
      ...(command.responseText !== undefined
        ? { responseText: command.responseText }
        : {}),
      ...(command.chatTaskId !== undefined
        ? { chatTaskId: command.chatTaskId }
        : {}),
      durationMs: command.durationMs,
    });

    this.events.emit("voice.completed", {
      command,
      durationMs: command.durationMs,
    });

    if (settings.continuousListening) {
      this.session!.markListening();
      if (!this.recorder.snapshot().recording) this.recorder.start();
    } else {
      this.session!.markListening();
    }

    const out: ProcessVoiceResult = {
      command,
      transcription: {
        text: transcription.text,
        confidence: transcription.confidence,
        providerId: transcription.providerId,
      },
      intent: command.intent,
      confidence: command.confidence,
      executed: interpreted.executed,
      responseText: interpreted.responseText,
      speech,
      session: this.session!.snapshot(),
      ...(interpreted.navigation !== undefined
        ? { navigation: interpreted.navigation }
        : {}),
      ...(interpreted.chatTaskId !== undefined
        ? { chatTaskId: interpreted.chatTaskId }
        : {}),
    };
    return out;
  }

  updateSettings(patch: Partial<VoiceSettingsState>): VoiceSettingsState {
    const next = this.settings.update(patch);
    this.wakeWord.configure(next.wakeWord, next.wakeWordEnabled);
    this.recorder.configure({
      microphoneId: next.microphoneId,
      noiseReduction: next.noiseReduction,
      vadEnabled: next.vadEnabled,
    });
    return next;
  }

  getSession(): VoiceSession | null {
    return this.session;
  }

  securityState() {
    const mic = this.recorder.snapshot();
    const health = this.provider.health();
    return {
      microphone: {
        granted: mic.permissionGranted,
        reason: mic.permissionGranted ? "granted" : "required",
      },
      providerAuthenticated: health.status === "OK" || this.session !== null,
      sessionValid:
        this.session !== null && this.session.currentState !== "stopped",
    };
  }

  status() {
    const s = this.settings.get();
    const session = this.session?.snapshot() ?? null;
    const last = this.history.list(1)[0] ?? null;
    return {
      id: "ados.voice",
      name: "Enterprise Voice Module",
      health: "OK" as const,
      implemented: true as const,
      microphone: this.recorder.snapshot(),
      session,
      settings: s,
      context: this.context.get(),
      currentProvider: s.voiceProvider,
      speechProvider: s.speechProvider,
      ttsProvider: s.ttsProvider,
      currentAgent: this.context.get().selectedAgent,
      lastCommand: last,
      wakeWord: this.wakeWord.getPhrase(),
      security: this.securityState(),
      historyCount: this.history.list(10_000).length,
    };
  }

  private async ensureProviders(settings: VoiceSettingsState): Promise<void> {
    if (
      this.activeSttId !== settings.speechProvider ||
      this.activeTtsId !== settings.ttsProvider
    ) {
      await this.provider.disconnect();
      const stt = createSpeechRecognizer(settings.speechProvider);
      const tts = createSpeechSynthesizer(settings.ttsProvider);
      this.provider = createVoiceProvider({
        id: settings.voiceProvider,
        recognizer: stt,
        synthesizer: tts,
      });
      this.activeSttId = settings.speechProvider;
      this.activeTtsId = settings.ttsProvider;
      await this.provider.connect();
      return;
    }
    if (this.provider.health().status !== "OK") {
      await this.provider.connect();
    }
  }

  private makeCommand(partial: {
    text: string;
    intent: VoiceCommand["intent"];
    confidence: number;
    language: string;
    provider: string;
    status: VoiceCommand["status"];
    wakeWordMatched?: boolean;
  }): VoiceCommand {
    const cmd: VoiceCommand = {
      id: `vcmd_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      text: partial.text,
      intent: partial.intent,
      confidence: partial.confidence,
      language: partial.language,
      timestamp: new Date().toISOString(),
      sessionId: this.session!.id,
      provider: partial.provider,
      status: partial.status,
    };
    if (partial.wakeWordMatched !== undefined) {
      cmd.wakeWordMatched = partial.wakeWordMatched;
    }
    return cmd;
  }
}

export function createSpeechPipeline(
  bridge: ChatBridge,
  settings?: Partial<VoiceSettingsState>,
): SpeechPipeline {
  return new SpeechPipeline(bridge, settings);
}
