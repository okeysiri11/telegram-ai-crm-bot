/**
 * Sprint 46.4 — Unified Intent Bar types & status labels (RU).
 */

export type UnifiedIntentKind =
  | "CHAT"
  | "SEARCH"
  | "COMMAND"
  | "CREATE"
  | "NAVIGATE"
  | "WORKFLOW";

export type InteractionStatus =
  | "received"
  | "routing"
  | "running"
  | "waiting_user"
  | "completed"
  | "failed"
  | "cancelled";

export const STATUS_LABEL_RU: Record<InteractionStatus, string> = {
  received: "Принято",
  routing: "Определяю задачу…",
  running: "Выполняю",
  waiting_user: "Нужно уточнение",
  completed: "Готово",
  failed: "Ошибка",
  cancelled: "Отменено",
};

export type IntentSearchHit = {
  id: string;
  title: string;
  path: string;
  category: string;
  categoryLabel: string;
};

export type IntentInteraction = {
  id: string;
  text: string;
  intent: UnifiedIntentKind;
  status: InteractionStatus;
  createdAt: number;
  updatedAt: number;
  /** Meaningful progress for the user (Ищу… / Анализирую…) */
  progressLabel?: string;
  reply?: string;
  resultPath?: string;
  resultCount?: number;
  hits?: IntentSearchHit[];
  error?: string;
  verticalId?: string;
  /** Debug only — never show in client UI by default */
  debug?: {
    route?: string;
    commandId?: string;
    latencyMs?: number;
    score?: number;
  };
};

export type VerticalIntentConfig = {
  verticalId: string;
  contextLabel: string;
  searchScope: string[];
  aiSpecialist?: string;
  availableActions: string[];
};
