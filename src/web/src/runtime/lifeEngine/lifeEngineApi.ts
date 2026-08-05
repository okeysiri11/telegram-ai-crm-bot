/**
 * Life Engine REST client — Sprint 29.2.
 * Prefix: /api/enterprise-life/v1
 */

import { webConfig } from "@/config/webConfig";
import { lifeEngine } from "./lifeEngine";

export function lifeApiPrefix() {
  return webConfig.lifePrefix || "/api/enterprise-life/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${lifeApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const lifeEngineApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: lifeEngine.version, mode: "local_engine" };
  },

  async cityRuntime() {
    const remote = await tryFetch<Record<string, unknown>>("/city");
    if (remote?.citizens) return remote;
    return lifeEngine.cityRuntime();
  },

  async occupancy(buildingId?: string) {
    const q = buildingId ? `?buildingId=${encodeURIComponent(buildingId)}` : "";
    const remote = await tryFetch<{ occupancy: unknown[] }>(`/occupancy${q}`);
    if (remote?.occupancy) return remote;
    return { occupancy: lifeEngine.occupancy(buildingId) };
  },

  async timeline(subjectKind?: string, subjectId?: string) {
    const params = new URLSearchParams();
    if (subjectKind) params.set("subjectKind", subjectKind);
    if (subjectId) params.set("subjectId", subjectId);
    const q = params.toString() ? `?${params}` : "";
    const remote = await tryFetch<{ timeline: unknown[] }>(`/timeline${q}`);
    if (remote?.timeline) return remote;
    if (subjectKind && subjectId) {
      return {
        timeline: lifeEngine.timeline.forSubject(subjectKind as never, subjectId),
      };
    }
    return { timeline: lifeEngine.timeline.unified(40) };
  },

  async events() {
    const remote = await tryFetch<{ events: unknown[] }>("/events");
    if (remote?.events) return remote;
    return { events: lifeEngine.events(40) };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: lifeEngine.version,
      stats: lifeEngine.stats(),
      endpoints: [
        "GET /health",
        "GET /city",
        "GET /occupancy",
        "GET /timeline",
        "GET /events",
        "GET /meetings",
        "GET /vehicles",
        "GET /inventory",
      ],
    };
  },
};
