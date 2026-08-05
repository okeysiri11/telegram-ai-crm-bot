import type { AudioFrame } from "./VoiceRecorder.js";

export interface TranscriptionResult {
  readonly text: string;
  readonly confidence: number;
  readonly language: string;
  readonly providerId: string;
  readonly durationMs: number;
  readonly partial: boolean;
}

/**
 * Speech-to-text provider contract.
 */
export interface SpeechRecognizer {
  readonly id: string;
  readonly name: string;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  transcribe(input: {
    frames?: readonly AudioFrame[];
    /** Direct text override (Control Center / tests / typed voice). */
    textHint?: string;
    language?: string;
  }): Promise<TranscriptionResult>;
  health(): { status: "OK" | "DOWN"; message?: string };
}

abstract class BaseStt implements SpeechRecognizer {
  abstract readonly id: string;
  abstract readonly name: string;
  protected connected = false;

  async connect(): Promise<void> {
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    this.connected = false;
  }

  health(): { status: "OK" | "DOWN"; message?: string } {
    return {
      status: this.connected ? "OK" : "DOWN",
      ...(this.connected ? {} : { message: "Not connected" }),
    };
  }

  abstract transcribe(input: {
    frames?: readonly AudioFrame[];
    textHint?: string;
    language?: string;
  }): Promise<TranscriptionResult>;

  protected ensureConnected(): void {
    if (!this.connected) throw new Error(`${this.id} is not connected`);
  }
}

/** OpenAI STT mock — functional in-process provider. */
export class OpenAiSttProvider extends BaseStt {
  readonly id = "stt.openai";
  readonly name = "OpenAI STT";

  async transcribe(input: {
    frames?: readonly AudioFrame[];
    textHint?: string;
    language?: string;
  }): Promise<TranscriptionResult> {
    this.ensureConnected();
    const started = Date.now();
    await delay(12);
    const text = resolveTranscript(input);
    return {
      text,
      confidence: input.textHint ? 0.98 : 0.9,
      language: input.language ?? "en-US",
      providerId: this.id,
      durationMs: Date.now() - started,
      partial: false,
    };
  }
}

/** Whisper API-style mock. */
export class WhisperSttProvider extends BaseStt {
  readonly id = "stt.whisper.mock";
  readonly name = "Whisper (Mock)";

  async transcribe(input: {
    frames?: readonly AudioFrame[];
    textHint?: string;
    language?: string;
  }): Promise<TranscriptionResult> {
    this.ensureConnected();
    const started = Date.now();
    await delay(18);
    const text = resolveTranscript(input);
    return {
      text,
      confidence: input.textHint ? 0.97 : 0.93,
      language: input.language ?? "en-US",
      providerId: this.id,
      durationMs: Date.now() - started,
      partial: false,
    };
  }
}

/** Local Whisper mock for air-gapped deployments. */
export class LocalWhisperSttProvider extends BaseStt {
  readonly id = "stt.whisper.local";
  readonly name = "Local Whisper";

  async transcribe(input: {
    frames?: readonly AudioFrame[];
    textHint?: string;
    language?: string;
  }): Promise<TranscriptionResult> {
    this.ensureConnected();
    const started = Date.now();
    await delay(8);
    const text = resolveTranscript(input);
    return {
      text,
      confidence: input.textHint ? 0.96 : 0.88,
      language: input.language ?? "en-US",
      providerId: this.id,
      durationMs: Date.now() - started,
      partial: false,
    };
  }
}

function resolveTranscript(input: {
  frames?: readonly AudioFrame[];
  textHint?: string;
}): string {
  if (input.textHint?.trim()) return input.textHint.trim();
  const bytes = input.frames?.reduce((n, f) => n + f.samples.length, 0) ?? 0;
  if (bytes === 0) {
    throw new Error("No audio frames or textHint provided for transcription");
  }
  // Deterministic mock transcript from audio energy signature
  return `Generate code for voice module frame ${bytes}`;
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function createBuiltinSpeechRecognizers(): SpeechRecognizer[] {
  return [
    new WhisperSttProvider(),
    new OpenAiSttProvider(),
    new LocalWhisperSttProvider(),
  ];
}

export function createSpeechRecognizer(id?: string): SpeechRecognizer {
  const all = createBuiltinSpeechRecognizers();
  const found = id ? all.find((p) => p.id === id) : all[0];
  if (!found) throw new Error(`Speech recognizer not found: ${id}`);
  return found;
}
