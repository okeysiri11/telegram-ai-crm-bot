/**
 * ADOS Enterprise Voice Module — shared types.
 */

export type VoiceIntent =
  | "create_project"
  | "create_task"
  | "open_module"
  | "search"
  | "run_workflow"
  | "generate_code"
  | "review_code"
  | "explain_code"
  | "open_crm"
  | "open_erp"
  | "open_ai_studio"
  | "open_marketplace"
  | "create_document"
  | "generate_report"
  | "run_agent"
  | "execute_command"
  | "unknown";

export type VoiceCommandStatus =
  | "received"
  | "transcribed"
  | "interpreted"
  | "queued"
  | "executing"
  | "completed"
  | "failed"
  | "cancelled"
  | "ignored";

export type VoiceSessionState =
  | "idle"
  | "listening"
  | "paused"
  | "processing"
  | "speaking"
  | "stopped";

export interface VoiceCommand {
  readonly id: string;
  text: string;
  intent: VoiceIntent;
  confidence: number;
  language: string;
  readonly timestamp: string;
  sessionId: string;
  provider: string;
  status: VoiceCommandStatus;
  wakeWordMatched?: boolean;
  chatTaskId?: string;
  responseText?: string;
  error?: string;
  durationMs?: number;
  entities?: Readonly<Record<string, string>>;
}

export interface VoiceHistoryEntry {
  readonly id: string;
  readonly at: string;
  readonly sessionId: string;
  readonly text: string;
  readonly intent: VoiceIntent;
  readonly confidence: number;
  readonly status: VoiceCommandStatus;
  readonly provider: string;
  readonly responseText?: string;
  readonly chatTaskId?: string;
  readonly durationMs?: number;
}

export type VoiceEventType =
  | "voice.started"
  | "voice.stopped"
  | "voice.detected"
  | "voice.transcribed"
  | "voice.intent"
  | "voice.executed"
  | "voice.response"
  | "voice.status"
  | "voice.partial"
  | "voice.final"
  | "voice.execution"
  | "voice.completed";

export interface VoiceEvent {
  readonly type: VoiceEventType;
  readonly at: string;
  readonly payload: unknown;
}

export interface MicPermissionState {
  readonly granted: boolean;
  readonly reason: string;
}

export interface VoiceSecurityState {
  readonly microphone: MicPermissionState;
  readonly providerAuthenticated: boolean;
  readonly sessionValid: boolean;
}
