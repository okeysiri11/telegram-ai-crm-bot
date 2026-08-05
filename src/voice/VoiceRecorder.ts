/**
 * Microphone / audio capture abstraction for the Enterprise Voice pipeline.
 * Server-side: accepts PCM/base64 frames; tracks recording + VAD state.
 */

export interface AudioFrame {
  readonly samples: Uint8Array;
  readonly sampleRate: number;
  readonly channels: number;
  readonly at: string;
}

export interface RecorderSnapshot {
  readonly recording: boolean;
  readonly microphoneId: string;
  readonly frames: number;
  readonly bytes: number;
  readonly voiceDetected: boolean;
  readonly noiseReduction: boolean;
  readonly permissionGranted: boolean;
}

export class VoiceRecorder {
  private recording = false;
  private frames: AudioFrame[] = [];
  private bytes = 0;
  private voiceDetected = false;
  private microphoneId = "default";
  private noiseReduction = true;
  private vadEnabled = true;
  private permissionGranted = false;

  configure(options: {
    microphoneId?: string;
    noiseReduction?: boolean;
    vadEnabled?: boolean;
  }): void {
    if (options.microphoneId !== undefined) this.microphoneId = options.microphoneId;
    if (options.noiseReduction !== undefined) {
      this.noiseReduction = options.noiseReduction;
    }
    if (options.vadEnabled !== undefined) this.vadEnabled = options.vadEnabled;
  }

  async requestPermission(): Promise<boolean> {
    // Enterprise runtime: grant for in-process / Control Center sessions
    this.permissionGranted = true;
    return true;
  }

  start(): void {
    if (!this.permissionGranted) {
      throw new Error("Microphone permission required");
    }
    this.recording = true;
    this.frames = [];
    this.bytes = 0;
    this.voiceDetected = false;
  }

  stop(): AudioFrame[] {
    this.recording = false;
    const out = [...this.frames];
    return out;
  }

  /**
   * Ingest an audio frame (from Control Center or API).
   * Applies noise reduction + VAD heuristics on energy.
   */
  pushFrame(frame: AudioFrame): { voiceDetected: boolean } {
    if (!this.recording) {
      throw new Error("Recorder is not recording");
    }
    let samples = frame.samples;
    if (this.noiseReduction) {
      samples = reduceNoise(samples);
    }
    const energy = averageEnergy(samples);
    const detected = this.vadEnabled ? energy > 8 : samples.length > 0;
    if (detected) this.voiceDetected = true;
    this.frames.push({
      samples,
      sampleRate: frame.sampleRate,
      channels: frame.channels,
      at: frame.at,
    });
    this.bytes += samples.byteLength;
    return { voiceDetected: detected };
  }

  /**
   * Convenience: ingest base64 PCM (or empty → synthetic silence for text-only).
   */
  pushBase64(base64: string, sampleRate = 16_000): { voiceDetected: boolean } {
    const buf = Buffer.from(base64 || "AAAA", "base64");
    return this.pushFrame({
      samples: new Uint8Array(buf),
      sampleRate,
      channels: 1,
      at: new Date().toISOString(),
    });
  }

  snapshot(): RecorderSnapshot {
    return {
      recording: this.recording,
      microphoneId: this.microphoneId,
      frames: this.frames.length,
      bytes: this.bytes,
      voiceDetected: this.voiceDetected,
      noiseReduction: this.noiseReduction,
      permissionGranted: this.permissionGranted,
    };
  }

  clear(): void {
    this.frames = [];
    this.bytes = 0;
    this.voiceDetected = false;
  }
}

function averageEnergy(samples: Uint8Array): number {
  if (samples.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i]!;
  return sum / samples.length;
}

function reduceNoise(samples: Uint8Array): Uint8Array {
  const out = new Uint8Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const v = samples[i]!;
    out[i] = v < 4 ? 0 : v;
  }
  return out;
}

export function createVoiceRecorder(): VoiceRecorder {
  return new VoiceRecorder();
}
