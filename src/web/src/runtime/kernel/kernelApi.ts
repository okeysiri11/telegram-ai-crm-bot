/**
 * Kernel REST client — Sprint 29.9.
 */

import { webConfig } from "@/config/webConfig";
import { enterpriseKernel } from "./EnterpriseKernel";

export function kernelApiPrefix() {
  return webConfig.kernelPrefix || "/api/enterprise-kernel/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${kernelApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const kernelApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    const s = enterpriseKernel.status();
    return {
      status: "ok",
      version: enterpriseKernel.version,
      phase: s.phase,
      ready: s.ready,
      degraded: s.degraded,
      mode: "local_engine",
    };
  },

  async status() {
    const remote = await tryFetch<Record<string, unknown>>("/status");
    if (remote?.phase) return remote;
    return enterpriseKernel.status();
  },

  async diagnostics() {
    const remote = await tryFetch<Record<string, unknown>>("/diagnostics");
    if (remote?.id) return remote;
    return enterpriseKernel.diagnostics();
  },

  async bootSequence() {
    const remote = await tryFetch<{ steps: unknown[] }>("/boot-sequence");
    if (remote?.steps) return remote;
    return { steps: enterpriseKernel.bootSequence() };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: enterpriseKernel.version,
      stats: enterpriseKernel.stats(),
      endpoints: [
        "GET /health",
        "GET /status",
        "GET /diagnostics",
        "GET /boot-sequence",
        "GET /modules",
        "GET /recovery",
        "GET /config",
        "GET /inventory",
      ],
    };
  },
};
