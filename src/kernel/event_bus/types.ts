/**
 * Enterprise Event Bus shared types.
 * Provider-independent. No business-module imports.
 */

export type EventDeliveryMode = "sync" | "async" | "delayed";

export type EventPriority = number; // higher = sooner (default 0)

export interface EventMetadata {
  readonly correlationId?: string;
  readonly causationId?: string;
  readonly source?: string;
  readonly tenantId?: string;
  readonly packageId?: string;
  readonly [key: string]: unknown;
}

export interface EventInput<TPayload = unknown> {
  readonly type: string;
  readonly payload?: TPayload;
  readonly priority?: EventPriority;
  readonly mode?: EventDeliveryMode;
  readonly delayMs?: number;
  readonly sticky?: boolean;
  readonly metadata?: EventMetadata;
  /** Optional client-supplied id; otherwise generated. */
  readonly id?: string;
}

export interface ADOSEvent<TPayload = unknown> {
  readonly id: string;
  readonly type: string;
  readonly payload: TPayload;
  readonly priority: EventPriority;
  readonly mode: EventDeliveryMode;
  readonly delayMs: number;
  readonly sticky: boolean;
  readonly metadata: EventMetadata;
  readonly timestamp: string;
  readonly sequence: number;
}

export type EventHandler<TPayload = unknown> = (
  event: ADOSEvent<TPayload>,
) => void | Promise<void>;

export interface SubscribeOptions {
  readonly priority?: EventPriority;
  readonly once?: boolean;
  readonly filter?: EventFilterFn;
  readonly async?: boolean;
}

export type EventFilterFn = (event: ADOSEvent) => boolean;

export interface EventFilterCriteria {
  readonly types?: readonly string[];
  readonly typePattern?: string;
  readonly minPriority?: number;
  readonly maxPriority?: number;
  readonly source?: string;
  readonly since?: string;
  readonly until?: string;
  readonly stickyOnly?: boolean;
  readonly predicate?: EventFilterFn;
}

export interface Subscription {
  readonly id: string;
  readonly eventType: string;
  readonly priority: EventPriority;
  readonly once: boolean;
  unsubscribe(): void;
}

export interface ReplayOptions {
  readonly filter?: EventFilterCriteria;
  readonly limit?: number;
  /** Re-dispatch through current subscribers (default true). */
  readonly dispatch?: boolean;
}

export interface EventHistoryOptions {
  /** Ring buffer capacity. Default 100_000. */
  readonly capacity?: number;
}

export interface EventBusOptions {
  readonly history?: EventHistoryOptions;
  /** Max delayed timers outstanding. Default 100_000. */
  readonly maxDelayed?: number;
  /** Preserve insertion order among equal priorities. */
  readonly stablePriority?: boolean;
}

/** Well-known platform event type constants (communication backbone). */
export const StandardEventTypes = {
  TaskCreated: "TaskCreated",
  TaskAssigned: "TaskAssigned",
  TaskStarted: "TaskStarted",
  TaskCompleted: "TaskCompleted",
  TaskFailed: "TaskFailed",
  AgentStarted: "AgentStarted",
  AgentStopped: "AgentStopped",
  ProviderConnected: "ProviderConnected",
  PluginLoaded: "PluginLoaded",
  KnowledgeUpdated: "KnowledgeUpdated",
  MemoryUpdated: "MemoryUpdated",
  WorkflowStarted: "WorkflowStarted",
  WorkflowFinished: "WorkflowFinished",
  SecurityAlert: "SecurityAlert",
  SystemShutdown: "SystemShutdown",
  BootCompleted: "BootCompleted",
} as const;

export type StandardEventType =
  (typeof StandardEventTypes)[keyof typeof StandardEventTypes];
