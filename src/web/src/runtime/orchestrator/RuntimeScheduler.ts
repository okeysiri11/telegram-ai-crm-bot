/**
 * Runtime scheduler — Sprint 29.8.
 * Orchestration operations only — no business logic.
 */

import type { RuntimeId, ScheduleJob, SchedulerOperation } from "./orchestratorTypes";
import { runtimeRegistry } from "./RuntimeRegistry";
import { runtimeDependencyGraph } from "./RuntimeDependencyGraph";
import { publishOrchestratorEvent } from "./orchestratorEvents";

function uid() {
  return `job_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

const queue: ScheduleJob[] = [];

function runOp(runtimeId: RuntimeId, operation: SchedulerOperation): { ok: boolean; message?: string; error?: string } {
  const adapter = runtimeRegistry.get(runtimeId);
  if (!adapter) return { ok: false, error: "runtime_not_registered" };
  try {
    switch (operation) {
      case "startup":
        adapter.startup();
        return { ok: true, message: "started" };
      case "shutdown":
        adapter.shutdown?.();
        return { ok: true, message: "stopped" };
      case "reload":
        (adapter.reload || adapter.startup)();
        return { ok: true, message: "reloaded" };
      case "rebuild":
        (adapter.rebuild || adapter.reload || adapter.startup)();
        return { ok: true, message: "rebuilt" };
      case "warm_cache":
        (adapter.warmCache || adapter.refresh || adapter.startup)();
        return { ok: true, message: "cache_warmed" };
      case "refresh":
        (adapter.refresh || adapter.sync || adapter.startup)();
        return { ok: true, message: "refreshed" };
      case "sync":
        (adapter.sync || adapter.refresh || adapter.startup)();
        return { ok: true, message: "synced" };
      default:
        return { ok: false, error: "unknown_operation" };
    }
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "schedule_failed" };
  }
}

export const runtimeScheduler = {
  clear() {
    queue.length = 0;
  },

  list(limit = 40) {
    return queue.slice(0, limit);
  },

  pending() {
    return queue.filter((j) => j.status === "pending" || j.status === "running");
  },

  enqueue(operation: SchedulerOperation, runtimeId?: RuntimeId): ScheduleJob {
    const job: ScheduleJob = {
      id: uid(),
      operation,
      runtimeId,
      status: "pending",
      enqueuedAt: now(),
    };
    queue.unshift(job);
    if (queue.length > 200) queue.length = 200;
    publishOrchestratorEvent("ScheduleEnqueued", {
      jobId: job.id,
      operation,
      runtimeId,
    });
    return job;
  },

  /** Execute one job immediately (orchestration). */
  run(jobId: string): ScheduleJob | null {
    const job = queue.find((j) => j.id === jobId);
    if (!job) return null;
    job.status = "running";
    job.startedAt = now();

    if (!job.runtimeId) {
      // Platform-wide: apply to all in dependency order
      const order =
        job.operation === "shutdown"
          ? [...runtimeDependencyGraph.order()].reverse()
          : runtimeDependencyGraph.order();
      const errors: string[] = [];
      for (const id of order) {
        const res = runOp(id, job.operation);
        if (!res.ok) errors.push(`${id}:${res.error}`);
      }
      job.status = errors.length ? "failed" : "completed";
      job.error = errors.length ? errors.join("; ") : undefined;
      job.message = errors.length ? undefined : `platform_${job.operation}`;
      job.finishedAt = now();
      publishOrchestratorEvent("ScheduleCompleted", {
        jobId: job.id,
        operation: job.operation,
        ok: job.status === "completed",
      });
      return job;
    }

    const res = runOp(job.runtimeId, job.operation);
    job.status = res.ok ? "completed" : "failed";
    job.message = res.message;
    job.error = res.error;
    job.finishedAt = now();
    publishOrchestratorEvent("ScheduleCompleted", {
      jobId: job.id,
      operation: job.operation,
      runtimeId: job.runtimeId,
      ok: res.ok,
    });
    return job;
  },

  /** Enqueue + run */
  execute(operation: SchedulerOperation, runtimeId?: RuntimeId): ScheduleJob {
    const job = this.enqueue(operation, runtimeId);
    return this.run(job.id)!;
  },

  startupAll() {
    return this.execute("startup");
  },

  shutdownAll() {
    return this.execute("shutdown");
  },
};
