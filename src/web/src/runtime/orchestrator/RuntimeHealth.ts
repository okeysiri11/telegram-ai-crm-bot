/**
 * Aggregated runtime health — Sprint 29.8.
 */

import type { PlatformHealth, RuntimeHealthReport, RuntimeHealthStatus, RuntimeId } from "./orchestratorTypes";
import { runtimeRegistry } from "./RuntimeRegistry";
import { publishOrchestratorEvent } from "./orchestratorEvents";

const lastReports = new Map<RuntimeId, RuntimeHealthReport>();

function now() {
  return new Date().toISOString();
}

function rank(status: RuntimeHealthStatus): number {
  switch (status) {
    case "error":
      return 5;
    case "maintenance":
      return 4;
    case "busy":
      return 3;
    case "starting":
      return 2;
    case "stopped":
      return 1;
    default:
      return 0;
  }
}

export const runtimeHealth = {
  clear() {
    lastReports.clear();
  },

  probe(id: RuntimeId): RuntimeHealthReport {
    const adapter = runtimeRegistry.get(id);
    if (!adapter) {
      const report: RuntimeHealthReport = {
        status: "stopped",
        message: "not_registered",
        checkedAt: now(),
      };
      lastReports.set(id, report);
      return report;
    }
    const started = performance.now();
    let report: RuntimeHealthReport;
    try {
      report = adapter.probeHealth();
      report = {
        ...report,
        latencyMs: Math.round(performance.now() - started),
        checkedAt: report.checkedAt || now(),
      };
    } catch (e) {
      report = {
        status: "error",
        message: e instanceof Error ? e.message : "probe_failed",
        checkedAt: now(),
        latencyMs: Math.round(performance.now() - started),
      };
    }
    const prev = lastReports.get(id);
    lastReports.set(id, report);
    if (!prev || prev.status !== report.status) {
      publishOrchestratorEvent("RuntimeHealthChanged", {
        runtimeId: id,
        status: report.status,
        message: report.message,
      });
    }
    return report;
  },

  probeAll(): Record<string, RuntimeHealthReport> {
    const out: Record<string, RuntimeHealthReport> = {};
    for (const a of runtimeRegistry.list()) {
      out[a.id] = this.probe(a.id);
    }
    return out;
  },

  get(id: RuntimeId) {
    return lastReports.get(id) || this.probe(id);
  },

  platform(): PlatformHealth {
    const reports = this.probeAll();
    const counts: PlatformHealth = {
      status: "healthy",
      healthy: 0,
      starting: 0,
      stopped: 0,
      error: 0,
      busy: 0,
      maintenance: 0,
      total: 0,
      updatedAt: now(),
    };
    let worst: RuntimeHealthStatus = "healthy";
    for (const r of Object.values(reports)) {
      counts.total += 1;
      counts[r.status] += 1;
      if (rank(r.status) > rank(worst)) worst = r.status;
    }
    counts.status = counts.total === 0 ? "stopped" : worst;
    publishOrchestratorEvent("PlatformHealthUpdated", {
      status: counts.status,
      healthy: counts.healthy,
      error: counts.error,
      total: counts.total,
    });
    return counts;
  },
};
