/**
 * Configurable voice settings — persisted in-memory (enterprise defaults).
 */

export interface VoiceSettingsState {
  language: string;
  microphoneId: string;
  wakeWord: string;
  wakeWordEnabled: boolean;
  voiceProvider: string;
  speechProvider: string;
  ttsProvider: string;
  autoExecute: boolean;
  pushToTalk: boolean;
  continuousListening: boolean;
  voiceSpeed: number;
  voiceVolume: number;
  noiseReduction: boolean;
  vadEnabled: boolean;
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettingsState = {
  language: "en-US",
  microphoneId: "default",
  wakeWord: "Hey ADOS",
  wakeWordEnabled: true,
  voiceProvider: "provider.voice.mock",
  speechProvider: "stt.whisper.mock",
  ttsProvider: "tts.system",
  autoExecute: true,
  pushToTalk: false,
  continuousListening: false,
  voiceSpeed: 1,
  voiceVolume: 0.8,
  noiseReduction: true,
  vadEnabled: true,
};

export class VoiceSettings {
  private state: VoiceSettingsState;

  constructor(initial?: Partial<VoiceSettingsState>) {
    this.state = { ...DEFAULT_VOICE_SETTINGS, ...initial };
  }

  get(): Readonly<VoiceSettingsState> {
    return { ...this.state };
  }

  update(patch: Partial<VoiceSettingsState>): Readonly<VoiceSettingsState> {
    if (patch.wakeWord !== undefined) {
      const trimmed = patch.wakeWord.trim();
      if (!trimmed) throw new Error("wakeWord must not be empty");
      patch = { ...patch, wakeWord: trimmed };
    }
    if (patch.voiceSpeed !== undefined) {
      patch = {
        ...patch,
        voiceSpeed: Math.min(2, Math.max(0.5, patch.voiceSpeed)),
      };
    }
    if (patch.voiceVolume !== undefined) {
      patch = {
        ...patch,
        voiceVolume: Math.min(1, Math.max(0, patch.voiceVolume)),
      };
    }
    this.state = { ...this.state, ...patch };
    return this.get();
  }

  reset(): Readonly<VoiceSettingsState> {
    this.state = { ...DEFAULT_VOICE_SETTINGS };
    return this.get();
  }
}

export function createVoiceSettings(
  initial?: Partial<VoiceSettingsState>,
): VoiceSettings {
  return new VoiceSettings(initial);
}
