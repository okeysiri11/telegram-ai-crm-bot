/**
 * EBN REST API client — Sprint 29.0.
 * Versioned prefix: /api/enterprise-ebn/v1
 * Local engine is source of truth; HTTP used when available.
 */

import { webConfig } from "@/config/webConfig";
import { businessNetworkEngine } from "./businessNetworkEngine";

export function ebnApiPrefix() {
  return webConfig.ebnPrefix;
}

async function tryFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${ebnApiPrefix()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** REST surface — falls back to in-process engine (Enterprise Runtime standard). */
export const businessNetworkApi = {
  async health() {
    const remote = await tryFetch<{ status: string; version?: string }>("/health");
    if (remote) return remote;
    return { status: "ok", version: businessNetworkEngine.version, mode: "local_engine" };
  },

  async listProfiles() {
    const remote = await tryFetch<{ profiles: unknown[] }>("/profiles");
    if (remote?.profiles) return remote;
    businessNetworkEngine.startup();
    return { profiles: businessNetworkEngine.listProfiles() };
  },

  async getProfile(id: string) {
    const remote = await tryFetch<{ profile: unknown }>(`/profiles/${encodeURIComponent(id)}`);
    if (remote?.profile) return remote;
    return { profile: businessNetworkEngine.getProfile(id) };
  },

  async listRelationships(profileId?: string) {
    const q = profileId ? `?profileId=${encodeURIComponent(profileId)}` : "";
    const remote = await tryFetch<{ relationships: unknown[] }>(`/relationships${q}`);
    if (remote?.relationships) return remote;
    return { relationships: businessNetworkEngine.listRelationships(profileId) };
  },

  async createRelationship(body: {
    fromProfileId: string;
    toProfileId: string;
    type: string;
  }) {
    const remote = await tryFetch<{ ok: boolean; relationship?: unknown }>("/relationships", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (remote) return remote;
    return businessNetworkEngine.createRelationship({
      fromProfileId: body.fromProfileId,
      toProfileId: body.toProfileId,
      type: body.type as Parameters<typeof businessNetworkEngine.createRelationship>[0]["type"],
    });
  },

  async approveRelationship(id: string) {
    const remote = await tryFetch<{ relationship?: unknown }>(
      `/relationships/${encodeURIComponent(id)}/approve`,
      { method: "POST" },
    );
    if (remote) return remote;
    return { relationship: businessNetworkEngine.approveRelationship(id) };
  },

  async graph(profileId?: string) {
    const q = profileId ? `?profileId=${encodeURIComponent(profileId)}` : "";
    const remote = await tryFetch<{ nodes: unknown[]; edges: unknown[] }>(`/graph${q}`);
    if (remote?.nodes) return remote;
    return profileId
      ? businessNetworkEngine.graphConnections(profileId)
      : businessNetworkEngine.graphSnapshot();
  },

  async listConversations() {
    const remote = await tryFetch<{ conversations: unknown[] }>("/conversations");
    if (remote?.conversations) return remote;
    return { conversations: businessNetworkEngine.listConversations() };
  },

  async cityFacade(profileId: string) {
    const remote = await tryFetch<{ facade: unknown }>(
      `/city/${encodeURIComponent(profileId)}`,
    );
    if (remote?.facade) return remote;
    return { facade: businessNetworkEngine.cityFacade(profileId) };
  },

  async inventory() {
    const remote = await tryFetch<Record<string, unknown>>("/inventory");
    if (remote) return remote;
    return {
      version: businessNetworkEngine.version,
      stats: businessNetworkEngine.stats(),
      endpoints: [
        "GET /health",
        "GET /profiles",
        "GET /profiles/:id",
        "GET /relationships",
        "POST /relationships",
        "POST /relationships/:id/approve",
        "POST /relationships/:id/reject",
        "GET /graph",
        "GET /conversations",
        "GET /documents",
        "GET /city/:profileId",
        "GET /inventory",
      ],
    };
  },
};
