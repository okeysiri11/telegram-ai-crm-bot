/**
 * Workflow Runtime types — Sprint 28.8.
 */

export const WORKFLOW_RUNTIME_VERSION = "28.8";
export const WORKFLOW_PERSIST_KEY = "ews_workflow_runtime_v1";

export type WorkflowNodeKind =
  | "start"
  | "end"
  | "sequential"
  | "parallel"
  | "condition"
  | "loop"
  | "delay"
  | "wait_event"
  | "ai_action"
  | "approval"
  | "notification"
  | "command"
  | "http"
  | "webhook"
  | "script";

export type WorkflowStatus =
  | "idle"
  | "running"
  | "paused"
  | "waiting"
  | "completed"
  | "failed"
  | "cancelled";

export type WorkflowNodeDef = {
  id: string;
  kind: WorkflowNodeKind;
  label: string;
  /** Next node ids (sequential / default branch). */
  next?: string[];
  /** Condition true/false branches */
  whenTrue?: string[];
  whenFalse?: string[];
  /** Loop body + after */
  body?: string[];
  maxIterations?: number;
  /** delay ms */
  delayMs?: number;
  /** wait_event: EnterpriseEventType or payload match */
  eventType?: string;
  eventMatch?: Record<string, unknown>;
  /** command / ai */
  commandId?: string;
  commandArgs?: Record<string, unknown>;
  utterance?: string;
  /** notification */
  notificationTitle?: string;
  notificationBody?: string;
  /** http / webhook */
  url?: string;
  method?: string;
  /** condition expression key in context.vars */
  conditionKey?: string;
  /** script id (future) */
  scriptId?: string;
  /** parallel child entry nodes */
  branches?: string[][];
};

export type WorkflowDefinition = {
  id: string;
  name: string;
  description?: string;
  version: string;
  entryNodeId: string;
  nodes: Record<string, WorkflowNodeDef>;
  tags?: string[];
  source?: "catalog" | "template" | "ai" | "dynamic";
};

export type WorkflowContext = {
  vars: Record<string, unknown>;
  memory: Record<string, unknown>;
  outputs: Record<string, unknown>;
  temp: Record<string, unknown>;
  meta: {
    workflowId: string;
    definitionId: string;
    startedAt: string;
    surface?: string;
    tenantId?: string | null;
  };
};

export type NodeExecutionRecord = {
  nodeId: string;
  kind: WorkflowNodeKind;
  label: string;
  status: "pending" | "running" | "done" | "failed" | "skipped" | "waiting";
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
  retryCount: number;
  error?: string;
  output?: unknown;
};

export type WorkflowLogEntry = {
  id: string;
  at: string;
  level: "info" | "warn" | "error" | "debug";
  message: string;
  nodeId?: string;
};

export type WorkflowSession = {
  id: string;
  definitionId: string;
  status: WorkflowStatus;
  context: WorkflowContext;
  nodeRecords: Record<string, NodeExecutionRecord>;
  cursor: string[];
  logs: WorkflowLogEntry[];
  startedAt: string;
  updatedAt: string;
  completedAt?: string;
  waitEventType?: string;
  waitUntil?: string;
  approvalPending?: boolean;
  retryCount: number;
  snapshotVersion: number;
};

export type WorkflowHistoryEntry = {
  id: string;
  sessionId: string;
  definitionId: string;
  name: string;
  status: WorkflowStatus;
  startedAt: string;
  completedAt?: string;
  durationMs?: number;
  error?: string;
};

export type WorkflowStartResult = {
  ok: boolean;
  sessionId?: string;
  error?: string;
  session?: WorkflowSession;
};
