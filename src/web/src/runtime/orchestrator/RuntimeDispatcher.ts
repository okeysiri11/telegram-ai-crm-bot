/**
 * Runtime dispatcher — Sprint 29.8.
 * Dispatches orchestration intents to registered adapters (no business logic).
 */

import type { RuntimeId, SchedulerOperation } from "./orchestratorTypes";
import { runtimeScheduler } from "./RuntimeScheduler";
import { runtimeRegistry } from "./RuntimeRegistry";

export type DispatchResult = {
  ok: boolean;
  runtimeId?: RuntimeId;
  operation: SchedulerOperation;
  jobId?: string;
  error?: string;
  message?: string;
};

export const runtimeDispatcher = {
  dispatch(operation: SchedulerOperation, runtimeId?: RuntimeId): DispatchResult {
    if (runtimeId && !runtimeRegistry.get(runtimeId)) {
      return { ok: false, runtimeId, operation, error: "runtime_not_registered" };
    }
    const job = runtimeScheduler.execute(operation, runtimeId);
    return {
      ok: job.status === "completed",
      runtimeId,
      operation,
      jobId: job.id,
      error: job.error,
      message: job.message,
    };
  },

  startup(runtimeId?: RuntimeId) {
    return this.dispatch("startup", runtimeId);
  },

  shutdown(runtimeId?: RuntimeId) {
    return this.dispatch("shutdown", runtimeId);
  },

  reload(runtimeId?: RuntimeId) {
    return this.dispatch("reload", runtimeId);
  },

  rebuild(runtimeId?: RuntimeId) {
    return this.dispatch("rebuild", runtimeId);
  },

  warmCache(runtimeId?: RuntimeId) {
    return this.dispatch("warm_cache", runtimeId);
  },

  refresh(runtimeId?: RuntimeId) {
    return this.dispatch("refresh", runtimeId);
  },

  sync(runtimeId?: RuntimeId) {
    return this.dispatch("sync", runtimeId);
  },
};
