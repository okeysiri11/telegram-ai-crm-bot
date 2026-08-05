/**
 * Kernel recovery — Sprint 29.9.
 * Isolate runtime failures; never take down the whole platform.
 */

import { enterpriseOrchestrator, type RuntimeId } from "@/runtime/orchestrator";
import { kernelConfiguration } from "./KernelConfiguration";
import { kernelLifecycle } from "./KernelLifecycle";
import type { RecoveryRecord } from "./kernelTypes";
import { publishKernelEvent } from "./kernelEvents";

function uid() {
  return `recov_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

const history: RecoveryRecord[] = [];
const attempts = new Map<string, number>();

export const kernelRecovery = {
  clear() {
    history.length = 0;
    attempts.clear();
  },

  history(limit = 40) {
    return history.slice(0, limit);
  },

  record(entry: Omit<RecoveryRecord, "id" | "at"> & { at?: string }) {
    const full: RecoveryRecord = {
      id: uid(),
      at: entry.at || now(),
      ...entry,
    };
    history.unshift(full);
    if (history.length > 200) history.length = 200;
    return full;
  },

  /**
   * Attempt graceful restart of a single runtime.
   * On failure: mark unhealthy, notify orchestrator, continue platform.
   */
  recoverRuntime(runtimeId: RuntimeId): RecoveryRecord {
    const cfg = kernelConfiguration.get();
    if (!cfg.featureFlags.recoveryEnabled) {
      return this.record({
        runtimeId,
        action: "platform_continue",
        ok: true,
        attempt: 0,
        message: "recovery_disabled",
      });
    }

    kernelLifecycle.beginRecovery();
    const attempt = (attempts.get(runtimeId) || 0) + 1;
    attempts.set(runtimeId, attempt);
    publishKernelEvent("RecoveryAttempted", { runtimeId, attempt });

    if (attempt > cfg.recoveryMaxAttempts) {
      const rec = this.record({
        runtimeId,
        action: "mark_unhealthy",
        ok: false,
        attempt,
        message: "max_attempts_exceeded",
      });
      this.notifyOrchestrator(runtimeId, "unhealthy");
      this.record({
        runtimeId,
        action: "platform_continue",
        ok: true,
        attempt,
        message: "platform_continues_degraded",
      });
      kernelLifecycle.markDegraded(`runtime_${runtimeId}_unhealthy`);
      publishKernelEvent("RecoveryFailed", { runtimeId, attempt });
      return rec;
    }

    try {
      const result = enterpriseOrchestrator.schedule("reload", runtimeId);
      if (result.ok) {
        attempts.set(runtimeId, 0);
        const rec = this.record({
          runtimeId,
          action: "restart",
          ok: true,
          attempt,
          message: "runtime_reloaded",
        });
        publishKernelEvent("RecoverySucceeded", { runtimeId, attempt });
        if (kernelLifecycle.phase() === "recovering") {
          kernelLifecycle.setPhase("degraded", "recovered_partial");
        }
        return rec;
      }
      throw new Error(result.error || "reload_failed");
    } catch (e) {
      const message = e instanceof Error ? e.message : "recovery_failed";
      this.record({
        runtimeId,
        action: "mark_unhealthy",
        ok: false,
        attempt,
        message,
      });
      this.notifyOrchestrator(runtimeId, "unhealthy");
      const cont = this.record({
        runtimeId,
        action: "platform_continue",
        ok: true,
        attempt,
        message: "platform_continues_after_failure",
      });
      kernelLifecycle.markDegraded(`runtime_${runtimeId}_recovery_failed`);
      publishKernelEvent("RecoveryFailed", { runtimeId, attempt, message });
      return cont;
    }
  },

  notifyOrchestrator(runtimeId: RuntimeId | string, status: string) {
    this.record({
      runtimeId,
      action: "notify_orchestrator",
      ok: true,
      attempt: attempts.get(String(runtimeId)) || 0,
      message: status,
    });
    // Soft notify via refresh of orchestrator health view
    try {
      if (enterpriseOrchestrator.isReady()) {
        enterpriseOrchestrator.platformHealth();
      }
    } catch {
      /* never crash platform */
    }
  },
};
