/**
 * Kernel health aggregation — Sprint 29.9.
 */

import { enterpriseOrchestrator } from "@/runtime/orchestrator";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import type { KernelHealthSnapshot } from "./kernelTypes";
import { kernelLifecycle } from "./KernelLifecycle";
import { publishKernelEvent } from "./kernelEvents";

function now() {
  return new Date().toISOString();
}

let eventBusErrors = 0;

export const kernelHealth = {
  clear() {
    eventBusErrors = 0;
  },

  noteEventBusError() {
    eventBusErrors += 1;
  },

  eventBusOk() {
    try {
      // Smoke: subscribe/unsubscribe no-op listener
      const unsub = enterpriseEventBus.subscribe(() => undefined);
      unsub();
      return eventBusErrors < 10;
    } catch {
      return false;
    }
  },

  snapshot(): KernelHealthSnapshot {
    const phase = kernelLifecycle.phase();
    let platformStatus: KernelHealthSnapshot["platformStatus"] = "unknown";
    let runtimeHealthy = 0;
    let runtimeTotal = 0;
    let runtimeError = 0;

    if (enterpriseOrchestrator.isReady()) {
      const h = enterpriseOrchestrator.platformHealth();
      platformStatus = h.status;
      runtimeHealthy = h.healthy;
      runtimeTotal = h.total;
      runtimeError = h.error;
    }

    const eventBusOk = this.eventBusOk();
    const ready = kernelLifecycle.isReady();
    const degraded =
      phase === "degraded" ||
      runtimeError > 0 ||
      (runtimeTotal > 0 && runtimeHealthy < runtimeTotal);

    const snap: KernelHealthSnapshot = {
      phase,
      platformStatus,
      ready,
      degraded,
      runtimeHealthy,
      runtimeTotal,
      runtimeError,
      eventBusOk,
      checkedAt: now(),
    };
    publishKernelEvent("HealthUpdated", {
      phase: snap.phase,
      platformStatus: snap.platformStatus,
      ready: snap.ready,
      degraded: snap.degraded,
    });
    return snap;
  },
};
