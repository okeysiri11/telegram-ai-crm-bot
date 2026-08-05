/**
 * Production Runtime — Sprint 28.2.
 * Facade over Job Manager + AI Agent Runtime + Health Service.
 * Does NOT create a second job engine.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { useNotificationStore } from "@/notifications/notificationStore";
import { jobManager } from "./jobManager";
import { aiAgentRuntime } from "./aiAgentRuntime";
import { healthService } from "./healthService";
import {
  UNIVERSAL_PIPELINES,
  universalPipelineById,
  type UniversalPipelineDef,
} from "./universalPipelines";
import type {
  JobLifecycle,
  ProductionQueueKind,
  ProductionWorkerRecord,
  QueueAnalyticsSnapshot,
  RuntimeJobRecord,
  UniversalPipelineId,
} from "./types";

const QUEUE_KINDS: ProductionQueueKind[] = [
  "production",
  "task",
  "render",
  "generation",
  "publishing",
];

type Listener = () => void;
const listeners = new Set<Listener>();

let workers: ProductionWorkerRecord[] = bootstrapWorkers();
let lastAnalytics: QueueAnalyticsSnapshot = emptyAnalytics();
let throughputCounter = 0;

function now() {
  return new Date().toISOString();
}

function emptyAnalytics(): QueueAnalyticsSnapshot {
  const byQueue = {} as QueueAnalyticsSnapshot["byQueue"];
  for (const q of QUEUE_KINDS) {
    byQueue[q] = { length: 0, running: 0, failed: 0, avgEtaSec: 0 };
  }
  return {
    byQueue,
    throughputPerTick: 0,
    retryRate: 0,
    workersBusy: 0,
    workersTotal: workers.length || 5,
    estimatedClearSec: 0,
    updatedAt: now(),
  };
}

function bootstrapWorkers(): ProductionWorkerRecord[] {
  const t = now();
  return [
    { id: "pw_prod_1", label: "Production Worker A", queueKind: "production", status: "idle", jobId: null, capacity: 2, load: 0, updatedAt: t },
    { id: "pw_task_1", label: "Task Worker A", queueKind: "task", status: "idle", jobId: null, capacity: 3, load: 0, updatedAt: t },
    { id: "pw_gen_1", label: "Generation Worker A", queueKind: "generation", status: "idle", jobId: null, capacity: 2, load: 0, updatedAt: t },
    { id: "pw_gen_2", label: "Generation Worker B", queueKind: "generation", status: "idle", jobId: null, capacity: 2, load: 0, updatedAt: t },
    { id: "pw_render_1", label: "Render Worker A", queueKind: "render", status: "idle", jobId: null, capacity: 1, load: 0, updatedAt: t },
    { id: "pw_pub_1", label: "Publishing Worker A", queueKind: "publishing", status: "idle", jobId: null, capacity: 2, load: 0, updatedAt: t },
  ];
}

function emitLocal() {
  listeners.forEach((l) => l());
}

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

function resolveAgentIds(names: string[]): string[] {
  const agents = aiAgentRuntime.list();
  return names.map((name) => {
    const hit = agents.find((a) => a.name.toLowerCase() === name.toLowerCase());
    return hit?.id || `agent_${name.toLowerCase().replace(/\s+/g, "_")}`;
  });
}

function assignAgents(names: string[], task: string, workflow: string) {
  const ids = resolveAgentIds(names);
  for (const id of ids) {
    const agent = aiAgentRuntime.list().find((a) => a.id === id);
    if (!agent) continue;
    aiAgentRuntime.setAgent(id, {
      status: "busy",
      task,
      queueDepth: Math.max(1, agent.queueDepth),
      workflow,
      health: "warning",
    });
  }
  return ids;
}

function queueOf(job: RuntimeJobRecord): ProductionQueueKind {
  return job.queueKind || (job.source === "production" ? "production" : "task");
}

function activeJobs(): RuntimeJobRecord[] {
  return jobManager.list().filter((j) =>
    ["running", "waiting", "retrying"].includes(j.status),
  );
}

function computeAnalytics(): QueueAnalyticsSnapshot {
  const all = jobManager.list();
  const byQueue = {} as QueueAnalyticsSnapshot["byQueue"];
  for (const q of QUEUE_KINDS) {
    const slice = all.filter((j) => queueOf(j) === q);
    const active = slice.filter((j) => j.status === "waiting" || j.status === "retrying" || j.status === "running");
    const running = slice.filter((j) => j.status === "running");
    const failed = slice.filter((j) => j.status === "failed");
    const etas = active.map((j) => j.etaSec ?? 0).filter((n) => n > 0);
    byQueue[q] = {
      length: active.length,
      running: running.length,
      failed: failed.length,
      avgEtaSec: etas.length ? Math.round(etas.reduce((a, b) => a + b, 0) / etas.length) : 0,
    };
  }
  const retries = all.filter((j) => j.retries > 0).length;
  const busy = workers.filter((w) => w.status === "busy").length;
  const totalLen = QUEUE_KINDS.reduce((n, q) => n + byQueue[q].length, 0);
  const avgEta = QUEUE_KINDS.reduce((n, q) => n + byQueue[q].avgEtaSec, 0) / QUEUE_KINDS.length;
  lastAnalytics = {
    byQueue,
    throughputPerTick: throughputCounter,
    retryRate: all.length ? retries / all.length : 0,
    workersBusy: busy,
    workersTotal: workers.length,
    estimatedClearSec: Math.round(avgEta * Math.max(1, totalLen / Math.max(1, busy))),
    updatedAt: now(),
  };
  throughputCounter = 0;
  return lastAnalytics;
}

function pickWorker(queue: ProductionQueueKind): ProductionWorkerRecord | null {
  const free = workers
    .filter((w) => w.queueKind === queue && w.status !== "offline" && w.load < w.capacity)
    .sort((a, b) => a.load - b.load);
  return free[0] || null;
}

function scheduleWaiting() {
  const waiting = jobManager
    .list()
    .filter((j) => j.status === "waiting" || j.status === "retrying")
    .filter((j) => j.source === "production" || j.queueKind);

  for (const job of waiting) {
    const q = queueOf(job);
    const worker = pickWorker(q);
    if (!worker) continue;
    jobManager.upsert({
      ...job,
      status: "running",
      progress: Math.max(job.progress, 20),
      workerId: worker.id,
      updatedAt: now(),
    });
    workers = workers.map((w) =>
      w.id === worker.id
        ? {
            ...w,
            status: "busy" as const,
            jobId: job.id,
            load: w.load + 1,
            updatedAt: now(),
          }
        : w,
    );
    if (job.agentIds?.length) {
      for (const aid of job.agentIds) {
        aiAgentRuntime.setAgent(aid, {
          status: "busy",
          task: job.title,
          workflow: job.universalPipelineId || "production_runtime",
          health: "warning",
        });
      }
    }
    throughputCounter += 1;
  }
}

function advanceRunning() {
  for (const job of jobManager.list().filter((j) => j.status === "running" && j.queueKind)) {
    if (job.progress >= 96) {
      jobManager.setStatus(job.id, "completed", 100);
      if (job.workerId) {
        workers = workers.map((w) =>
          w.id === job.workerId
            ? {
                ...w,
                status: "idle" as const,
                jobId: null,
                load: Math.max(0, w.load - 1),
                updatedAt: now(),
              }
            : w,
        );
      }
      if (job.agentIds?.length) {
        for (const aid of job.agentIds) {
          aiAgentRuntime.setAgent(aid, {
            status: "idle",
            task: null,
            workflow: null,
            health: "healthy",
            queueDepth: 0,
          });
        }
      }
      throughputCounter += 1;
      try {
        useNotificationStore.getState().push({
          title: "Production job completed",
          body: job.title,
          kind: "success",
        });
      } catch {
        /* optional */
      }
    }
  }
}

function inferQueueFromAutomation(kind: string, title: string): ProductionQueueKind {
  const t = `${kind} ${title}`.toLowerCase();
  if (t.includes("render")) return "render";
  if (t.includes("publish") || t.includes("schedule")) return "publishing";
  if (t.includes("generat") || t.includes("image") || t.includes("video") || t.includes("voice")) {
    return "generation";
  }
  if (kind === "batch" || kind === "queue") return "task";
  return "production";
}

export const productionRuntime = {
  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  queues(): ProductionQueueKind[] {
    return [...QUEUE_KINDS];
  },

  listQueue(kind: ProductionQueueKind): RuntimeJobRecord[] {
    return jobManager.list().filter((j) => queueOf(j) === kind);
  },

  queueLength(kind: ProductionQueueKind): number {
    return activeJobs().filter((j) => queueOf(j) === kind).length;
  },

  workers(): ProductionWorkerRecord[] {
    return workers.slice();
  },

  analytics(): QueueAnalyticsSnapshot {
    return lastAnalytics;
  },

  pipelines(): UniversalPipelineDef[] {
    return UNIVERSAL_PIPELINES.slice();
  },

  /** Enqueue a production job through Job Manager. */
  enqueue(input: {
    title: string;
    queueKind: ProductionQueueKind;
    studioId?: string;
    pipelineId?: string;
    universalPipelineId?: UniversalPipelineId;
    agents?: string[];
    etaSec?: number;
    status?: JobLifecycle;
  }): string {
    const id = uid("prj");
    const agentIds = input.agents?.length ? assignAgents(input.agents, input.title, input.universalPipelineId || "production_runtime") : [];
    jobManager.upsert({
      id,
      title: input.title,
      status: input.status || "waiting",
      progress: 5,
      etaSec: input.etaSec ?? 180,
      source: "production",
      startedAt: now(),
      retries: 0,
      queueKind: input.queueKind,
      studioId: input.studioId,
      pipelineId: input.pipelineId,
      universalPipelineId: input.universalPipelineId,
      agentIds,
      workerId: null,
    });
    enterpriseEventBus.publish({
      type: "job_update",
      source: "production",
      payload: { stream: "production", jobId: id, queueKind: input.queueKind },
    });
    emitLocal();
    return id;
  },

  /** Start a universal pipeline → generation (+ optional render/publish) jobs. */
  runUniversalPipeline(
    pipelineId: UniversalPipelineId,
    opts?: { title?: string; extraAgents?: string[]; pipelineRefId?: string },
  ): { jobIds: string[]; pipeline: UniversalPipelineDef } {
    const def = universalPipelineById(pipelineId);
    if (!def) throw new Error(`Unknown pipeline ${pipelineId}`);
    const agents = [...def.defaultAgents, ...(opts?.extraAgents || [])];
    const title = opts?.title || `${def.label} · run`;
    const jobIds: string[] = [];

    // Task orchestration job
    jobIds.push(
      this.enqueue({
        title: `Task · ${title}`,
        queueKind: "task",
        studioId: def.studioId,
        universalPipelineId: def.id,
        pipelineId: opts?.pipelineRefId,
        agents: agents.slice(0, 1),
        etaSec: 60,
      }),
    );

    // Primary work lane
    jobIds.push(
      this.enqueue({
        title: title,
        queueKind: def.primaryQueue,
        studioId: def.studioId,
        universalPipelineId: def.id,
        pipelineId: opts?.pipelineRefId,
        agents,
        etaSec: def.primaryQueue === "render" ? 300 : 180,
      }),
    );

    if (def.stages.includes("render") && def.primaryQueue !== "render") {
      jobIds.push(
        this.enqueue({
          title: `Render · ${title}`,
          queueKind: "render",
          studioId: def.studioId,
          universalPipelineId: def.id,
          pipelineId: opts?.pipelineRefId,
          agents: agents.slice(-1),
          etaSec: 240,
        }),
      );
    }

    if (def.stages.includes("publish")) {
      jobIds.push(
        this.enqueue({
          title: `Publish · ${title}`,
          queueKind: "publishing",
          studioId: def.studioId,
          universalPipelineId: def.id,
          pipelineId: opts?.pipelineRefId,
          agents: def.id === "publishing" ? agents : ["Publisher"],
          etaSec: 120,
        }),
      );
    }

    enterpriseEventBus.publish({
      type: "ai_request",
      source: "production",
      payload: {
        stream: "ai",
        universalPipelineId: def.id,
        collaboration: def.collaboration,
        agents,
        jobIds,
      },
    });

    try {
      useNotificationStore.getState().push({
        title: "Pipeline queued",
        body: `${def.label} · ${jobIds.length} jobs`,
        kind: "info",
      });
    } catch {
      /* ignore */
    }

    emitLocal();
    return { jobIds, pipeline: def };
  },

  /** Retry Manager — uses Job Manager.retry. */
  retryFailed(limit = 5): string[] {
    const failed = jobManager.list().filter((j) => j.status === "failed" && j.queueKind).slice(0, limit);
    const ids: string[] = [];
    for (const j of failed) {
      jobManager.retry(j.id);
      ids.push(j.id);
    }
    emitLocal();
    return ids;
  },

  cancel(jobId: string) {
    jobManager.cancel(jobId);
    workers = workers.map((w) =>
      w.jobId === jobId
        ? { ...w, status: "idle" as const, jobId: null, load: Math.max(0, w.load - 1), updatedAt: now() }
        : w,
    );
    emitLocal();
  },

  pause(jobId: string) {
    jobManager.pause(jobId);
    emitLocal();
  },

  resume(jobId: string) {
    jobManager.resume(jobId);
    emitLocal();
  },

  setPriority(jobId: string, priority: import("./types").JobPriority) {
    jobManager.setPriority(jobId, priority);
    emitLocal();
  },

  /** Enrich automation sync with queue kinds (called from jobManager path). */
  annotateAutomation(job: RuntimeJobRecord & { kind?: string }): Partial<RuntimeJobRecord> {
    return {
      queueKind: job.queueKind || inferQueueFromAutomation(job.kind || "queue", job.title),
      source: "production",
    };
  },

  /** Background processing tick — called from Runtime Engine. */
  tick() {
    scheduleWaiting();
    advanceRunning();
    computeAnalytics();
    // Soft health signal for queue pressure
    const pressure = QUEUE_KINDS.reduce((n, q) => n + this.queueLength(q), 0);
    if (pressure > 12) {
      enterpriseEventBus.publish({
        type: "runtime_update",
        source: "system",
        payload: { stream: "queue", pressure, analytics: lastAnalytics },
      });
    }
    emitLocal();
  },

  /** Monitoring snapshot for UI / City. */
  monitor() {
    const analytics = lastAnalytics.updatedAt ? lastAnalytics : computeAnalytics();
    const health = healthService.getLevel();
    return {
      health,
      queues: Object.fromEntries(
        QUEUE_KINDS.map((q) => [
          q,
          {
            length: analytics.byQueue[q].length,
            running: analytics.byQueue[q].running,
            failed: analytics.byQueue[q].failed,
            etaSec: analytics.byQueue[q].avgEtaSec,
          },
        ]),
      ) as Record<ProductionQueueKind, { length: number; running: number; failed: number; etaSec: number }>,
      workers: workers.slice(),
      jobs: jobManager.list().filter((j) => j.queueKind || j.source === "production"),
      analytics,
      agentsActive: aiAgentRuntime.activeCount(),
    };
  },

  depths(): Record<ProductionQueueKind, number> {
    const out = {} as Record<ProductionQueueKind, number>;
    for (const q of QUEUE_KINDS) out[q] = this.queueLength(q);
    return out;
  },
};
