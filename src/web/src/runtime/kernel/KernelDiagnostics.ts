/**
 * Kernel diagnostics — Sprint 29.9.
 */

import { enterpriseOrchestrator, ORCHESTRATOR_RUNTIME_VERSION } from "@/runtime/orchestrator";
import { KERNEL_RUNTIME_VERSION, PLATFORM_IDENTITY } from "./KernelVersion";
import { kernelConfiguration } from "./KernelConfiguration";
import { kernelLifecycle } from "./KernelLifecycle";
import { kernelHealth } from "./KernelHealth";
import type { DiagnosticReport } from "./kernelTypes";
import { publishKernelEvent } from "./kernelEvents";

function uid() {
  return `diag_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

function readMemory() {
  const perf = performance as Performance & {
    memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number };
  };
  if (!perf.memory) {
    return { available: false as const };
  }
  const m = perf.memory;
  return {
    available: true as const,
    usedJsHeapMb: Math.round((m.usedJSHeapSize / (1024 * 1024)) * 10) / 10,
    totalJsHeapMb: Math.round((m.totalJSHeapSize / (1024 * 1024)) * 10) / 10,
    limitJsHeapMb: Math.round((m.jsHeapSizeLimit / (1024 * 1024)) * 10) / 10,
  };
}

export const kernelDiagnostics = {
  collect(): DiagnosticReport {
    const config = kernelConfiguration.get();
    const health = kernelHealth.snapshot();
    const failedModules: string[] = [];
    const dependencyErrors: string[] = [];
    const versionMismatches: string[] = [];
    const configurationProblems = kernelConfiguration.problems();
    const notes: string[] = [];

    const runtimes: DiagnosticReport["runtimes"] = [];
    if (enterpriseOrchestrator.isReady()) {
      try {
        enterpriseOrchestrator.graph.assertAcyclic();
      } catch (e) {
        dependencyErrors.push(e instanceof Error ? e.message : "dependency_error");
      }
      for (const r of enterpriseOrchestrator.runtimes()) {
        runtimes.push({ id: r.id, status: r.status, version: String(r.version) });
        if (r.status === "error" || r.status === "stopped") failedModules.push(r.id);
      }
      if (enterpriseOrchestrator.version !== ORCHESTRATOR_RUNTIME_VERSION) {
        versionMismatches.push(
          `orchestrator expected ${ORCHESTRATOR_RUNTIME_VERSION} got ${enterpriseOrchestrator.version}`,
        );
      }
    } else {
      failedModules.push("orchestrator");
      notes.push("orchestrator_not_ready");
    }

    if (KERNEL_RUNTIME_VERSION !== PLATFORM_IDENTITY.kernelVersion) {
      versionMismatches.push("kernel_identity_mismatch");
    }

    const report: DiagnosticReport = {
      id: uid(),
      at: now(),
      phase: kernelLifecycle.phase(),
      startupTimeMs: kernelLifecycle.startupTimeMs(),
      memory: readMemory(),
      runtimes,
      failedModules,
      dependencyErrors,
      versionMismatches,
      configurationProblems,
      eventBus: {
        ok: health.eventBusOk,
        recentErrors: 0,
      },
      notes,
    };

    publishKernelEvent("DiagnosticsCollected", {
      diagnosticId: report.id,
      failed: failedModules.length,
      startupTimeMs: report.startupTimeMs,
    });
    return report;
  },
};
