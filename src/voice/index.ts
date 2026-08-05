export type {
  VoiceCommand,
  VoiceCommandStatus,
  VoiceEvent,
  VoiceEventType,
  VoiceHistoryEntry,
  VoiceIntent,
  VoiceSecurityState,
  VoiceSessionState,
} from "./types.js";

export { VoiceEvents, createVoiceEvents } from "./VoiceEvents.js";
export {
  VoiceSettings,
  createVoiceSettings,
  DEFAULT_VOICE_SETTINGS,
  type VoiceSettingsState,
} from "./VoiceSettings.js";
export { VoiceHistory, createVoiceHistory } from "./VoiceHistory.js";
export {
  VoiceContext,
  createVoiceContext,
  type VoiceContextState,
} from "./VoiceContext.js";
export { WakeWord, createWakeWord } from "./WakeWord.js";
export {
  IntentDetector,
  createIntentDetector,
  type IntentMatch,
} from "./IntentDetector.js";
export {
  CommandInterpreter,
  createCommandInterpreter,
} from "./CommandInterpreter.js";
export {
  VoiceRecorder,
  createVoiceRecorder,
  type AudioFrame,
  type RecorderSnapshot,
} from "./VoiceRecorder.js";
export {
  createBuiltinSpeechRecognizers,
  createSpeechRecognizer,
  OpenAiSttProvider,
  WhisperSttProvider,
  LocalWhisperSttProvider,
  type SpeechRecognizer,
  type TranscriptionResult,
} from "./SpeechRecognizer.js";
export {
  createBuiltinSpeechSynthesizers,
  createSpeechSynthesizer,
  OpenAiTtsProvider,
  SystemVoiceTtsProvider,
  type SpeechSynthesizer,
  type SynthesisResult,
} from "./SpeechSynthesizer.js";
export { VoiceProvider, createVoiceProvider } from "./VoiceProvider.js";
export {
  VoiceSession,
  createVoiceSession,
  type VoiceSessionSnapshot,
} from "./VoiceSession.js";
export {
  SpeechPipeline,
  createSpeechPipeline,
  type ProcessVoiceInput,
  type ProcessVoiceResult,
} from "./SpeechPipeline.js";
export { VoiceGateway, createVoiceGateway } from "./VoiceGateway.js";
export {
  VoiceService,
  createVoiceService,
  VOICE_SERVICE_ID,
} from "./VoiceService.js";
