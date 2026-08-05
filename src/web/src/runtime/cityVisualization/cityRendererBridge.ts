/**
 * City renderer bridge — Sprint 29.5.
 * Contract for future 2D/3D clients. Does NOT render.
 */

import type { RendererBridgePayload, LodTier } from "./cityVisualizationTypes";

export type CityRendererAdapter = {
  id: string;
  label: string;
  /** Called when scene rebuilt or incremental update available */
  onPayload: (payload: RendererBridgePayload) => void;
};

const adapters = new Map<string, CityRendererAdapter>();
let lastPayload: RendererBridgePayload | null = null;

export const cityRendererBridge = {
  clear() {
    adapters.clear();
    lastPayload = null;
  },

  register(adapter: CityRendererAdapter) {
    adapters.set(adapter.id, adapter);
    if (lastPayload) adapter.onPayload(lastPayload);
    return () => adapters.delete(adapter.id);
  },

  list() {
    return [...adapters.values()].map((a) => ({ id: a.id, label: a.label }));
  },

  /** Push payload to all registered future renderers */
  publish(payload: RendererBridgePayload) {
    lastPayload = payload;
    for (const a of adapters.values()) {
      try {
        a.onPayload(payload);
      } catch {
        /* renderer isolation */
      }
    }
    return adapters.size;
  },

  lastPayload() {
    return lastPayload;
  },

  /** LOD-ready hint for clients */
  recommendLod(entityCount: number): LodTier {
    if (entityCount > 400) return "far";
    if (entityCount > 200) return "medium";
    if (entityCount > 80) return "near";
    return "detail";
  },
};
