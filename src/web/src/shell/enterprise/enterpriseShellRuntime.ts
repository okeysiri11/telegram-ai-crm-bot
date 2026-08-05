/**
 * Enterprise Shell Runtime — Sprint 28.5.
 * Lifecycle orchestration over Integration Hub + Runtime Engine + Desktop.
 */

import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { sessionCoordinator } from "@/integration-hub/sessionCoordinator";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { registerIntegrationSearch } from "@/integration-hub/searchRegistration";
import { shellModuleRegistry } from "./shellModuleRegistry";
import { useShellPreferences } from "./shellPreferencesStore";
import { logActivity } from "@/workspace-engine/activityJournal";
import { SHELL_QUICK_ACTIONS, registerQuickActionsInSearch } from "./shellQuickActions";
import { refreshShellSearch } from "./shellSearch";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseKernel } from "@/runtime/kernel";

export type ShellLifecyclePhase =
  | "idle"
  | "starting"
  | "restoring"
  | "ready"
  | "shutting_down"
  | "stopped";

export type ShellLifecycleSnapshot = {
  phase: ShellLifecyclePhase;
  startedAt: string | null;
  modules: number;
  quickActions: number;
  lastError: string | null;
};

type Listener = (snap: ShellLifecycleSnapshot) => void;

const listeners = new Set<Listener>();
let phase: ShellLifecyclePhase = "idle";
let startedAt: string | null = null;
let lastError: string | null = null;
let busUnsub: (() => void) | null = null;

function snapshot(): ShellLifecycleSnapshot {
  return {
    phase,
    startedAt,
    modules: shellModuleRegistry.list().length,
    quickActions: SHELL_QUICK_ACTIONS.length,
    lastError,
  };
}

function emit() {
  const snap = snapshot();
  listeners.forEach((l) => l(snap));
}

export const enterpriseShellRuntime = {
  subscribe(listener: Listener) {
    listeners.add(listener);
    listener(snapshot());
    return () => {
      listeners.delete(listener);
    };
  },

  getSnapshot() {
    return snapshot();
  },

  /** Startup · restore · lazy init. Idempotent. */
  async startup() {
    if (phase === "ready" || phase === "starting" || phase === "restoring") return snapshot();
    phase = "starting";
    emit();
    try {
      useShellPreferences.getState().hydrate();
      registerIntegrationSearch();
      refreshShellSearch();
      registerQuickActionsInSearch();
      commandRuntime.setSurface("shell");
      commandRuntime.startup();
      // Sprint 29.9 — Kernel boots platform (config → orchestrator → runtimes → health)
      enterpriseKernel.boot();
      runtimeEngine.start();
      phase = "restoring";
      emit();
      sessionCoordinator.restoreAll();
      busUnsub?.();
      busUnsub = enterpriseEventBus.subscribe((event) => {
        if (event.type === "open_module" || event.type === "navigate") {
          const path = event.path || String(event.payload?.path || "");
          const mod = shellModuleRegistry.list().find((m) => path.startsWith(m.route.split("?")[0]!));
          if (mod) useShellPreferences.getState().rememberModule(mod.id);
          try {
            logActivity({
              kind: "navigate",
              title: `Opened ${mod?.label || path}`,
              detail: path,
            });
          } catch {
            /* ignore */
          }
        }
      });
      startedAt = new Date().toISOString();
      phase = "ready";
      lastError = null;
      enterpriseEventBus.publish({
        type: "runtime_update",
        source: "system",
        payload: { stream: "runtime", shell: "ready", modules: shellModuleRegistry.list().length },
      });
      logActivity({ kind: "system", title: "Enterprise Shell ready", detail: `modules ${shellModuleRegistry.list().length}` });
    } catch (e) {
      lastError = e instanceof Error ? e.message : "Shell startup failed";
      phase = "ready";
    }
    emit();
    return snapshot();
  },

  shutdown() {
    if (phase === "stopped" || phase === "idle") return;
    phase = "shutting_down";
    emit();
    busUnsub?.();
    busUnsub = null;
    try {
      runtimeEngine.stop();
    } catch {
      /* ignore */
    }
    phase = "stopped";
    emit();
  },

  /** Lazy module touch — records load without duplicating route lazy(). */
  initializeModule(moduleId: string) {
    const mod = shellModuleRegistry.get(moduleId);
    if (!mod) return false;
    useShellPreferences.getState().rememberModule(moduleId);
    logActivity({ kind: "system", title: `Module init · ${mod.label}`, detail: mod.route });
    return true;
  },

  unloadModule(moduleId: string) {
    // Dynamic modules only — catalog modules stay registered
    const mod = shellModuleRegistry.get(moduleId);
    if (mod?.source === "dynamic") {
      shellModuleRegistry.unregister(moduleId);
      refreshShellSearch();
      return true;
    }
    return false;
  },

  /** Execute a shell quick action / registered command via Command Runtime. */
  executeCommand(actionOrId: string, args?: Record<string, unknown>) {
    commandRuntime.setSurface("shell");
    return commandRuntime.execute(actionOrId, args);
  },

  executeQuickAction(quickActionId: string) {
    const qa = SHELL_QUICK_ACTIONS.find((a) => a.id === quickActionId);
    if (!qa) return commandRuntime.execute(quickActionId);
    return this.executeCommand(qa.id);
  },
};
