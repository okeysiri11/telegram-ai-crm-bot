/**
 * Trend analyzer — Sprint 29.7 (advisory).
 */

import type { EnterpriseTrend, TrendPoint } from "./intelligenceTypes";
import type { LiveSignals } from "./liveSignals";
import { publishIntelligenceEvent } from "./intelligenceEvents";

function uid() {
  return `tr_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

const baselines = new Map<string, number>();

function point(key: string, label: string, value: number): TrendPoint {
  const prev = baselines.get(key) ?? value;
  const delta = value - prev;
  baselines.set(key, value);
  return {
    key,
    label,
    value,
    delta,
    direction: delta > 0 ? "up" : delta < 0 ? "down" : "flat",
  };
}

export const trendAnalyzer = {
  clear() {
    baselines.clear();
  },

  analyze(signals: LiveSignals): EnterpriseTrend[] {
    const utilization =
      signals.assetsTotal > 0
        ? Math.round((signals.assetsInUse / signals.assetsTotal) * 100)
        : 0;
    const districtAvg =
      signals.districtActivity.length > 0
        ? Math.round(
            signals.districtActivity.reduce((s, d) => s + d.activity, 0) /
              signals.districtActivity.length,
          )
        : 0;
    const projectHealth =
      signals.projects.length === 0
        ? 50
        : Math.min(
            100,
            Math.round(
              (signals.projects.reduce((s, p) => s + Math.min(10, p.members), 0) /
                Math.max(1, signals.projects.length)) *
                12,
            ),
          );

    const trends: EnterpriseTrend[] = [
      {
        id: uid(),
        domain: "citizen",
        label: "Citizen presence",
        points: [
          point("citizens_online", "Online", signals.citizensOnline),
          point("meetings_active", "Active meetings", signals.meetingsActive),
        ],
        updatedAt: now(),
      },
      {
        id: uid(),
        domain: "asset",
        label: "Asset utilization",
        points: [
          point("asset_util", "Utilization %", utilization),
          point("asset_maint", "Maintenance", signals.assetsMaintenance),
        ],
        updatedAt: now(),
      },
      {
        id: uid(),
        domain: "workflow",
        label: "Workflow throughput",
        points: [
          point("wf_running", "Running", signals.workflowRunning),
          point("wf_failed", "Failed", signals.workflowFailed),
          point("wf_done", "Completed", signals.workflowCompleted),
        ],
        updatedAt: now(),
      },
      {
        id: uid(),
        domain: "partner",
        label: "Partner network",
        points: [
          point("partners_approved", "Approved", signals.partnersApproved),
          point("partners_pending", "Pending", signals.partnersPending),
        ],
        updatedAt: now(),
      },
      {
        id: uid(),
        domain: "district",
        label: "District activity",
        points: [
          point("district_avg", "Avg activity", districtAvg),
          point("project_health", "Project health", projectHealth),
        ],
        updatedAt: now(),
      },
    ];

    for (const t of trends) {
      publishIntelligenceEvent("TrendUpdated", {
        trendId: t.id,
        domain: t.domain,
        points: t.points.length,
      });
    }
    return trends;
  },
};
