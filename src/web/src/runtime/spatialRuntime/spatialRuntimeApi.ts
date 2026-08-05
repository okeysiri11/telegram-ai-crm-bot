/**
 * Spatial Runtime REST client — Sprint 29.4.
 */

import { webConfig } from "@/config/webConfig";
import { spatialRuntime } from "./spatialRuntime";

export function spatialApiPrefix() {
  return webConfig.spatialPrefix || "/api/enterprise-spatial/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${spatialApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const spatialRuntimeApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: spatialRuntime.version, mode: "local_engine" };
  },

  async hierarchy() {
    const remote = await tryFetch<Record<string, unknown>>("/hierarchy");
    if (remote?.city) return remote;
    return spatialRuntime.hierarchy();
  },

  async districts(kind?: string) {
    const q = kind ? `?kind=${encodeURIComponent(kind)}` : "";
    const remote = await tryFetch<{ districts: unknown[] }>(`/districts${q}`);
    if (remote?.districts) return remote;
    return {
      districts: kind
        ? spatialRuntime.districts(kind as Parameters<typeof spatialRuntime.districts>[0])
        : spatialRuntime.districts(),
    };
  },

  async city() {
    const remote = await tryFetch<Record<string, unknown>>("/city");
    if (remote?.stats) return remote;
    return spatialRuntime.cityQuery();
  },

  async route(from: string, to: string) {
    const q = `?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;
    const remote = await tryFetch<{ route: unknown }>(`/route${q}`);
    if (remote?.route) return remote;
    return { route: spatialRuntime.route(from, to) };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: spatialRuntime.version,
      stats: spatialRuntime.stats(),
      endpoints: [
        "GET /health",
        "GET /hierarchy",
        "GET /districts",
        "GET /buildings",
        "GET /route",
        "GET /city",
        "GET /inventory",
      ],
    };
  },
};
