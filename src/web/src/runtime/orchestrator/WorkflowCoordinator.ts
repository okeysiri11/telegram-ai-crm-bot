/**
 * Workflow / event coordinator — Sprint 29.8.
 * Routes EventBus events to appropriate runtimes via orchestration hooks.
 * Additive layer — does not remove existing direct runtime wiring.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import type { EnterpriseEvent } from "@/integration-hub/types";
import type { RoutedEvent, RuntimeId } from "./orchestratorTypes";
import { runtimeDispatcher } from "./RuntimeDispatcher";
import { publishOrchestratorEvent } from "./orchestratorEvents";

function uid() {
  return `route_${Math.random().toString(36).slice(2, 10)}`;
}

const recent: RoutedEvent[] = [];
let unsub: (() => void) | null = null;
let enabled = false;

/** Map bus event types → runtime targets for refresh/sync orchestration */
const ROUTE_MAP: Record<string, RuntimeId[]> = {
  business_network_update: ["business_network", "intelligence"],
  digital_citizen_update: ["digital_citizen", "life", "intelligence"],
  life_engine_update: ["life", "city_visualization", "intelligence"],
  asset_runtime_update: ["asset", "city_visualization", "intelligence"],
  spatial_runtime_update: ["spatial", "city_visualization", "interaction"],
  city_visualization_update: ["city_visualization", "interaction", "intelligence"],
  interaction_runtime_update: ["interaction", "intelligence"],
  intelligence_runtime_update: ["intelligence"],
  workflow_update: ["workflow", "automation", "intelligence"],
  runtime_update: ["intelligence"],
};

export const workflowCoordinator = {
  clear() {
    recent.length = 0;
  },

  recent(limit = 40) {
    return recent.slice(0, limit);
  },

  routeMap() {
    return { ...ROUTE_MAP };
  },

  /** Resolve targets for a bus event type */
  resolveTargets(busType: string): RuntimeId[] {
    return ROUTE_MAP[busType] || [];
  },

  /**
   * Route an event: record + optionally refresh target runtimes.
   * Orchestration only — targets decide how to refresh.
   */
  route(event: Pick<EnterpriseEvent, "type" | "payload">, opts?: { refresh?: boolean }): RoutedEvent {
    const targets = this.resolveTargets(event.type);
    const entry: RoutedEvent = {
      id: uid(),
      at: new Date().toISOString(),
      busType: event.type,
      targetRuntimeIds: targets,
      payload: event.payload,
    };
    recent.unshift(entry);
    if (recent.length > 300) recent.length = 300;

    if (opts?.refresh !== false) {
      for (const id of targets) {
        // Soft refresh — orchestration hint; adapters no-op safely if unchanged
        if (id === "intelligence") {
          runtimeDispatcher.refresh("intelligence");
        } else if (id === "city_visualization") {
          runtimeDispatcher.refresh("city_visualization");
        }
      }
    }

    publishOrchestratorEvent("EventRouted", {
      busType: event.type,
      targets,
      routedId: entry.id,
    });
    return entry;
  },

  start() {
    if (enabled) return;
    enabled = true;
    unsub?.();
    unsub = enterpriseEventBus.subscribe((event) => {
      if (!enabled) return;
      if (!ROUTE_MAP[event.type]) return;
      // Observe & record; avoid recursive refresh storms — record only for most events
      this.route(event, { refresh: false });
    });
  },

  stop() {
    enabled = false;
    unsub?.();
    unsub = null;
  },

  isActive() {
    return enabled;
  },
};
