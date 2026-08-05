/**
 * Global Runtime Engine — Sprint 28.1.
 * Publishes platform state; modules subscribe via enterpriseEventBus + hooks.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { useProductionStore } from "@/ai-production-studio/productionStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { healthService } from "./healthService";
import { jobManager } from "./jobManager";
import { aiAgentRuntime } from "./aiAgentRuntime";
import { productionRuntime } from "./productionRuntime";
import {
  RUNTIME_ENGINE_VERSION,
  RUNTIME_TICK_MS,
  type RuntimeMetrics,
  type RuntimeSnapshot,
  type RuntimeStreamKind,
} from "./types";

type Listener = (snap: RuntimeSnapshot) => void;

const listeners = new Set<Listener>();
let started = false;
let tickTimer: number | null = null;
let healthUnsub: (() => void) | null = null;
let tick = 0;
let cpuPct = 18;
let memoryPct = 42;
let gpuPct = 8;
/** Stable snapshot for useSyncExternalStore — new object only on emit. */
let cachedSnap: RuntimeSnapshot | null = null;

function now() {
  return new Date().toISOString();
}

function readMetrics(): RuntimeMetrics {
  const counts = jobManager.counts();
  const health = healthService.getItems();
  const providers = health.filter((h) => h.id === "providers" || h.id === "mcp" || h.id === "voice");
  const providersOnline = providers.filter((p) => p.tone === "ok").length;
  const depths = productionRuntime.depths();
  let sessions = 1;
  try {
    sessions = Math.max(1, useWorkspaceManager.getState().tabs?.length || 1);
  } catch {
    /* ignore */
  }
  return {
    cpuPct: Math.round(cpuPct),
    memoryPct: Math.round(memoryPct),
    gpuPct: Math.round(gpuPct),
    workers: productionRuntime.workers().filter((w) => w.status !== "offline").length,
    sessions,
    jobsRunning: counts.running,
    jobsWaiting: counts.waiting + counts.retrying,
    providersOnline,
    providersTotal: Math.max(providers.length, 3),
    agentsActive: aiAgentRuntime.activeCount(),
    heartbeatAt: now(),
    tick,
    queueProduction: depths.production,
    queueTask: depths.task,
    queueRender: depths.render,
    queueGeneration: depths.generation,
    queuePublishing: depths.publishing,
  };
}

function buildSnapshot(): RuntimeSnapshot {
  return {
    version: RUNTIME_ENGINE_VERSION,
    status: healthService.getLevel(),
    metrics: readMetrics(),
    healthItems: healthService.getItems(),
    jobs: jobManager.list(),
    agents: aiAgentRuntime.list(),
    productionWorkers: productionRuntime.workers(),
    queueAnalytics: productionRuntime.analytics(),
    updatedAt: now(),
  };
}

function emit(kind: RuntimeStreamKind = "runtime") {
  const snap = buildSnapshot();
  cachedSnap = snap;
  listeners.forEach((l) => l(snap));
  enterpriseEventBus.publish({
    type: "runtime_update",
    source: "system",
    payload: {
      stream: kind,
      status: snap.status,
      tick: snap.metrics.tick,
      jobsRunning: snap.metrics.jobsRunning,
      agentsActive: snap.metrics.agentsActive,
      cpuPct: snap.metrics.cpuPct,
      memoryPct: snap.metrics.memoryPct,
      gpuPct: snap.metrics.gpuPct,
      queueRender: snap.metrics.queueRender,
      queueGeneration: snap.metrics.queueGeneration,
      queuePublishing: snap.metrics.queuePublishing,
    },
  });
}

function syncProduction() {
  try {
    const jobs = useProductionStore.getState().jobs;
    if (jobs?.length) jobManager.syncProductionJobs(jobs);
  } catch {
    /* store may be empty pre-hydrate */
  }
}

function onTick() {
  tick += 1;
  // Smooth local estimates (browser has no process CPU API)
  cpuPct = Math.min(92, Math.max(8, cpuPct + (Math.random() * 6 - 3)));
  memoryPct = Math.min(88, Math.max(20, memoryPct + (Math.random() * 4 - 2)));
  gpuPct = Math.min(80, Math.max(0, gpuPct + (Math.random() * 5 - 2)));
  jobManager.tick();
  productionRuntime.tick();
  aiAgentRuntime.tick();
  syncProduction();
  emit(tick % 5 === 0 ? "heartbeat" : tick % 3 === 0 ? "production" : "runtime");
}

export const runtimeEngine = {
  start() {
    if (started || typeof window === "undefined") return;
    started = true;
    healthService.start();
    healthUnsub = healthService.subscribe(() => emit("provider"));
    syncProduction();
    emit("heartbeat");
    tickTimer = window.setInterval(onTick, RUNTIME_TICK_MS);
  },

  stop() {
    if (!started) return;
    started = false;
    if (tickTimer != null) {
      window.clearInterval(tickTimer);
      tickTimer = null;
    }
    healthUnsub?.();
    healthUnsub = null;
    healthService.stop();
  },

  isStarted() {
    return started;
  },

  subscribe(listener: Listener) {
    listeners.add(listener);
    this.start();
    listener(this.getSnapshot());
    return () => {
      listeners.delete(listener);
    };
  },

  getSnapshot() {
    if (!cachedSnap) cachedSnap = buildSnapshot();
    return cachedSnap;
  },

  publishStream(kind: RuntimeStreamKind, payload?: Record<string, unknown>) {
    const type =
      kind === "ai"
        ? "ai_request"
        : kind === "production" || kind === "queue"
          ? "job_update"
          : kind === "workflow"
            ? "workflow_update"
            : kind === "provider"
              ? "provider_update"
              : kind === "desktop"
                ? "desktop_update"
                : kind === "city"
                  ? "city_update"
                  : kind === "notification"
                    ? "notification"
                    : "runtime_update";
    enterpriseEventBus.publish({
      type,
      source: "system",
      payload: { stream: kind, ...payload },
    });
  },
};
