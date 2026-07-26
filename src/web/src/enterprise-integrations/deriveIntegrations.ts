/**
 * Enterprise Integration Hub derivation — Sprint 33.1.
 * Pure client layer over catalog + connectionState + live-ops.
 * No new Integration Engine / API Gateway.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import { hubIntegrations } from "@/integrations/hub";
import {
  ALL_INTEGRATIONS,
  type IntegrationDef,
  type IntegrationStatus,
} from "./integrationCatalog";
import { getConnection, listConnections, resolveStatus } from "./connectionState";

export type IntegrationMonitorRow = {
  id: string;
  title: string;
  category: IntegrationDef["category"];
  status: IntegrationStatus;
  lastSyncAt: string | null;
  operations: number;
  errors: number;
  latencyMs: number;
  hubPath?: string;
  processes: string[];
  aiAgents: string[];
  route?: string;
};

export type IntegrationDashboard = {
  active: number;
  needsSetup: number;
  errors: number;
  lastSyncAt: string | null;
  statusSummary: string;
};

export type TwinIntegrationView = {
  connectedSystems: string[];
  processesUsing: string[];
  aiUsing: string[];
};

export type IntegrationHubBundle = {
  dashboard: IntegrationDashboard;
  rows: IntegrationMonitorRow[];
  twin: TwinIntegrationView;
};

function hubPathFor(def: IntegrationDef): string | undefined {
  if (def.healthHint) return def.healthHint;
  if (!def.hubKey) return undefined;
  const v = (hubIntegrations as Record<string, string>)[def.hubKey];
  return typeof v === "string" ? v : undefined;
}

export function deriveIntegrationHub(snapshot?: LiveEnterpriseSnapshot | null): IntegrationHubBundle {
  void listConnections(); // ensure seeds
  const healthBlob = (snapshot?.health || [])
    .map((h) => `${h.id}:${h.ok ? "ok" : "bad"}`)
    .join(" ");

  const rows: IntegrationMonitorRow[] = ALL_INTEGRATIONS.map((def) => {
    let status = resolveStatus(def.id);
    const conn = getConnection(def.id);

    // Soft signal from live health
    if (def.id === "crm" && snapshot?.health.some((h) => h.id === "crm" && !h.ok)) status = "error";
    if (def.hubKey === "notifications" && /notifications:bad/.test(healthBlob)) status = "error";
    if (def.id === "oauth" && snapshot && !snapshot.mcOk && status === "active") {
      /* keep active — MC is not OAuth */
    }

    return {
      id: def.id,
      title: def.title,
      category: def.category,
      status,
      lastSyncAt: conn?.lastSyncAt || null,
      operations: conn?.operations || 0,
      errors: conn?.errors || (status === "error" ? 1 : 0),
      latencyMs: conn?.latencyMs || 0,
      hubPath: hubPathFor(def),
      processes: def.processes,
      aiAgents: def.aiAgents,
      route: def.route,
    };
  });

  const active = rows.filter((r) => r.status === "active").length;
  const needsSetup = rows.filter((r) => r.status === "needs_setup" || r.status === "draft").length;
  const errors = rows.filter((r) => r.status === "error").length;
  const syncs = rows.map((r) => r.lastSyncAt).filter(Boolean).sort().reverse();
  const lastSyncAt = syncs[0] || null;

  const connected = rows.filter((r) => r.status === "active");
  const twin: TwinIntegrationView = {
    connectedSystems: connected.map((r) => r.title),
    processesUsing: [...new Set(connected.flatMap((r) => r.processes))],
    aiUsing: [...new Set(connected.flatMap((r) => r.aiAgents))],
  };

  return {
    dashboard: {
      active,
      needsSetup,
      errors,
      lastSyncAt,
      statusSummary:
        errors > 0
          ? `${errors} с ошибками подключения`
          : needsSetup > 0
            ? `${active} активны · ${needsSetup} требуют настройки`
            : `${active} интеграций активны`,
    },
    rows,
    twin,
  };
}
