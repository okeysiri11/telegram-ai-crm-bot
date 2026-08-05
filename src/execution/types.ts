/**
 * Enterprise Execution Planner — types.
 * Executes ChatGPT engineering specs; never invents architecture.
 */

export type AgentRole =
  | "developer"
  | "ui"
  | "documentation"
  | "qa"
  | "review"
  | "build"
  | "deploy";

export type TaskStatus =
  | "pending"
  | "ready"
  | "running"
  | "blocked"
  | "completed"
  | "failed"
  | "skipped";

export type PlanStatus =
  | "draft"
  | "ready"
  | "running"
  | "completed"
  | "failed"
  | "partial";

export interface EngineeringSpecification {
  readonly mission: string;
  readonly objective: string;
  readonly requirements: readonly string[];
  readonly files: readonly string[];
  readonly modules: readonly string[];
  readonly tests: readonly string[];
  readonly acceptanceCriteria: readonly string[];
  readonly raw?: string;
}

export interface WorkPackage {
  readonly mission: string;
  readonly goal: string;
  readonly files: readonly string[];
  readonly expectedResult: string;
  readonly validation: readonly string[];
}

export interface ExecutionTask {
  readonly id: string;
  readonly planId: string;
  readonly title: string;
  readonly role: AgentRole;
  readonly agentId: string;
  readonly priority: number;
  readonly dependencies: readonly string[];
  readonly workPackage: WorkPackage;
  status: TaskStatus;
  progress: number;
  readonly logs: string[];
  result?: unknown;
  error?: string;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  parallelGroup?: number;
}

export interface ExecutionPlanSnapshot {
  readonly id: string;
  readonly status: PlanStatus;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly startedAt: string | null;
  readonly completedAt: string | null;
  readonly specification: EngineeringSpecification;
  readonly tasks: readonly ExecutionTask[];
  readonly graph: {
    readonly nodes: readonly { id: string; role: AgentRole; status: TaskStatus }[];
    readonly edges: readonly { from: string; to: string }[];
  };
  readonly runningAgents: readonly string[];
  readonly completedCount: number;
  readonly failedCount: number;
  readonly blockedCount: number;
  readonly progress: number;
}

export interface ExecutionReport {
  readonly planId: string;
  readonly generatedAt: string;
  readonly status: PlanStatus;
  readonly completedTasks: readonly string[];
  readonly failedTasks: readonly string[];
  readonly warnings: readonly string[];
  readonly buildStatus: "passed" | "failed" | "skipped";
  readonly testStatus: "passed" | "failed" | "skipped";
  readonly filesChanged: readonly string[];
  readonly nextRecommendations: readonly string[];
  readonly summary: string;
}

export type ExecutionEventType =
  | "plan.created"
  | "plan.started"
  | "task.assigned"
  | "task.started"
  | "task.completed"
  | "task.failed"
  | "plan.completed";

export interface ExecutionEvent {
  readonly type: ExecutionEventType;
  readonly at: string;
  readonly payload: unknown;
}

/** Maps logical planner roles → registered Orchestrator agent ids. */
export const ROLE_TO_AGENT: Readonly<Record<AgentRole, string>> = {
  developer: "agent.developer",
  ui: "agent.developer",
  documentation: "agent.research",
  qa: "agent.qa",
  review: "agent.reviewer",
  build: "agent.automation",
  deploy: "agent.automation",
};
