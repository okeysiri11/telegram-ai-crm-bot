/**
 * Insight engine — Sprint 29.7 (advisory).
 */

import type { AnalyticsSnapshot, EnterpriseInsight, EnterpriseRisk, DetectedPattern } from "./intelligenceTypes";
import type { LiveSignals } from "./liveSignals";
import { publishIntelligenceEvent } from "./intelligenceEvents";

function uid() {
  return `ins_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

export function buildAnalytics(
  signals: LiveSignals,
  risks: EnterpriseRisk[],
  insightCount: number,
  recommendationCount: number,
): AnalyticsSnapshot {
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
  const businessActivity = Math.min(
    100,
    signals.meetingsActive * 15 +
      signals.citizensOnline * 10 +
      signals.partnersApproved * 5 +
      Math.round(districtAvg / 2),
  );

  return {
    businessActivity,
    workflowBottlenecks: signals.workflowRunning + signals.automationPending + signals.workflowFailed,
    citizenOnline: signals.citizensOnline,
    assetUtilizationPct: utilization,
    partnerRelations: signals.partnersApproved,
    projectHealth,
    districtActivityAvg: districtAvg,
    openRisks: risks.length,
    insightCount,
    recommendationCount,
  };
}

export const insightEngine = {
  generate(
    signals: LiveSignals,
    risks: EnterpriseRisk[],
    patterns: DetectedPattern[],
  ): EnterpriseInsight[] {
    const insights: EnterpriseInsight[] = [];

    insights.push({
      id: uid(),
      category: "business_activity",
      title: "Enterprise City pulse",
      summary: `${signals.citizensOnline}/${signals.citizensTotal} citizens present · ${signals.meetingsActive} active meetings · ${signals.profiles} companies`,
      severity: signals.citizensOnline > 0 ? "info" : "low",
      subjectIds: signals.occupancyHot.slice(0, 3).map((h) => h.buildingId),
      metrics: {
        online: signals.citizensOnline,
        meetings: signals.meetingsActive,
        profiles: signals.profiles,
      },
      source: "life+ebn",
      createdAt: now(),
    });

    if (signals.workflowRunning + signals.automationPending > 0) {
      insights.push({
        id: uid(),
        category: "workflow",
        title: "Workflow bottleneck signal",
        summary: `${signals.workflowRunning} running workflows · ${signals.automationPending} automation pending`,
        severity: signals.workflowFailed > 0 ? "medium" : "info",
        subjectIds: [],
        metrics: {
          running: signals.workflowRunning,
          pending: signals.automationPending,
          failed: signals.workflowFailed,
        },
        source: "workflow+automation",
        createdAt: now(),
      });
    }

    insights.push({
      id: uid(),
      category: "citizen",
      title: "Citizen activity",
      summary: `${signals.interactionActions} recent interaction actions · selection size ${signals.selectionCount}`,
      severity: "info",
      subjectIds: [],
      metrics: {
        online: signals.citizensOnline,
        interactions: signals.interactionActions,
      },
      source: "interaction+citizens",
      createdAt: now(),
    });

    insights.push({
      id: uid(),
      category: "asset",
      title: "Asset utilization",
      summary: `${signals.assetsInUse} in use · ${signals.assetsAvailable} available · ${signals.assetsMaintenance} maintenance`,
      severity: signals.assetsMaintenance > 0 ? "low" : "info",
      subjectIds: [],
      metrics: {
        total: signals.assetsTotal,
        inUse: signals.assetsInUse,
        available: signals.assetsAvailable,
        maintenance: signals.assetsMaintenance,
      },
      source: "asset_runtime",
      createdAt: now(),
    });

    insights.push({
      id: uid(),
      category: "partner",
      title: "Partner relations",
      summary: `${signals.partnersApproved} approved · ${signals.partnersPending} pending approvals`,
      severity: signals.partnersPending > 0 ? "low" : "info",
      subjectIds: [],
      metrics: {
        approved: signals.partnersApproved,
        pending: signals.partnersPending,
      },
      source: "business_network",
      createdAt: now(),
    });

    for (const p of signals.projects.slice(0, 5)) {
      insights.push({
        id: uid(),
        category: "project",
        title: `Project health · ${p.name}`,
        summary: `${p.members} participants`,
        severity: p.members === 0 ? "medium" : "info",
        subjectIds: [p.id],
        metrics: { members: p.members },
        source: "life_engine",
        createdAt: now(),
      });
    }

    for (const d of signals.districtActivity
      .slice()
      .sort((a, b) => b.activity - a.activity)
      .slice(0, 4)) {
      insights.push({
        id: uid(),
        category: "district",
        title: `District activity · ${d.districtId}`,
        summary: `Activity ${d.activity} · population ${d.population}`,
        severity: d.activity >= 60 ? "low" : "info",
        subjectIds: [d.districtId],
        metrics: { activity: d.activity, population: d.population },
        source: "city_visualization",
        createdAt: now(),
      });
    }

    if (risks.length) {
      insights.push({
        id: uid(),
        category: "operations",
        title: "Operational risk summary",
        summary: `${risks.length} advisory risk signal(s) — no automatic remediation`,
        severity: risks.some((r) => r.severity === "high" || r.severity === "critical")
          ? "medium"
          : "low",
        subjectIds: risks.flatMap((r) => r.subjectIds).slice(0, 6),
        metrics: { risks: risks.length },
        source: "risk_detector",
        createdAt: now(),
      });
    }

    if (patterns.length) {
      insights.push({
        id: uid(),
        category: "operations",
        title: "Patterns observed",
        summary: patterns.map((p) => p.name).join(", "),
        severity: "info",
        subjectIds: [],
        metrics: { patterns: patterns.length },
        source: "pattern_detector",
        createdAt: now(),
      });
    }

    for (const i of insights) {
      publishIntelligenceEvent("InsightCreated", {
        insightId: i.id,
        category: i.category,
        severity: i.severity,
      });
    }
    return insights;
  },
};
