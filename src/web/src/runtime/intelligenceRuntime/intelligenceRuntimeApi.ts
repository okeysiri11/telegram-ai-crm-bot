/**
 * Intelligence Runtime REST client — Sprint 29.7.
 */

import { webConfig } from "@/config/webConfig";
import { intelligenceRuntime } from "./intelligenceRuntime";

export function intelligenceApiPrefix() {
  return webConfig.intelligencePrefix || "/api/enterprise-intelligence/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${intelligenceApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const intelligenceRuntimeApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return {
      status: "ok",
      version: intelligenceRuntime.version,
      mode: "local_engine",
      advisoryOnly: true,
      autonomousExecution: false,
    };
  },

  async insights() {
    const remote = await tryFetch<{ insights: unknown[] }>("/insights");
    if (remote?.insights) return remote;
    return { insights: intelligenceRuntime.insights() };
  },

  async recommendations() {
    const remote = await tryFetch<{ recommendations: unknown[] }>("/recommendations");
    if (remote?.recommendations) return remote;
    return { recommendations: intelligenceRuntime.recommendations() };
  },

  async risks() {
    const remote = await tryFetch<{ risks: unknown[] }>("/risks");
    if (remote?.risks) return remote;
    return { risks: intelligenceRuntime.risks() };
  },

  async trends() {
    const remote = await tryFetch<{ trends: unknown[] }>("/trends");
    if (remote?.trends) return remote;
    return { trends: intelligenceRuntime.trends() };
  },

  async analytics() {
    const remote = await tryFetch<Record<string, unknown>>("/analytics");
    if (remote?.businessActivity != null) return remote;
    return intelligenceRuntime.analytics();
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: intelligenceRuntime.version,
      policy: intelligenceRuntime.policy,
      stats: intelligenceRuntime.stats(),
      endpoints: [
        "GET /health",
        "GET /insights",
        "GET /recommendations",
        "GET /trends",
        "GET /risks",
        "GET /analytics",
        "GET /inventory",
      ],
    };
  },
};
