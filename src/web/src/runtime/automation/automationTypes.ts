/**
 * Automation Engine types — Sprint 28.9.
 */

export const AUTOMATION_ENGINE_VERSION = "28.9";
export const AUTOMATION_PERSIST_KEY = "ews_automation_v1";
export const AUTOMATION_HISTORY_KEY = "ews_automation_history_v1";

export type AutomationTriggerKind =
  | "manual"
  | "startup"
  | "shutdown"
  | "schedule"
  | "webhook"
  | "event_bus"
  | "command"
  | "ai_intent"
  | "notification"
  | "workflow_completed";

export type AutomationQueueStatus =
  | "pending"
  | "running"
  | "waiting"
  | "completed"
  | "failed"
  | "cancelled"
  | "retry";

export type ErrorPolicy = "fail" | "continue" | "retry" | "skip";

export type AutomationPolicy = {
  retryCount: number;
  timeoutMs: number;
  backoffMs: number;
  concurrency: number;
  priority: number;
  errorPolicy: ErrorPolicy;
};

export type AutomationTrigger = {
  kind: AutomationTriggerKind;
  /** schedule: interval ms or cron-like "every:Nms" */
  scheduleMs?: number;
  /** event_bus / workflow_completed event type */
  eventType?: string;
  /** command action/id */
  commandId?: string;
  /** ai intent keyword */
  intentMatch?: string;
  /** webhook path token */
  webhookToken?: string;
  /** notification title match */
  notificationMatch?: string;
  enabled?: boolean;
};

export type AutomationDefinition = {
  id: string;
  name: string;
  description?: string;
  /** Workflow Runtime definition id — required execution target */
  workflowId: string;
  triggers: AutomationTrigger[];
  policy: AutomationPolicy;
  enabled: boolean;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
};

export type AutomationJob = {
  id: string;
  automationId: string;
  workflowId: string;
  status: AutomationQueueStatus;
  priority: number;
  attempt: number;
  triggerKind: AutomationTriggerKind;
  workflowSessionId?: string;
  error?: string;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
  nextRetryAt?: string;
  timeline: AutomationTimelineEvent[];
};

export type AutomationTimelineEvent = {
  id: string;
  at: string;
  type: string;
  message: string;
};

export type AutomationHistoryEntry = {
  id: string;
  jobId: string;
  automationId: string;
  workflowId: string;
  status: AutomationQueueStatus;
  triggerKind: AutomationTriggerKind;
  attempt: number;
  durationMs?: number;
  error?: string;
  at: string;
};

export const DEFAULT_POLICY: AutomationPolicy = {
  retryCount: 2,
  timeoutMs: 60_000,
  backoffMs: 500,
  concurrency: 2,
  priority: 50,
  errorPolicy: "retry",
};
