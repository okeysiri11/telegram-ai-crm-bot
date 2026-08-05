/**
 * City Visualization REST client — Sprint 29.5.
 */

import { webConfig } from "@/config/webConfig";
import { cityVisualizationRuntime } from "./cityVisualizationRuntime";

export function cityVizApiPrefix() {
  return webConfig.cityVizPrefix || "/api/enterprise-city-viz/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${cityVizApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const cityVisualizationApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: cityVisualizationRuntime.version, mode: "local_engine" };
  },

  async scene() {
    const remote = await tryFetch<{ scene: unknown }>("/scene");
    if (remote?.scene) return remote;
    return { scene: cityVisualizationRuntime.scene() };
  },

  async visible(lod?: string) {
    const q = lod ? `?lod=${encodeURIComponent(lod)}` : "";
    const remote = await tryFetch<Record<string, unknown>>(`/visible${q}`);
    if (remote?.revision != null) return remote;
    return cityVisualizationRuntime.visibleQuery(
      lod as Parameters<typeof cityVisualizationRuntime.visibleQuery>[0],
    );
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: cityVisualizationRuntime.version,
      stats: cityVisualizationRuntime.stats(),
      endpoints: [
        "GET /health",
        "GET /scene",
        "GET /visible",
        "GET /buildings",
        "GET /citizens",
        "GET /companies",
        "GET /assets",
        "GET /activities",
        "GET /districts",
        "GET /inventory",
      ],
    };
  },
};
