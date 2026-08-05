/**
 * Central Job Manager — Sprint 28.1.
 * Tracks lifecycle, progress, ETA. Syncs production automation jobs + synthetic queue.
 */

import type { AutomationJob } from "@/ai-production-studio/productionCatalog";
import type { JobLifecycle, ProductionQueueKind, RuntimeJobRecord } from "./types";

type Listener = (jobs: RuntimeJobRecord[]) => void;

const listeners = new Set<Listener>();
let jobs: RuntimeJobRecord[] = seedJobs();

function now() {
  return new Date().toISOString();
}

function mapAutomationStatus(s: AutomationJob["status"], retries: number): JobLifecycle {
  if (s === "running") return "running";
  if (s === "queued") return retries > 0 ? "retrying" : "waiting";
  if (s === "done") return "completed";
  if (s === "failed") return retries > 0 ? "retrying" : "failed";
  return "waiting";
}

function seedJobs(): RuntimeJobRecord[] {
  const t = now();
  return [
    {
      id: "rj_sys_heartbeat",
      title: "Runtime heartbeat",
      status: "running",
      progress: 100,
      etaSec: null,
      source: "system",
      startedAt: t,
      updatedAt: t,
      retries: 0,
    },
    {
      id: "rj_queue_render",
      title: "Render queue · night pack",
      status: "waiting",
      progress: 12,
      etaSec: 420,
      source: "queue",
      startedAt: t,
      updatedAt: t,
      retries: 0,
      queueKind: "render",
    },
    {
      id: "rj_queue_gen",
      title: "Generation · creative batch",
      status: "waiting",
      progress: 8,
      etaSec: 240,
      source: "production",
      startedAt: t,
      updatedAt: t,
      retries: 0,
      queueKind: "generation",
      studioId: "image",
    },
    {
      id: "rj_queue_pub",
      title: "Publishing · approval window",
      status: "waiting",
      progress: 5,
      etaSec: 180,
      source: "production",
      startedAt: t,
      updatedAt: t,
      retries: 0,
      queueKind: "publishing",
      studioId: "publishing",
    },
    {
      id: "rj_wf_approve",
      title: "Workflow · approval gate",
      status: "waiting",
      progress: 40,
      etaSec: 90,
      source: "workflow",
      startedAt: t,
      updatedAt: t,
      retries: 0,
      queueKind: "task",
    },
  ];
}

function emit() {
  listeners.forEach((l) => l(jobs.slice()));
}

function upsert(record: RuntimeJobRecord) {
  const idx = jobs.findIndex((j) => j.id === record.id);
  if (idx >= 0) jobs[idx] = record;
  else jobs = [record, ...jobs].slice(0, 80);
  emit();
}

export const jobManager = {
  subscribe(listener: Listener) {
    listeners.add(listener);
    listener(jobs.slice());
    return () => {
      listeners.delete(listener);
    };
  },

  list() {
    return jobs.slice();
  },

  counts() {
    const base: Record<JobLifecycle, number> = {
      running: 0,
      waiting: 0,
      completed: 0,
      failed: 0,
      cancelled: 0,
      retrying: 0,
      paused: 0,
    };
    for (const j of jobs) base[j.status] += 1;
    return base;
  },

  upsert(partial: Omit<RuntimeJobRecord, "updatedAt"> & { updatedAt?: string }) {
    upsert({ ...partial, updatedAt: partial.updatedAt || now() });
  },

  setStatus(id: string, status: JobLifecycle, progress?: number) {
    const cur = jobs.find((j) => j.id === id);
    if (!cur) return;
    upsert({
      ...cur,
      status,
      progress: progress ?? cur.progress,
      updatedAt: now(),
      retries: status === "retrying" ? cur.retries + 1 : cur.retries,
      etaSec:
        status === "completed" || status === "failed" || status === "cancelled"
          ? 0
          : cur.etaSec,
    });
  },

  create(partial: Omit<RuntimeJobRecord, "updatedAt" | "startedAt" | "retries" | "progress" | "status"> & {
    status?: JobLifecycle;
    progress?: number;
    retries?: number;
  }) {
    const t = now();
    const record: RuntimeJobRecord = {
      progress: 0,
      retries: 0,
      status: "waiting",
      ...partial,
      startedAt: t,
      updatedAt: t,
    };
    upsert(record);
    return record;
  },

  start(id: string) {
    this.setStatus(id, "running", 5);
  },

  pause(id: string) {
    this.setStatus(id, "paused");
  },

  resume(id: string) {
    this.setStatus(id, "running");
  },

  setPriority(id: string, priority: import("./types").JobPriority) {
    const cur = jobs.find((j) => j.id === id);
    if (!cur) return;
    upsert({ ...cur, priority, updatedAt: now() });
  },

  appendLog(id: string, message: string, level: "info" | "warn" | "error" = "info") {
    const cur = jobs.find((j) => j.id === id);
    if (!cur) return;
    const entry = { at: now(), message, level };
    upsert({
      ...cur,
      logs: [...(cur.logs || []), entry].slice(-40),
      history: [...(cur.history || []), entry].slice(-80),
      updatedAt: now(),
    });
  },

  /** Sync from Production automation jobs (existing store). */
  syncProductionJobs(automation: AutomationJob[]) {
    for (const a of automation) {
      const title = a.title.toLowerCase();
      const queueKind =
        title.includes("render")
          ? ("render" as const)
          : title.includes("publish") || a.kind === "schedule"
            ? ("publishing" as const)
            : title.includes("generat") || title.includes("image") || title.includes("video")
              ? ("generation" as const)
              : a.kind === "batch"
                ? ("task" as const)
                : ("production" as const);
      upsert({
        id: `prod_${a.id}`,
        title: a.title,
        status: mapAutomationStatus(a.status, a.retries),
        progress:
          a.status === "done" ? 100 : a.status === "running" ? 55 + (a.retries % 3) * 10 : 15,
        etaSec: a.status === "done" || a.status === "failed" ? 0 : 60 + a.retries * 30,
        source: "production",
        startedAt: a.updatedAt,
        updatedAt: now(),
        retries: a.retries,
        queueKind,
        pipelineId: a.pipelineId,
      });
    }
    emit();
  },

  listByQueue(kind: ProductionQueueKind) {
    return jobs.filter((j) => j.queueKind === kind);
  },

  /** Tick waiting jobs forward slightly (live feel without fake completion storms). */
  tick() {
    jobs = jobs.map((j) => {
      if (j.status !== "running" && j.status !== "waiting" && j.status !== "retrying") return j;
      const progress = Math.min(99, j.progress + (j.status === "running" ? 3 : 1));
      const etaSec = j.etaSec == null ? null : Math.max(0, j.etaSec - 12);
      return { ...j, progress, etaSec, updatedAt: now() };
    });
    emit();
  },

  cancel(id: string) {
    this.setStatus(id, "cancelled", 100);
  },

  retry(id: string) {
    const cur = jobs.find((j) => j.id === id);
    if (!cur) return;
    upsert({
      ...cur,
      status: "retrying",
      progress: Math.max(5, cur.progress - 10),
      retries: cur.retries + 1,
      etaSec: 120,
      updatedAt: now(),
    });
  },
};
