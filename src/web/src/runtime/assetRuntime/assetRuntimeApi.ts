/**
 * Asset Runtime REST client — Sprint 29.3.
 */

import { webConfig } from "@/config/webConfig";
import { assetRuntime } from "./assetRuntime";

export function assetApiPrefix() {
  return webConfig.assetPrefix || "/api/enterprise-assets/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${assetApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const assetRuntimeApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: assetRuntime.version, mode: "local_engine" };
  },

  async listAssets(buildingId?: string) {
    const q = buildingId ? `?buildingId=${encodeURIComponent(buildingId)}` : "";
    const remote = await tryFetch<{ assets: unknown[] }>(`/assets${q}`);
    if (remote?.assets) return remote;
    return { assets: assetRuntime.list(buildingId ? { buildingId } : undefined) };
  },

  async getAsset(id: string) {
    const remote = await tryFetch<{ asset: unknown }>(`/assets/${encodeURIComponent(id)}`);
    if (remote?.asset) return remote;
    return { asset: assetRuntime.get(id) };
  },

  async city() {
    const remote = await tryFetch<Record<string, unknown>>("/city");
    if (remote?.totals) return remote;
    return assetRuntime.cityQuery();
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: assetRuntime.version,
      stats: assetRuntime.stats(),
      endpoints: [
        "GET /health",
        "GET /assets",
        "GET /assets/:id",
        "POST /assets",
        "POST /assets/:id/assign",
        "POST /assets/:id/transfer",
        "POST /assets/:id/move",
        "POST /assets/:id/lifecycle",
        "GET /city",
        "GET /inventory",
      ],
    };
  },
};
