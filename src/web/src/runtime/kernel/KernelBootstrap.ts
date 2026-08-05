/**
 * Kernel bootstrap sequence — Sprint 29.9.
 * Boot → Config → Registry → Deps → Orchestrator → Runtimes → Health → Ready
 */

import { enterpriseOrchestrator } from "@/runtime/orchestrator";
import { kernelConfiguration } from "./KernelConfiguration";
import { kernelLifecycle } from "./KernelLifecycle";
import { kernelRegistry } from "./KernelRegistry";
import { kernelHealth } from "./KernelHealth";
import { kernelDiagnostics } from "./KernelDiagnostics";
import type { BootStep } from "./kernelTypes";

export type BootstrapResult = {
  ok: boolean;
  degraded: boolean;
  phase: string;
  steps: BootStep[];
  startupTimeMs: number | null;
  error?: string;
  diagnosticsId?: string;
};

export const kernelBootstrap = {
  /**
   * Run full platform boot sequence.
   * Isolates failures — platform can become ready/degraded without hard crash.
   */
  run(): BootstrapResult {
    kernelLifecycle.beginBoot();
    let degraded = false;
    let fatal: string | undefined;

    try {
      // 1. Configuration
      kernelLifecycle.setPhase("configuration");
      kernelLifecycle.markStep("configuration", "running");
      try {
        kernelConfiguration.load();
        const problems = kernelConfiguration.problems();
        kernelLifecycle.markStep("configuration", problems.length ? "ok" : "ok", {
          message: problems.length ? `warnings:${problems.join(",")}` : "config_loaded",
        });
      } catch (e) {
        const msg = e instanceof Error ? e.message : "config_failed";
        kernelLifecycle.markStep("configuration", "failed", { error: msg });
        fatal = msg;
      }

      if (fatal) {
        kernelLifecycle.completeBoot(false, fatal);
        return {
          ok: false,
          degraded: false,
          phase: kernelLifecycle.phase(),
          steps: kernelLifecycle.steps(),
          startupTimeMs: kernelLifecycle.startupTimeMs(),
          error: fatal,
        };
      }

      if (!kernelConfiguration.get().featureFlags.orchestratorEnabled) {
        kernelLifecycle.markStep("orchestrator_startup", "skipped", {
          message: "orchestrator_disabled",
        });
        kernelLifecycle.completeBoot(false, "orchestrator_disabled");
        return {
          ok: false,
          degraded: false,
          phase: kernelLifecycle.phase(),
          steps: kernelLifecycle.steps(),
          startupTimeMs: kernelLifecycle.startupTimeMs(),
          error: "orchestrator_disabled",
        };
      }

      // 2. Runtime registry (kernel view + prepare orchestrator adapters via startup)
      kernelLifecycle.setPhase("registry");
      kernelLifecycle.markStep("runtime_registry", "running");
      try {
        kernelRegistry.register({
          id: "kernel",
          kind: "kernel",
          label: "Enterprise Kernel",
          version: "29.9",
          loaded: true,
          status: "healthy",
        });
        kernelLifecycle.markStep("runtime_registry", "ok", {
          message: `modules:${kernelRegistry.list().length}`,
        });
      } catch (e) {
        kernelLifecycle.markStep("runtime_registry", "failed", {
          error: e instanceof Error ? e.message : "registry_failed",
        });
        degraded = true;
      }

      // 3. Dependency validation + 4/5. Orchestrator & runtime startup
      kernelLifecycle.setPhase("dependency_validation");
      kernelLifecycle.markStep("dependency_validation", "running");
      kernelLifecycle.setPhase("orchestrator_startup");
      kernelLifecycle.markStep("orchestrator_startup", "running");
      kernelLifecycle.setPhase("runtime_startup");
      kernelLifecycle.markStep("all_runtime_startup", "running");

      try {
        // Orchestrator registers adapters, validates graph, starts all runtimes
        enterpriseOrchestrator.startup();
        try {
          enterpriseOrchestrator.graph.assertAcyclic();
          kernelLifecycle.markStep("dependency_validation", "ok", {
            message: `order:${enterpriseOrchestrator.dependencyOrder().length}`,
          });
        } catch (e) {
          kernelLifecycle.markStep("dependency_validation", "failed", {
            error: e instanceof Error ? e.message : "cycle",
          });
          degraded = true;
        }
        kernelLifecycle.markStep("orchestrator_startup", "ok", {
          message: `version:${enterpriseOrchestrator.version}`,
        });
        kernelLifecycle.markStep("all_runtime_startup", "ok", {
          message: `runtimes:${enterpriseOrchestrator.runtimes().length}`,
        });
      } catch (e) {
        const msg = e instanceof Error ? e.message : "orchestrator_startup_failed";
        kernelLifecycle.markStep("orchestrator_startup", "failed", { error: msg });
        kernelLifecycle.markStep("all_runtime_startup", "failed", { error: msg });
        kernelLifecycle.markStep("dependency_validation", "failed", { error: msg });
        // Do not kill platform — mark degraded and continue to health check
        degraded = true;
      }

      // 6. Health validation
      kernelLifecycle.setPhase("health_validation");
      kernelLifecycle.markStep("health_validation", "running");
      try {
        const health = kernelHealth.snapshot();
        if (health.runtimeError > 0 || !health.eventBusOk) {
          degraded = true;
        }
        kernelLifecycle.markStep("health_validation", "ok", {
          message: `${health.runtimeHealthy}/${health.runtimeTotal} healthy`,
        });
      } catch (e) {
        kernelLifecycle.markStep("health_validation", "failed", {
          error: e instanceof Error ? e.message : "health_failed",
        });
        degraded = true;
      }

      // 7. Platform ready (or degraded)
      const diag = kernelDiagnostics.collect();
      if (degraded) {
        kernelLifecycle.markDegraded("boot_completed_with_degradation");
        kernelLifecycle.markStep("platform_ready", "ok", {
          message: "platform_ready_degraded",
        });
        kernelLifecycle.markStep("boot", "ok", { message: "boot_degraded" });
        // Force phase to degraded after markStep platform_ready wouldn't set ready
        kernelLifecycle.setPhase("degraded", "boot_completed_with_degradation");
      } else {
        kernelLifecycle.completeBoot(true);
      }

      return {
        ok: true,
        degraded,
        phase: kernelLifecycle.phase(),
        steps: kernelLifecycle.steps(),
        startupTimeMs: kernelLifecycle.startupTimeMs(),
        diagnosticsId: diag.id,
      };
    } catch (e) {
      const msg = e instanceof Error ? e.message : "kernel_boot_crash";
      // Never rethrow — isolate
      kernelLifecycle.completeBoot(false, msg);
      return {
        ok: false,
        degraded: false,
        phase: kernelLifecycle.phase(),
        steps: kernelLifecycle.steps(),
        startupTimeMs: kernelLifecycle.startupTimeMs(),
        error: msg,
      };
    }
  },
};
