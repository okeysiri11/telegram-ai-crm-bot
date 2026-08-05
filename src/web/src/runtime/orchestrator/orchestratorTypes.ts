/**
 * Enterprise Orchestrator Runtime types — Sprint 29.8.
 * Coordination layer only — does not replace existing runtimes.
 */

export const ORCHESTRATOR_RUNTIME_VERSION = "29.8";
export const ORCHESTRATOR_PERSIST_KEY = "ews_orchestrator_runtime_v1";
export const ORCHESTRATOR_API_PREFIX = "/api/enterprise-orchestrator/v1";

export type RuntimeId =
  | "business_network"
  | "digital_citizen"
  | "asset"
  | "life"
  | "spatial"
  | "city_visualization"
  | "interaction"
  | "intelligence"
  | "workflow"
  | "automation";

export type RuntimeHealthStatus =
  | "healthy"
  | "starting"
  | "stopped"
  | "error"
  | "busy"
  | "maintenance";

export type SchedulerOperation =
  | "startup"
  | "shutdown"
  | "reload"
  | "rebuild"
  | "warm_cache"
  | "refresh"
  | "sync";

export type OrchestratorEventName =
  | "RuntimeRegistered"
  | "RuntimeStarted"
  | "RuntimeStopped"
  | "RuntimeHealthChanged"
  | "ScheduleEnqueued"
  | "ScheduleCompleted"
  | "EventRouted"
  | "PlatformHealthUpdated";

export type RuntimeDescriptor = {
  id: RuntimeId;
  label: string;
  version: string;
  status: RuntimeHealthStatus;
  dependencies: RuntimeId[];
  health: RuntimeHealthReport;
  events: string[];
  api: string;
  permissions: string[];
  route?: string;
};

export type RuntimeHealthReport = {
  status: RuntimeHealthStatus;
  message?: string;
  checkedAt: string;
  latencyMs?: number;
  details?: Record<string, unknown>;
};

export type RuntimeAdapter = {
  id: RuntimeId;
  label: string;
  version: string;
  dependencies: RuntimeId[];
  events: string[];
  api: string;
  permissions: string[];
  route?: string;
  startup: () => unknown;
  shutdown?: () => void;
  reload?: () => unknown;
  rebuild?: () => unknown;
  warmCache?: () => unknown;
  refresh?: () => unknown;
  sync?: () => unknown;
  probeHealth: () => RuntimeHealthReport;
};

export type ScheduleJob = {
  id: string;
  operation: SchedulerOperation;
  runtimeId?: RuntimeId;
  status: "pending" | "running" | "completed" | "failed";
  enqueuedAt: string;
  startedAt?: string;
  finishedAt?: string;
  error?: string;
  message?: string;
};

export type RoutedEvent = {
  id: string;
  at: string;
  busType: string;
  targetRuntimeIds: RuntimeId[];
  payload?: Record<string, unknown>;
};

export type PlatformHealth = {
  status: RuntimeHealthStatus;
  healthy: number;
  starting: number;
  stopped: number;
  error: number;
  busy: number;
  maintenance: number;
  total: number;
  updatedAt: string;
};

export type DependencyEdge = {
  from: RuntimeId;
  to: RuntimeId;
};
