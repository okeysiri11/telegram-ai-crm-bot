/**
 * Enterprise Kernel — Sprint 29.9.
 * Platform bootstrap & lifecycle manager (no business logic).
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { enterpriseOrchestrator, type RuntimeId } from "@/runtime/orchestrator";
import { KERNEL_RUNTIME_VERSION, kernelVersion, PLATFORM_IDENTITY } from "./KernelVersion";
import { kernelConfiguration } from "./KernelConfiguration";
import { kernelLifecycle } from "./KernelLifecycle";
import { kernelRegistry } from "./KernelRegistry";
import { kernelHealth } from "./KernelHealth";
import { kernelDiagnostics } from "./KernelDiagnostics";
import { kernelRecovery } from "./KernelRecovery";
import { kernelBootstrap } from "./KernelBootstrap";
import { kernelEvents } from "./kernelEvents";

let booted = false;
let healthTimer: ReturnType<typeof setInterval> | null = null;

function stopHealthProbe() {
  if (healthTimer) {
    clearInterval(healthTimer);
    healthTimer = null;
  }
}

function startHealthProbe() {
  stopHealthProbe();
  const cfg = kernelConfiguration.get();
  if (!cfg.featureFlags.backgroundHealthProbe) return;
  healthTimer = setInterval(() => {
    try {
      kernelHealth.snapshot();
    } catch {
      kernelHealth.noteEventBusError();
    }
  }, cfg.healthProbeIntervalMs);
}

function registerCommands() {
  commandRuntime.register({
    id: "kernel_open",
    action: "open_kernel_runtime",
    label: "Open Enterprise Kernel",
    kind: "navigate",
    keywords: ["kernel", "boot", "platform", "diagnostics", "lifecycle"],
    route: "/kernel",
    permission: "*",
  });
  commandRuntime.register({
    id: "kernel_diagnostics",
    action: "collect_kernel_diagnostics",
    label: "Collect Kernel Diagnostics",
    kind: "system",
    keywords: ["diagnostics", "kernel", "health"],
    permission: "*",
    handler: async () => {
      const d = enterpriseKernel.diagnostics();
      return {
        ok: true,
        message: `phase ${d.phase} · failed ${d.failedModules.length} · ${d.startupTimeMs ?? "?"}ms`,
      };
    },
  });
}

export const enterpriseKernel = {
  version: KERNEL_RUNTIME_VERSION,
  identity: PLATFORM_IDENTITY,

  /**
   * Platform boot — full lifecycle sequence.
   * Idempotent when already ready/degraded.
   */
  boot() {
    if (booted && kernelLifecycle.isReady()) {
      return this.status();
    }
    commandRuntime.startup();
    const result = kernelBootstrap.run();
    registerCommands();
    booted = result.ok || result.degraded || kernelLifecycle.isReady();
    if (booted) startHealthProbe();

    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: {
        stream: "kernel_runtime",
        ready: booted,
        version: KERNEL_RUNTIME_VERSION,
        phase: kernelLifecycle.phase(),
        degraded: result.degraded,
      },
    });
    return this.status();
  },

  /** Alias used by Shell */
  startup() {
    return this.boot();
  },

  isReady() {
    return booted && kernelLifecycle.isReady();
  },

  shutdown() {
    kernelLifecycle.beginShutdown();
    stopHealthProbe();
    try {
      if (enterpriseOrchestrator.isReady()) {
        enterpriseOrchestrator.shutdown();
      }
    } catch {
      /* isolate */
    }
    booted = false;
    kernelLifecycle.completeShutdown();
    return this.status();
  },

  /** Safe restart — never throws to caller */
  restart() {
    if (!kernelConfiguration.get().featureFlags.safeRestart) {
      return { ok: false, error: "safe_restart_disabled" as const };
    }
    kernelLifecycle.beginRestart();
    try {
      this.shutdown();
      kernelLifecycle.clear();
      kernelConfiguration.clear();
      kernelRegistry.clear();
      kernelHealth.clear();
      kernelRecovery.clear();
      kernelEvents.clear();
      // Orchestrator.shutdown() already ran; next boot() re-enters orchestrator.startup()
      const status = this.boot();
      return { ok: status.ready || status.degraded, status };
    } catch (e) {
      kernelLifecycle.markDegraded(e instanceof Error ? e.message : "restart_failed");
      return { ok: false, error: "restart_failed" as const };
    }
  },

  recover(runtimeId: RuntimeId) {
    return kernelRecovery.recoverRuntime(runtimeId);
  },

  configuration: kernelConfiguration,
  lifecycle: kernelLifecycle,
  registry: kernelRegistry,
  health: kernelHealth,
  diagnosticsEngine: kernelDiagnostics,
  recovery: kernelRecovery,
  versionApi: kernelVersion,
  events: kernelEvents,
  bootstrap: kernelBootstrap,

  config() {
    return kernelConfiguration.get();
  },

  healthSnapshot() {
    return kernelHealth.snapshot();
  },

  diagnostics() {
    return kernelDiagnostics.collect();
  },

  bootSequence() {
    return kernelLifecycle.steps();
  },

  recoveryHistory(limit?: number) {
    return kernelRecovery.history(limit);
  },

  modules() {
    return kernelRegistry.list();
  },

  status() {
    const health = kernelHealth.snapshot();
    return {
      version: KERNEL_RUNTIME_VERSION,
      phase: kernelLifecycle.phase(),
      ready: health.ready,
      degraded: health.degraded,
      startupTimeMs: kernelLifecycle.startupTimeMs(),
      health,
      identity: kernelVersion.descriptor(),
      config: kernelConfiguration.get(),
      lastError: kernelLifecycle.lastError(),
    };
  },

  stats() {
    const s = this.status();
    return {
      version: s.version,
      phase: s.phase,
      ready: s.ready,
      degraded: s.degraded,
      startupTimeMs: s.startupTimeMs,
      modules: kernelRegistry.list().length,
      recoveryRecords: kernelRecovery.history(200).length,
      events: kernelEvents.list(200).length,
      health: s.health,
    };
  },

  inspectorSnapshot() {
    return {
      version: KERNEL_RUNTIME_VERSION,
      status: this.status(),
      bootSequence: this.bootSequence(),
      modules: this.modules(),
      diagnostics: this.diagnostics(),
      recoveryHistory: this.recoveryHistory(20),
      events: kernelEvents.list(30),
      stats: this.stats(),
    };
  },

  __resetForTests() {
    stopHealthProbe();
    booted = false;
    kernelLifecycle.clear();
    kernelConfiguration.clear();
    kernelRegistry.clear();
    kernelHealth.clear();
    kernelRecovery.clear();
    kernelEvents.clear();
  },
};
