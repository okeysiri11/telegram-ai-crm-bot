/**
 * Integration connection records — Sprint 33.1.
 * localStorage persistence (same pattern as Marketplace).
 * No new Integration Engine.
 */

import type { IntegrationStatus } from "./integrationCatalog";
import { ALL_INTEGRATIONS, getIntegration } from "./integrationCatalog";

const KEY = "ewp_integrations_connected_v1";

export type ConnectionRecord = {
  integrationId: string;
  status: IntegrationStatus;
  connectedAt: string;
  lastSyncAt: string;
  operations: number;
  errors: number;
  latencyMs: number;
};

type ConnMap = Record<string, ConnectionRecord>;

function readMap(): ConnMap {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return {};
    return JSON.parse(raw) as ConnMap;
  } catch {
    return {};
  }
}

function writeMap(map: ConnMap) {
  try {
    localStorage.setItem(KEY, JSON.stringify(map));
  } catch {
    /* ignore */
  }
}

function seedDefaults(): ConnMap {
  const map = readMap();
  let dirty = false;
  const now = new Date().toISOString();
  for (const def of ALL_INTEGRATIONS) {
    if (map[def.id]) continue;
    if (def.defaultStatus === "active") {
      map[def.id] = {
        integrationId: def.id,
        status: "active",
        connectedAt: now,
        lastSyncAt: now,
        operations: 40 + Math.floor(Math.random() * 80),
        errors: 0,
        latencyMs: 80 + Math.floor(Math.random() * 120),
      };
      dirty = true;
    }
  }
  if (dirty) writeMap(map);
  return map;
}

export function listConnections(): ConnectionRecord[] {
  return Object.values(seedDefaults());
}

export function getConnection(id: string): ConnectionRecord | undefined {
  return seedDefaults()[id];
}

export function resolveStatus(id: string): IntegrationStatus {
  const rec = getConnection(id);
  if (rec) return rec.status;
  return getIntegration(id)?.defaultStatus || "draft";
}

export function connectIntegration(id: string): ConnectionRecord {
  const map = seedDefaults();
  const now = new Date().toISOString();
  const prev = map[id];
  const rec: ConnectionRecord = {
    integrationId: id,
    status: "active",
    connectedAt: prev?.connectedAt || now,
    lastSyncAt: now,
    operations: (prev?.operations || 0) + 1,
    errors: 0,
    latencyMs: 60 + Math.floor(Math.random() * 90),
  };
  map[id] = rec;
  writeMap(map);
  return rec;
}

export function markError(id: string, detail?: string): ConnectionRecord {
  void detail;
  const map = seedDefaults();
  const now = new Date().toISOString();
  const prev = map[id];
  const rec: ConnectionRecord = {
    integrationId: id,
    status: "error",
    connectedAt: prev?.connectedAt || now,
    lastSyncAt: now,
    operations: prev?.operations || 0,
    errors: (prev?.errors || 0) + 1,
    latencyMs: prev?.latencyMs || 999,
  };
  map[id] = rec;
  writeMap(map);
  return rec;
}

export function syncIntegration(id: string): ConnectionRecord {
  const map = seedDefaults();
  const now = new Date().toISOString();
  const prev = map[id] || {
    integrationId: id,
    status: "active" as const,
    connectedAt: now,
    lastSyncAt: now,
    operations: 0,
    errors: 0,
    latencyMs: 100,
  };
  const rec: ConnectionRecord = {
    ...prev,
    status: prev.status === "error" ? "active" : prev.status === "draft" ? "active" : prev.status,
    lastSyncAt: now,
    operations: prev.operations + 1 + Math.floor(Math.random() * 5),
    latencyMs: 50 + Math.floor(Math.random() * 150),
  };
  if (rec.status === "needs_setup") rec.status = "active";
  map[id] = rec;
  writeMap(map);
  return rec;
}

export function setNeedsSetup(id: string): ConnectionRecord {
  const map = seedDefaults();
  const now = new Date().toISOString();
  const prev = map[id];
  const rec: ConnectionRecord = {
    integrationId: id,
    status: "needs_setup",
    connectedAt: prev?.connectedAt || now,
    lastSyncAt: prev?.lastSyncAt || now,
    operations: prev?.operations || 0,
    errors: prev?.errors || 0,
    latencyMs: prev?.latencyMs || 0,
  };
  map[id] = rec;
  writeMap(map);
  return rec;
}
