/**
 * Digital Citizen REST client — Sprint 29.1.
 * Prefix: /api/enterprise-edc/v1
 */

import { webConfig } from "@/config/webConfig";
import { digitalCitizenEngine } from "./digitalCitizenEngine";

export function edcApiPrefix() {
  return webConfig.edcPrefix || "/api/enterprise-edc/v1";
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${edcApiPrefix()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const digitalCitizenApi = {
  async health() {
    const remote = await tryFetch<{ status: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: digitalCitizenEngine.version, mode: "local_engine" };
  },

  async listCitizens() {
    const remote = await tryFetch<{ citizens: unknown[] }>("/citizens");
    if (remote?.citizens) return remote;
    digitalCitizenEngine.startup();
    return { citizens: digitalCitizenEngine.listCitizens() };
  },

  async getCitizen(id: string) {
    const remote = await tryFetch<{ citizen: unknown }>(`/citizens/${encodeURIComponent(id)}`);
    if (remote?.citizen) return remote;
    return { citizen: digitalCitizenEngine.getCitizen(id) };
  },

  async listMemberships(citizenId?: string) {
    const q = citizenId ? `?citizenId=${encodeURIComponent(citizenId)}` : "";
    const remote = await tryFetch<{ memberships: unknown[] }>(`/memberships${q}`);
    if (remote?.memberships) return remote;
    return { memberships: digitalCitizenEngine.listMemberships(citizenId) };
  },

  async workspace(citizenId: string) {
    const remote = await tryFetch<{ workspace: unknown }>(
      `/workspace/${encodeURIComponent(citizenId)}`,
    );
    if (remote?.workspace) return remote;
    return { workspace: digitalCitizenEngine.workspace(citizenId) };
  },

  async presence() {
    const remote = await tryFetch<{ presence: unknown[] }>("/presence");
    if (remote?.presence) return remote;
    return { presence: digitalCitizenEngine.presenceSnapshot() };
  },

  async setPresence(citizenId: string, status: string) {
    const remote = await tryFetch<{ ok: boolean }>("/presence", {
      method: "POST",
      body: JSON.stringify({ citizenId, status }),
    });
    if (remote) return remote;
    const c = digitalCitizenEngine.setPresence(citizenId, status as never);
    return { ok: Boolean(c) };
  },

  async cityFacade(citizenId: string) {
    const remote = await tryFetch<{ facade: unknown }>(
      `/city/${encodeURIComponent(citizenId)}`,
    );
    if (remote?.facade) return remote;
    return { facade: digitalCitizenEngine.cityFacade(citizenId) };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: digitalCitizenEngine.version,
      stats: digitalCitizenEngine.stats(),
      endpoints: [
        "GET /health",
        "GET /citizens",
        "GET /citizens/:id",
        "GET /memberships",
        "GET /workspace/:citizenId",
        "GET /presence",
        "POST /presence",
        "GET /ai",
        "GET /city/:citizenId",
        "GET /inventory",
      ],
    };
  },
};
