import type { VoiceCommand as BridgeVoiceCommand } from "@ados/chat-bridge";
import type { SpeechRecognizer } from "./SpeechRecognizer.js";
import type { SpeechSynthesizer } from "./SpeechSynthesizer.js";
import type { AudioFrame } from "./VoiceRecorder.js";

/**
 * Unified voice I/O provider — STT + optional capture listen contract.
 * Implements chat-bridge VoiceInputProvider shape for compatibility.
 */
export class VoiceProvider {
  readonly id: string;
  readonly name: string;
  readonly recognizer: SpeechRecognizer;
  readonly synthesizer: SpeechSynthesizer;

  private connected = false;
  private lastTranscript = "";

  constructor(options: {
    id: string;
    name: string;
    recognizer: SpeechRecognizer;
    synthesizer: SpeechSynthesizer;
  }) {
    this.id = options.id;
    this.name = options.name;
    this.recognizer = options.recognizer;
    this.synthesizer = options.synthesizer;
  }

  async connect(): Promise<void> {
    await this.recognizer.connect();
    await this.synthesizer.connect();
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    await this.recognizer.disconnect();
    await this.synthesizer.disconnect();
    this.connected = false;
  }

  health(): { status: "OK" | "DOWN"; message?: string } {
    if (!this.connected) return { status: "DOWN", message: "Disconnected" };
    const stt = this.recognizer.health();
    const tts = this.synthesizer.health();
    if (stt.status !== "OK" || tts.status !== "OK") {
      return { status: "DOWN", message: "STT/TTS unhealthy" };
    }
    return { status: "OK" };
  }

  /**
   * chat-bridge VoiceInputProvider.listen compatibility.
   */
  async listen(): Promise<BridgeVoiceCommand> {
    const result = await this.recognizer.transcribe({
      textHint: this.lastTranscript || "Generate code for voice module",
    });
    this.lastTranscript = result.text;
    return {
      id: `vc_${Date.now().toString(36)}`,
      transcript: result.text,
      confidence: result.confidence,
      locale: result.language,
      at: new Date().toISOString(),
    };
  }

  async transcribe(input: {
    frames?: readonly AudioFrame[];
    textHint?: string;
    language?: string;
  }) {
    const result = await this.recognizer.transcribe(input);
    this.lastTranscript = result.text;
    return result;
  }

  async speak(text: string, opts?: { speed?: number; volume?: number }) {
    return this.synthesizer.synthesize({
      text,
      ...(opts?.speed !== undefined ? { speed: opts.speed } : {}),
      ...(opts?.volume !== undefined ? { volume: opts.volume } : {}),
    });
  }

  setLastTranscript(text: string): void {
    this.lastTranscript = text;
  }
}

export function createVoiceProvider(options: {
  id?: string;
  name?: string;
  recognizer: SpeechRecognizer;
  synthesizer: SpeechSynthesizer;
}): VoiceProvider {
  return new VoiceProvider({
    id: options.id ?? "provider.voice.mock",
    name: options.name ?? "ADOS Voice Provider",
    recognizer: options.recognizer,
    synthesizer: options.synthesizer,
  });
}
