/**
 * Enterprise Runtime types — Sprint 28.1 / 28.2.
 */

import type { StatusTone } from "@/shell/enterprise/statusCatalog";

export const RUNTIME_ENGINE_VERSION = "28.2";
export const RUNTIME_TICK_MS = 12_000;
export const HEALTH_POLL_MS = 45_000;

/** Production Center queue lanes — projections over Job Manager (no second engine). */
export type ProductionQueueKind =
  | "production"
  | "task"
  | "render"
  | "generation"
  | "publishing";

export type UniversalPipelineId =
  | "image_generation"
  | "video_generation"
  | "audio_generation"
  | "voice_generation"
  | "avatar_generation"
  | "reels_generation"
  | "campaign_generation"
  | "publishing";

export type HealthLevel = "healthy" | "warning" | "critical" | "offline";

export type RuntimeHealthId =
  | "runtime"
  | "api"
  | "database"
  | "providers"
  | "voice"
  | "mcp"
  | "queue"
  | "build"
  | "version"
  | "frontend"
  | "ai"
  | "memory";

export type RuntimeHealthItem = {
  id: RuntimeHealthId;
  label: string;
  tone: StatusTone;
  detail: string;
};

export type JobLifecycle =
  | "running"
  | "waiting"
  | "completed"
  | "failed"
  | "cancelled"
  | "retrying"
  | "paused";

export type JobPriority = "critical" | "high" | "normal" | "low";

/** Sprint 30.5 — AI task pipeline stages (execution view). */
export type AiTaskStage =
  | "waiting"
  | "preparing"
  | "running"
  | "review"
  | "completed"
  | "failed";

export type RuntimeJobLog = {
  at: string;
  message: string;
  level?: "info" | "warn" | "error";
};

export type RuntimeJobRecord = {
  id: string;
  title: string;
  status: JobLifecycle;
  progress: number;
  etaSec: number | null;
  source: "production" | "ai" | "workflow" | "system" | "queue";
  startedAt: string;
  updatedAt: string;
  retries: number;
  /** Sprint 28.2 — Production Runtime metadata (optional). */
  queueKind?: ProductionQueueKind;
  studioId?: string;
  pipelineId?: string;
  universalPipelineId?: UniversalPipelineId;
  agentIds?: string[];
  workerId?: string | null;
  /** Sprint 30.5 — task execution / security */
  priority?: JobPriority;
  stage?: AiTaskStage;
  orgId?: string;
  workspaceId?: string;
  agentId?: string;
  logs?: RuntimeJobLog[];
  history?: RuntimeJobLog[];
};

export type AgentLifecyclePhase =
  | "idle"
  | "planning"
  | "waiting"
  | "running"
  | "paused"
  | "review"
  | "completed"
  | "failed"
  | "cancelled"
  | "retry";

export type AiAgentRuntime = {
  id: string;
  name: string;
  status: "idle" | "busy" | "waiting" | "error" | "offline";
  task: string | null;
  queueDepth: number;
  memoryMb: number;
  workflow: string | null;
  health: HealthLevel;
  updatedAt: string;
  /** Sprint 32.1 AgentOS */
  role?: string;
  version?: string;
  phase?: AgentLifecyclePhase;
  permissions?: string[];
  tokensUsed?: number;
  costUsd?: number;
  tenantId?: string;
};

export type RuntimeMetrics = {
  cpuPct: number;
  memoryPct: number;
  gpuPct: number;
  workers: number;
  sessions: number;
  jobsRunning: number;
  jobsWaiting: number;
  providersOnline: number;
  providersTotal: number;
  agentsActive: number;
  heartbeatAt: string;
  tick: number;
  /** Sprint 28.2 production queue depths (cached on tick). */
  queueProduction?: number;
  queueTask?: number;
  queueRender?: number;
  queueGeneration?: number;
  queuePublishing?: number;
};

export type ProductionWorkerRecord = {
  id: string;
  label: string;
  queueKind: ProductionQueueKind;
  status: "idle" | "busy" | "offline";
  jobId: string | null;
  capacity: number;
  load: number;
  updatedAt: string;
};

export type QueueAnalyticsSnapshot = {
  byQueue: Record<ProductionQueueKind, { length: number; running: number; failed: number; avgEtaSec: number }>;
  throughputPerTick: number;
  retryRate: number;
  workersBusy: number;
  workersTotal: number;
  estimatedClearSec: number;
  updatedAt: string;
};

export type RuntimeSnapshot = {
  version: string;
  status: HealthLevel;
  metrics: RuntimeMetrics;
  healthItems: RuntimeHealthItem[];
  jobs: RuntimeJobRecord[];
  agents: AiAgentRuntime[];
  productionWorkers?: ProductionWorkerRecord[];
  queueAnalytics?: QueueAnalyticsSnapshot;
  updatedAt: string;
};

export type RuntimeStreamKind =
  | "runtime"
  | "notification"
  | "ai"
  | "production"
  | "queue"
  | "provider"
  | "workflow"
  | "desktop"
  | "city"
  | "heartbeat";

export function toneToHealth(tone: StatusTone): HealthLevel {
  if (tone === "ok") return "healthy";
  if (tone === "warn") return "warning";
  if (tone === "err") return "critical";
  return "offline";
}

export function aggregateHealth(items: RuntimeHealthItem[]): HealthLevel {
  if (!items.length) return "offline";
  if (items.some((i) => i.tone === "err")) return "critical";
  if (items.some((i) => i.tone === "warn")) return "warning";
  if (items.every((i) => i.tone === "unknown")) return "offline";
  return "healthy";
}
