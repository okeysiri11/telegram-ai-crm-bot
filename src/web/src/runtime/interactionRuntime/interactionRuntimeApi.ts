/**
 * Interaction Runtime REST client — Sprint 29.6.
 */

import { webConfig } from "@/config/webConfig";
import { interactionRuntime } from "./interactionRuntime";

export function interactionApiPrefix() {
  return webConfig.interactionPrefix || "/api/enterprise-interaction/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${interactionApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const interactionRuntimeApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: interactionRuntime.version, mode: "local_engine" };
  },

  async sessions() {
    const remote = await tryFetch<{ sessions: unknown[] }>("/sessions");
    if (remote?.sessions) return remote;
    return { sessions: interactionRuntime.sessions() };
  },

  async selection() {
    const remote = await tryFetch<Record<string, unknown>>("/selection");
    if (remote?.revision != null) return remote;
    return interactionRuntime.selection();
  },

  async search(q: string) {
    const remote = await tryFetch<{ hits: unknown[] }>(`/search?q=${encodeURIComponent(q)}`);
    if (remote?.hits) return remote;
    return { hits: interactionRuntime.search(q) };
  },

  async history() {
    const remote = await tryFetch<{ history: unknown[] }>("/history");
    if (remote?.history) return remote;
    return { history: interactionRuntime.history() };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: interactionRuntime.version,
      stats: interactionRuntime.stats(),
      endpoints: [
        "GET /health",
        "GET /sessions",
        "GET /selection",
        "GET /search",
        "GET /navigation",
        "GET /actions",
        "GET /history",
        "GET /inventory",
      ],
    };
  },
};
