/**
 * Enterprise Workflow Engine types.
 * Depends only on Kernel services (Event Bus / Service Mesh via DI).
 * No business-module imports.
 */

export type WorkflowInstanceStatus =
  | "Created"
  | "Running"
  | "WaitingApproval"
  | "WaitingEvent"
  | "Suspended"
  | "Completed"
  | "Failed"
  | "Compensating"
  | "Compensated"
  | "Cancelled";

export type WorkflowStepKind =
  | "task"
  | "parallel"
  | "condition"
  | "approval"
  | "compensation"
  | "delay"
  | "event-wait";

export interface RetryPolicy {
  readonly maxAttempts: number;
  readonly backoffMs?: number;
  readonly backoffMultiplier?: number;
}

export interface StepTimeout {
  readonly ms: number;
}

export type ConditionFn = (ctx: WorkflowContextData) => boolean;

export type StepHandler = (
  ctx: WorkflowContextData,
  input: unknown,
) => unknown | Promise<unknown>;

export interface WorkflowContextData {
  readonly instanceId: string;
  readonly definitionId: string;
  get<T = unknown>(key: string): T | undefined;
  set(key: string, value: unknown): void;
  entries(): Readonly<Record<string, unknown>>;
}

export interface WorkflowStepInit {
  readonly id: string;
  readonly name?: string;
  readonly kind: WorkflowStepKind;
  /** Next step(s) after success — sequential uses first; parallel lists children. */
  readonly next?: readonly string[];
  /** On failure jump (optional). */
  readonly onError?: string;
  /** Compensation step id. */
  readonly compensateWith?: string;
  readonly retry?: RetryPolicy;
  readonly timeout?: StepTimeout;
  /** Condition step */
  readonly condition?: ConditionFn;
  readonly whenTrue?: string;
  readonly whenFalse?: string;
  /** Task: mesh capability or local handler id */
  readonly capability?: string;
  readonly handlerId?: string;
  readonly method?: string;
  /** Parallel join: wait for all | any */
  readonly join?: "all" | "any";
  /** Event wait type */
  readonly waitEventType?: string;
  readonly approvalRole?: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface WorkflowDefinitionInit {
  readonly id: string;
  readonly name?: string;
  readonly version: string;
  readonly start: string;
  readonly steps: readonly WorkflowStepInit[];
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface WorkflowHistoryEntry {
  readonly id: string;
  readonly instanceId: string;
  readonly at: string;
  readonly type: string;
  readonly stepId?: string;
  readonly message?: string;
  readonly data?: unknown;
}

export interface StartWorkflowOptions {
  readonly input?: Readonly<Record<string, unknown>>;
  readonly instanceId?: string;
}

export interface ApprovalDecision {
  readonly approved: boolean;
  readonly comment?: string;
  readonly actor?: string;
}

export interface WorkflowEngineOptions {
  /** Optional enterprise event bus for WorkflowStarted/Finished + event-wait. */
  readonly eventBus?: {
    publish(event: {
      type: string;
      payload?: unknown;
      mode?: "sync" | "async";
    }): Promise<unknown>;
    subscribe(
      type: string,
      handler: (event: { type: string; payload: unknown }) => void,
    ): { unsubscribe(): void };
  };
  /** Optional service mesh for capability task steps. */
  readonly serviceMesh?: {
    route<T = unknown>(request: {
      capability?: string;
      serviceId?: string;
      method: string;
      input?: unknown;
    }): Promise<{ ok: boolean; data?: T; error?: string }>;
  };
  readonly defaultRetry?: RetryPolicy;
}
