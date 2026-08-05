/**
 * Orchestrator REST client — Sprint 29.8.
 */

import { webConfig } from "@/config/webConfig";
import { enterpriseOrchestrator } from "./EnterpriseOrchestrator";

export function orchestratorApiPrefix() {
  return webConfig.orchestratorPrefix || "/api/enterprise-orchestrator/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${orchestratorApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const orchestratorApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    const h = enterpriseOrchestrator.platformHealth();
    return {
      status: "ok",
      version: enterpriseOrchestrator.version,
      platform: h.status,
      healthy: h.healthy,
      total: h.total,
      mode: "local_engine",
    };
  },

  async runtimes() {
    const remote = await tryFetch<{ runtimes: unknown[] }>("/runtimes");
    if (remote?.runtimes) return remote;
    return { runtimes: enterpriseOrchestrator.runtimes() };
  },

  async graph() {
    const remote = await tryFetch<Record<string, unknown>>("/graph");
    if (remote?.order) return remote;
    return {
      order: enterpriseOrchestrator.dependencyOrder(),
      edges: enterpriseOrchestrator.dependencyEdges(),
      canonicalChain: enterpriseOrchestrator.graph.canonicalChain(),
    };
  },

  async queue() {
    const remote = await tryFetch<{ queue: unknown[] }>("/queue");
    if (remote?.queue) return remote;
    return { queue: enterpriseOrchestrator.queue() };
  },

  async events() {
    const remote = await tryFetch<{ events: unknown[] }>("/events");
    if (remote?.events) return remote;
    return { events: enterpriseOrchestrator.routedEvents() };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: enterpriseOrchestrator.version,
      stats: enterpriseOrchestrator.stats(),
      endpoints: [
        "GET /health",
        "GET /runtimes",
        "GET /graph",
        "GET /queue",
        "GET /events",
        "GET /inventory",
      ],
    };
  },
};
