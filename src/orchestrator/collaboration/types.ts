/**
 * Multi-agent collaboration types — agents never talk peer-to-peer.
 */

export type CollaborationWorkflowStatus =
  | "Created"
  | "Running"
  | "Paused"
  | "Completed"
  | "Failed"
  | "Cancelled";

export type CollaborationStepMode = "sequential" | "parallel" | "conditional";

export interface CollaborationStepDef {
  readonly id: string;
  readonly name: string;
  readonly agentId: string;
  readonly capability?: string;
  readonly mode?: CollaborationStepMode;
  /** Parallel group id — steps with same group run together. */
  readonly parallelGroup?: string;
  /** Skip if context key equals value */
  readonly when?: { readonly key: string; readonly equals: unknown };
  readonly retries?: number;
  readonly estimatedMs?: number;
}

export interface WorkflowTemplate {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly category: string;
  readonly priority?: number;
  readonly estimatedMs: number;
  readonly steps: readonly CollaborationStepDef[];
}

export interface ContextArtifact {
  readonly id: string;
  readonly kind: "file" | "prompt" | "decision" | "result" | "log" | "other";
  readonly name: string;
  readonly at: string;
  readonly agentId?: string;
  readonly data: unknown;
}

export interface TimelineEvent {
  readonly id: string;
  readonly at: string;
  readonly type: string;
  readonly workflowId?: string;
  readonly agentId?: string;
  readonly providerId?: string;
  readonly stepId?: string;
  readonly durationMs?: number;
  readonly result?: unknown;
  readonly error?: string;
  readonly artifacts?: unknown;
  readonly message?: string;
}

export interface CollaborationStepState {
  readonly id: string;
  readonly agentId: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  attempts: number;
  output?: unknown;
  error?: string;
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
}

export interface CollaborationWorkflowSnapshot {
  readonly id: string;
  readonly templateId: string;
  readonly name: string;
  readonly status: CollaborationWorkflowStatus;
  readonly priority: number;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly estimatedMs: number;
  readonly elapsedMs: number;
  readonly currentStepIds: readonly string[];
  readonly steps: readonly CollaborationStepState[];
  readonly graph: {
    readonly nodes: Array<{ id: string; agentId: string; label: string }>;
    readonly edges: Array<{ from: string; to: string }>;
  };
  readonly contextKeys: readonly string[];
  readonly artifactCount: number;
}
