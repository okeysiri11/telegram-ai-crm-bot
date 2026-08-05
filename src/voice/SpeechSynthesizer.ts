/**
 * Text-to-speech provider abstraction.
 */

export interface SynthesisResult {
  readonly providerId: string;
  readonly text: string;
  readonly audioBase64: string;
  readonly format: "pcm16" | "wav" | "mp3";
  readonly durationMs: number;
  readonly sampleRate: number;
}

export interface SpeechSynthesizer {
  readonly id: string;
  readonly name: string;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  synthesize(input: {
    text: string;
    language?: string;
    speed?: number;
    volume?: number;
  }): Promise<SynthesisResult>;
  health(): { status: "OK" | "DOWN"; message?: string };
}

abstract class BaseTts implements SpeechSynthesizer {
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

  abstract synthesize(input: {
    text: string;
    language?: string;
    speed?: number;
    volume?: number;
  }): Promise<SynthesisResult>;
}

export class OpenAiTtsProvider extends BaseTts {
  readonly id = "tts.openai";
  readonly name = "OpenAI TTS";

  async synthesize(input: {
    text: string;
    language?: string;
    speed?: number;
    volume?: number;
  }): Promise<SynthesisResult> {
    if (!this.connected) throw new Error(`${this.id} is not connected`);
    const started = Date.now();
    await delay(15);
    return encodeSpeech(this.id, input.text, input.speed ?? 1, input.volume ?? 0.8, started);
  }
}

export class SystemVoiceTtsProvider extends BaseTts {
  readonly id = "tts.system";
  readonly name = "System Voice";

  async synthesize(input: {
    text: string;
    language?: string;
    speed?: number;
    volume?: number;
  }): Promise<SynthesisResult> {
    if (!this.connected) throw new Error(`${this.id} is not connected`);
    const started = Date.now();
    await delay(5);
    return encodeSpeech(this.id, input.text, input.speed ?? 1, input.volume ?? 0.8, started);
  }
}

function encodeSpeech(
  providerId: string,
  text: string,
  speed: number,
  volume: number,
  started: number,
): SynthesisResult {
  // Functional PCM-like payload (base64) — playable by Control Center mock player
  const payload = Buffer.from(
    `ADOS_TTS|${providerId}|speed=${speed}|vol=${volume}|${text}`,
    "utf8",
  ).toString("base64");
  return {
    providerId,
    text,
    audioBase64: payload,
    format: "pcm16",
    durationMs: Date.now() - started,
    sampleRate: 22_050,
  };
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function createBuiltinSpeechSynthesizers(): SpeechSynthesizer[] {
  return [new SystemVoiceTtsProvider(), new OpenAiTtsProvider()];
}

export function createSpeechSynthesizer(id?: string): SpeechSynthesizer {
  const all = createBuiltinSpeechSynthesizers();
  const found = id ? all.find((p) => p.id === id) : all[0];
  if (!found) throw new Error(`Speech synthesizer not found: ${id}`);
  return found;
}
