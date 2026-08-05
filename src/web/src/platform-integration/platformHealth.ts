/**
 * Sprint 30.6 — Platform health derivation over healthService + runtimeEngine.
 * No second monitoring engine.
 */

import { healthService } from "@/enterprise-runtime/healthService";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { jobManager } from "@/enterprise-runtime/jobManager";
import { aiAgentRuntime } from "@/enterprise-runtime/aiAgentRuntime";
import type { HealthLevel, RuntimeHealthItem } from "@/enterprise-runtime/types";

export type PlatformHealthSnapshot = {
  level: HealthLevel;
  updatedAt: string | null;
  items: RuntimeHealthItem[];
  cpuPct: number;
  memoryPct: number;
  workersBusy: number;
  workersTotal: number;
  runtimeStatus: HealthLevel;
  apiTone: string;
  databaseTone: string;
  cacheTone: string;
  queueLength: number;
  agentsActive: number;
};

export function derivePlatformHealth(): PlatformHealthSnapshot {
  const items = healthService.getItems();
  const level = healthService.getLevel();
  const snap = runtimeEngine.getSnapshot();
  const counts = jobManager.counts();
  const queueLength = counts.waiting + counts.retrying + counts.running;
  const agentsActive = aiAgentRuntime.activeCount();
  const findTone = (id: string) => items.find((i) => i.id === id)?.tone || "unknown";

  return {
    level,
    updatedAt: healthService.getUpdatedAt() || snap.updatedAt,
    items,
    cpuPct: snap.metrics.cpuPct,
    memoryPct: snap.metrics.memoryPct,
    workersBusy: snap.queueAnalytics?.workersBusy ?? Math.min(queueLength, snap.metrics.workers || 4),
    workersTotal: snap.queueAnalytics?.workersTotal ?? (snap.metrics.workers || 4),
    runtimeStatus: snap.status,
    apiTone: findTone("api"),
    databaseTone: findTone("database"),
    cacheTone: findTone("memory"),
    queueLength,
    agentsActive,
  };
}
