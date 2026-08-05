/**
 * Enterprise Orchestrator — Sprint 29.8.
 * Central coordination layer over existing Enterprise Runtimes (additive only).
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import {
  ORCHESTRATOR_RUNTIME_VERSION,
  type RuntimeId,
  type SchedulerOperation,
} from "./orchestratorTypes";
import { orchestratorEvents } from "./orchestratorEvents";
import { runtimeRegistry } from "./RuntimeRegistry";
import { runtimeDependencyGraph, CircularDependencyError } from "./RuntimeDependencyGraph";
import { runtimeHealth } from "./RuntimeHealth";
import { runtimeScheduler } from "./RuntimeScheduler";
import { runtimeDispatcher } from "./RuntimeDispatcher";
import { workflowCoordinator } from "./WorkflowCoordinator";
import { registerAllRuntimeAdapters } from "./runtimeAdapters";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "orchestrator_open",
    action: "open_orchestrator_runtime",
    label: "Open Orchestrator Runtime",
    kind: "navigate",
    keywords: ["orchestrator", "runtime registry", "health", "dependencies"],
    route: "/orchestrator",
    permission: "*",
  });
  commandRuntime.register({
    id: "orchestrator_health",
    action: "probe_platform_health",
    label: "Probe Platform Health",
    kind: "system",
    keywords: ["health", "orchestrator"],
    permission: "*",
    handler: async () => {
      const h = enterpriseOrchestrator.platformHealth();
      return { ok: true, message: `${h.status} · ${h.healthy}/${h.total} healthy` };
    },
  });
}

export const enterpriseOrchestrator = {
  version: ORCHESTRATOR_RUNTIME_VERSION,

  startup() {
    if (booted) return this.stats();
    commandRuntime.startup();
    runtimeRegistry.clear();
    runtimeHealth.clear();
    runtimeScheduler.clear();
    workflowCoordinator.clear();
    orchestratorEvents.clear();

    registerAllRuntimeAdapters();
    runtimeDependencyGraph.assertAcyclic();

    // Start all runtimes in dependency order (orchestration only)
    const job = runtimeScheduler.startupAll();
    if (job.status === "failed") {
      // Still mark booted — individual runtimes may have partial state
    }

    workflowCoordinator.start();
    registerCommands();
    booted = true;

    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: {
        stream: "orchestrator_runtime",
        ready: true,
        version: ORCHESTRATOR_RUNTIME_VERSION,
        runtimes: runtimeRegistry.ids().length,
      },
    });
    orchestratorEvents.publish("RuntimeStarted", {
      runtimeId: "orchestrator",
      count: runtimeRegistry.ids().length,
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  shutdown() {
    workflowCoordinator.stop();
    runtimeScheduler.shutdownAll();
    booted = false;
    orchestratorEvents.publish("RuntimeStopped", { platform: true });
  },

  registry: runtimeRegistry,
  graph: runtimeDependencyGraph,
  health: runtimeHealth,
  scheduler: runtimeScheduler,
  dispatcher: runtimeDispatcher,
  coordinator: workflowCoordinator,
  events: orchestratorEvents,

  runtimes() {
    if (!booted) this.startup();
    return runtimeRegistry.descriptors();
  },

  getRuntime(id: RuntimeId) {
    if (!booted) this.startup();
    const a = runtimeRegistry.get(id);
    return a ? runtimeRegistry.toDescriptor(a) : undefined;
  },

  dependencyOrder() {
    if (!booted) this.startup();
    return runtimeDependencyGraph.order();
  },

  dependencyEdges() {
    if (!booted) this.startup();
    return runtimeDependencyGraph.edges();
  },

  platformHealth() {
    if (!booted) this.startup();
    return runtimeHealth.platform();
  },

  schedule(operation: SchedulerOperation, runtimeId?: RuntimeId) {
    if (!booted) this.startup();
    return runtimeDispatcher.dispatch(operation, runtimeId);
  },

  queue() {
    if (!booted) this.startup();
    return runtimeScheduler.list(40);
  },

  routedEvents(limit = 30) {
    if (!booted) this.startup();
    return workflowCoordinator.recent(limit);
  },

  stats() {
    if (!booted) this.startup();
    const health = runtimeHealth.platform();
    return {
      version: ORCHESTRATOR_RUNTIME_VERSION,
      runtimes: runtimeRegistry.ids().length,
      order: runtimeDependencyGraph.order(),
      edges: runtimeDependencyGraph.edges().length,
      health,
      queuePending: runtimeScheduler.pending().length,
      routed: workflowCoordinator.recent(200).length,
      events: orchestratorEvents.list(200).length,
      coordinatorActive: workflowCoordinator.isActive(),
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    return {
      version: ORCHESTRATOR_RUNTIME_VERSION,
      runtimes: this.runtimes(),
      order: this.dependencyOrder(),
      edges: this.dependencyEdges(),
      canonicalChain: runtimeDependencyGraph.canonicalChain(),
      health: this.platformHealth(),
      queue: this.queue(),
      routedEvents: this.routedEvents(25),
      events: orchestratorEvents.list(30),
      stats: this.stats(),
      routeMap: workflowCoordinator.routeMap(),
    };
  },

  __resetForTests() {
    workflowCoordinator.stop();
    runtimeScheduler.clear();
    runtimeHealth.clear();
    runtimeRegistry.clear();
    workflowCoordinator.clear();
    orchestratorEvents.clear();
    booted = false;
  },
};

export { CircularDependencyError };
