/**
 * AI Orchestrator shared types.
 * Agents communicate only through the Orchestrator — never peer-to-peer.
 */

export type AgentLiveStatus =
  | "Idle"
  | "Running"
  | "Busy"
  | "Waiting"
  | "Offline"
  | "Error";

export type ProviderId =
  | "local"
  | "cursor"
  | "openai"
  | "claude"
  | "github"
  | "telegram";

export interface AgentCapability {
  readonly id: string;
  readonly description: string;
}

export interface AgentHealth {
  readonly status: "OK" | "DEGRADED" | "DOWN";
  readonly message?: string;
  readonly checkedAt: string;
}

export interface AgentTaskInput {
  readonly taskId: string;
  readonly type: string;
  readonly payload: unknown;
  readonly provider?: ProviderId;
}

export interface AgentTaskResult {
  readonly taskId: string;
  readonly agentId: string;
  readonly ok: boolean;
  readonly output: unknown;
  readonly error?: string;
  readonly durationMs: number;
  readonly provider: ProviderId;
  readonly completedAt: string;
}

export interface AgentMetrics {
  readonly tasksCompleted: number;
  readonly successes: number;
  readonly errors: number;
  readonly avgResponseTimeMs: number;
  readonly load: number;
  readonly queueSize: number;
  readonly runningTasks: number;
}

export interface AgentSnapshot {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly provider: ProviderId;
  readonly skills: readonly string[];
  readonly status: AgentLiveStatus;
  readonly memory: string;
  readonly currentTask: string | null;
  readonly queueSize: number;
  readonly runningTasks: number;
  readonly responseTimeMs: number;
  readonly lastExecution: string | null;
  readonly version: string;
  readonly health: AgentHealth;
  readonly metrics: AgentMetrics;
  readonly capabilities: readonly AgentCapability[];
}

export interface AgentLogEntry {
  readonly id: string;
  readonly at: string;
  readonly agentId: string;
  readonly level: "info" | "warn" | "error";
  readonly message: string;
  readonly taskId?: string;
  readonly meta?: unknown;
}

export interface OrchestratorTaskRequest {
  readonly task?: string;
  readonly type?: string;
  readonly payload?: unknown;
  readonly preferredAgent?: string;
  readonly capability?: string;
  readonly provider?: ProviderId;
}

export interface OrchestratorTaskResponse {
  readonly taskId: string;
  readonly agentId: string;
  readonly status: "completed" | "failed" | "queued";
  readonly result?: AgentTaskResult;
  readonly error?: string;
}

export interface OrchestratorStatus {
  readonly id: "ados.orchestrator";
  readonly name: "AI Orchestrator";
  readonly health: "OK" | "DEGRADED" | "DOWN";
  readonly agents: number;
  readonly runningTasks: number;
  readonly queueSize: number;
  readonly liveStatus: AgentLiveStatus | "Ready";
}
