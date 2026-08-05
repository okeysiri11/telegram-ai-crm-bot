/**
 * Runtime registry — Sprint 29.8.
 * Every enterprise runtime registers itself here.
 */

import type { RuntimeAdapter, RuntimeDescriptor, RuntimeId } from "./orchestratorTypes";
import { publishOrchestratorEvent } from "./orchestratorEvents";

const adapters = new Map<RuntimeId, RuntimeAdapter>();

export const runtimeRegistry = {
  clear() {
    adapters.clear();
  },

  register(adapter: RuntimeAdapter): RuntimeDescriptor {
    if (adapters.has(adapter.id)) {
      adapters.set(adapter.id, adapter);
    } else {
      adapters.set(adapter.id, adapter);
      publishOrchestratorEvent("RuntimeRegistered", {
        runtimeId: adapter.id,
        version: adapter.version,
      });
    }
    return this.toDescriptor(adapter);
  },

  get(id: RuntimeId) {
    return adapters.get(id);
  },

  list(): RuntimeAdapter[] {
    return [...adapters.values()];
  },

  ids(): RuntimeId[] {
    return [...adapters.keys()];
  },

  descriptors(): RuntimeDescriptor[] {
    return this.list().map((a) => this.toDescriptor(a));
  },

  toDescriptor(adapter: RuntimeAdapter): RuntimeDescriptor {
    const health = adapter.probeHealth();
    return {
      id: adapter.id,
      label: adapter.label,
      version: adapter.version,
      status: health.status,
      dependencies: [...adapter.dependencies],
      health,
      events: [...adapter.events],
      api: adapter.api,
      permissions: [...adapter.permissions],
      route: adapter.route,
    };
  },
};
