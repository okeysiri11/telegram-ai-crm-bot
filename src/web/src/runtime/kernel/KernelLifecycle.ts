/**
 * Kernel lifecycle phase machine — Sprint 29.9.
 */

import type { BootStep, BootStepId, KernelPhase } from "./kernelTypes";
import { publishKernelEvent } from "./kernelEvents";

const BOOT_STEPS: { id: BootStepId; label: string }[] = [
  { id: "boot", label: "Boot" },
  { id: "configuration", label: "Configuration" },
  { id: "runtime_registry", label: "Runtime Registry" },
  { id: "dependency_validation", label: "Dependency Validation" },
  { id: "orchestrator_startup", label: "Orchestrator Startup" },
  { id: "all_runtime_startup", label: "All Runtime Startup" },
  { id: "health_validation", label: "Health Validation" },
  { id: "platform_ready", label: "Platform Ready" },
];

let phase: KernelPhase = "uninitialized";
let steps: BootStep[] = BOOT_STEPS.map((s) => ({ ...s, status: "pending" }));
let bootStartedAt: number | null = null;
let bootFinishedAt: number | null = null;
let lastError: string | null = null;

function now() {
  return new Date().toISOString();
}

export const kernelLifecycle = {
  clear() {
    phase = "uninitialized";
    steps = BOOT_STEPS.map((s) => ({ ...s, status: "pending" }));
    bootStartedAt = null;
    bootFinishedAt = null;
    lastError = null;
  },

  phase() {
    return phase;
  },

  setPhase(next: KernelPhase, message?: string) {
    const prev = phase;
    phase = next;
    publishKernelEvent("PhaseChanged", { from: prev, to: next, message });
    return phase;
  },

  steps() {
    return steps.map((s) => ({ ...s }));
  },

  beginBoot() {
    bootStartedAt = performance.now();
    bootFinishedAt = null;
    lastError = null;
    steps = BOOT_STEPS.map((s) => ({ ...s, status: "pending" }));
    this.setPhase("booting");
    publishKernelEvent("BootStarted", {});
    this.markStep("boot", "running");
  },

  markStep(
    id: BootStepId,
    status: BootStep["status"],
    opts?: { message?: string; error?: string },
  ) {
    const step = steps.find((s) => s.id === id);
    if (!step) return;
    if (status === "running") {
      step.startedAt = now();
      step.status = "running";
    } else if (status === "ok" || status === "failed" || status === "skipped") {
      step.finishedAt = now();
      step.status = status;
      if (step.startedAt) {
        step.durationMs = Math.max(
          0,
          Date.parse(step.finishedAt) - Date.parse(step.startedAt),
        );
      } else if (bootStartedAt != null) {
        step.durationMs = Math.round(performance.now() - bootStartedAt);
      }
      step.message = opts?.message;
      step.error = opts?.error;
    } else {
      step.status = status;
    }
  },

  completeBoot(ok: boolean, error?: string) {
    bootFinishedAt = performance.now();
    this.markStep("boot", ok ? "ok" : "failed", {
      message: ok ? "kernel_boot_complete" : undefined,
      error,
    });
    this.markStep("platform_ready", ok ? "ok" : "failed", {
      message: ok ? "platform_ready" : error,
      error,
    });
    if (ok) {
      this.setPhase("ready");
      lastError = null;
      publishKernelEvent("BootCompleted", {
        durationMs: this.startupTimeMs(),
        ready: true,
      });
    } else {
      this.setPhase("error");
      lastError = error || "boot_failed";
      publishKernelEvent("BootCompleted", {
        durationMs: this.startupTimeMs(),
        ready: false,
        error: lastError,
      });
    }
  },

  markDegraded(message: string) {
    if (bootStartedAt != null && bootFinishedAt == null) {
      bootFinishedAt = performance.now();
    }
    this.setPhase("degraded", message);
    lastError = message;
  },

  beginShutdown() {
    this.setPhase("shutting_down");
    publishKernelEvent("ShutdownStarted", {});
  },

  completeShutdown() {
    this.setPhase("stopped");
    publishKernelEvent("ShutdownCompleted", {});
  },

  beginRestart() {
    this.setPhase("restarting");
    publishKernelEvent("RestartRequested", {});
  },

  beginRecovery() {
    this.setPhase("recovering");
  },

  startupTimeMs() {
    if (bootStartedAt == null) return null;
    const end = bootFinishedAt ?? performance.now();
    return Math.round(end - bootStartedAt);
  },

  lastError() {
    return lastError;
  },

  isReady() {
    return phase === "ready" || phase === "degraded";
  },
};
