/**
 * Enterprise Strategy & OKR Intelligence derivation — Sprint 33.8.
 * Strategic management layer over EI / Learning / Predictive / Runtime / Fabric.
 * No new Strategy Engine / Analytics Engine / Dashboard / AI Core / Store.
 */

import type { LiveEnterpriseSnapshot, RecommendationItem } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { deriveLearning } from "@/self-learning-enterprise/deriveLearning";
import { ENTERPRISE_GOALS, type EnterpriseGoalDef, type GoalDomain } from "./goalsCatalog";

export type GoalStatus = "completed" | "in_progress" | "delayed" | "at_risk";

export type LiveGoal = {
  id: string;
  domain: GoalDomain;
  label: string;
  objective: string;
  kpi: string;
  owner: string;
  priority: EnterpriseGoalDef["priority"];
  deadline: string;
  progress: number;
  status: GoalStatus;
  liveKpi: string;
  keyResults: Array<{ id: string; label: string; progress: number }>;
  aiRecommendation: string;
  blockers: string[];
  forecast: string;
  risk: "low" | "medium" | "high";
};

export type OkrCard = {
  goalId: string;
  objective: string;
  keyResults: string[];
  liveKpi: string;
  progress: number;
  aiRecommendation: string;
  route?: string;
};

export type GoalAlignment = {
  recommendationId: string;
  title: string;
  goalId: string;
  goalLabel: string;
  kpi: string;
  expectedEffect: string;
  ifDone: string;
  ifSkipped: string;
};

export type ExecutiveHorizon = {
  today: string[];
  week: string[];
  month: string[];
  deviations: string[];
  topRisks: string[];
  topOpportunities: string[];
};

export type TimelineItem = {
  id: string;
  label: string;
  deadline: string;
  status: GoalStatus;
  progress: number;
};

export type McGoalsBlock = {
  progressAvg: number;
  riskCount: number;
  forecast: string;
  blockers: string[];
};

export type OkrBundle = {
  goals: LiveGoal[];
  okrCards: OkrCard[];
  alignments: GoalAlignment[];
  executive: ExecutiveHorizon;
  timeline: TimelineItem[];
  mc: McGoalsBlock;
  scenarioImpacts: GoalAlignment[];
};

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function daysToDeadline(deadline: string): number {
  const d = Date.parse(deadline);
  if (Number.isNaN(d)) return 90;
  return Math.round((d - Date.now()) / 86_400_000);
}

function statusFor(progress: number, deadline: string, riskHigh: boolean): GoalStatus {
  if (progress >= 95) return "completed";
  const days = daysToDeadline(deadline);
  if (riskHigh || (progress < 40 && days < 60)) return "at_risk";
  if (progress < 55 && days < 90) return "delayed";
  return "in_progress";
}

function matchGoal(text: string): EnterpriseGoalDef {
  const hit = ENTERPRISE_GOALS.find((g) => g.tokens.test(text));
  return hit || ENTERPRISE_GOALS[hash(text) % ENTERPRISE_GOALS.length]!;
}

export function alignRecommendation(
  item: RecommendationItem | { id: string; title: string },
  goals: LiveGoal[] = [],
): GoalAlignment {
  const def = matchGoal(item.title);
  const live = goals.find((g) => g.id === def.id);
  const progress = live?.progress ?? def.baseProgress;
  return {
    recommendationId: item.id,
    title: item.title,
    goalId: def.id,
    goalLabel: def.label,
    kpi: def.kpi,
    expectedEffect: `+${4 + (hash(item.id) % 9)}% к прогрессу «${def.objective.slice(0, 42)}»`,
    ifDone: `Progress ${progress}% → ~${clamp(progress + 6 + (hash(item.title) % 8))}% · KPI «${def.kpi}» улучшится`,
    ifSkipped: `Риск: цель ${def.label} останется ~${progress}% · возможен статус At Risk к ${def.deadline}`,
  };
}

export function deriveOkr(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[] = [],
): OkrBundle {
  const runtime = deriveRuntime(snapshot, notifications);
  const pred = derivePredictive(snapshot, notifications);
  const intel = deriveIntelligence(snapshot, notifications);
  const fabric = deriveDataFabric(snapshot, { notifications });
  const learning = deriveLearning(snapshot, notifications);

  const failed = runtime.counts.failed + snapshot.aiOps.errors.length;
  const queue = runtime.health.queueSize;
  const crmActive = snapshot.activeModules.includes("crm") || /crm|deal|client/i.test(
    snapshot.activity.map((a) => a.title).join(" "),
  );
  const highRisks = pred.risks.filter((r) => r.severity === "high").length;

  const goals: LiveGoal[] = ENTERPRISE_GOALS.map((def) => {
    let progress = def.baseProgress;
    if (def.domain === "sales" || def.domain === "revenue") {
      progress += crmActive ? 12 : -5;
      progress += Math.min(10, snapshot.aiOps.completed.length * 3);
    }
    if (def.domain === "operations" || def.domain === "production") {
      progress += failed ? -failed * 8 : 10;
      progress += queue >= 3 ? -12 : 6;
      progress += learning.metrics.find((m) => m.id === "auto_ok")!.value > 55 ? 8 : -4;
    }
    if (def.domain === "hr") {
      progress += Math.min(15, runtime.counts.completed * 4);
      progress += intel.knowledgeAware ? 6 : -4;
    }
    if (def.domain === "customer_success") {
      progress += highRisks ? -highRisks * 6 : 8;
      progress += fabric.executive.problemLinks ? -5 : 5;
    }
    if (def.domain === "marketing") {
      progress += intel.decision.decideToday.length * 3;
    }
    if (def.domain === "profit") {
      progress += learning.timeSavedMin > 40 ? 8 : 2;
      progress -= failed * 4;
    }
    progress = clamp(Math.round(progress + ((hash(def.id + snapshot.updatedAt) % 7) - 3)));

    const riskHigh =
      (def.domain === "operations" && failed > 0) ||
      (def.domain === "sales" && !crmActive) ||
      highRisks > 1;
    const status = statusFor(progress, def.deadline, riskHigh);
    const risk: LiveGoal["risk"] =
      status === "at_risk" ? "high" : status === "delayed" ? "medium" : "low";

    const liveKpi =
      def.domain === "operations"
        ? `fail ${failed} · queue ${queue} · avg ${runtime.health.avgResponseMs}ms`
        : def.domain === "sales" || def.domain === "revenue"
          ? pred.forecasts.find((f) => f.id === "clients")?.detail || `${snapshot.aiOps.completed.length} AI closes`
          : def.domain === "hr"
            ? `AI success ~${learning.metrics.find((m) => m.id === "ai_eff")?.value ?? "—"}%`
            : `${progress}% of target`;

    const blockers: string[] = [];
    if (failed && (def.domain === "operations" || def.domain === "production")) {
      blockers.push(snapshot.aiOps.errors[0] || "Runtime failures");
    }
    if (fabric.executive.missingData && def.domain === "customer_success") {
      blockers.push("Missing Data Fabric coverage");
    }
    if (!crmActive && (def.domain === "sales" || def.domain === "revenue")) {
      blockers.push("CRM signals weak");
    }
    if (queue >= 3 && def.domain === "production") {
      blockers.push("Runtime queue bottleneck");
    }

    const aiRecommendation =
      learning.recommendations.find((r) => def.tokens.test(r.title + r.detail))?.title ||
      intel.decision.decideToday[0]?.title ||
      pred.opportunities[0]?.title ||
      "Синхронизировать активность с OKR в Mission Control";

    return {
      id: def.id,
      domain: def.domain,
      label: def.label,
      objective: def.objective,
      kpi: def.kpi,
      owner: def.owner,
      priority: def.priority,
      deadline: def.deadline,
      progress,
      status,
      liveKpi,
      keyResults: def.keyResults.map((label, i) => ({
        id: `${def.id}_kr_${i}`,
        label,
        progress: clamp(progress - 8 + i * 5 + (hash(label) % 6)),
      })),
      aiRecommendation,
      blockers,
      forecast:
        pred.forecasts.find((f) => def.tokens.test(f.label + f.detail))?.detail ||
        `К дедлайну ${def.deadline}: ~${clamp(progress + (risk === "high" ? -5 : 8))}%`,
      risk,
    };
  });

  const okrCards: OkrCard[] = goals.map((g) => ({
    goalId: g.id,
    objective: g.objective,
    keyResults: g.keyResults.map((k) => k.label),
    liveKpi: g.liveKpi,
    progress: g.progress,
    aiRecommendation: g.aiRecommendation,
    route: "/platform-builder/okr",
  }));

  const recoSources: Array<{ id: string; title: string }> = [
    ...snapshot.recommendations.map((r) => ({ id: r.id, title: r.title })),
    ...learning.recommendations.slice(0, 4).map((r) => ({ id: r.id, title: r.title })),
    ...intel.decision.decideToday.slice(0, 2).map((p) => ({ id: p.id, title: p.title })),
  ];

  const alignments = recoSources.slice(0, 10).map((r) => alignRecommendation(r, goals));
  const scenarioImpacts = alignments.slice(0, 6);

  const atRisk = goals.filter((g) => g.status === "at_risk" || g.risk === "high");
  const delayed = goals.filter((g) => g.status === "delayed");

  const executive: ExecutiveHorizon = {
    today: [
      ...intel.decision.decideToday.slice(0, 2).map((p) => p.title),
      ...goals.filter((g) => g.priority === "p0").slice(0, 2).map((g) => `${g.label}: ${g.progress}%`),
    ].slice(0, 4),
    week: [
      `Закрыть blockers: ${goals.flatMap((g) => g.blockers).slice(0, 2).join(" · ") || "нет критичных"}`,
      `Learning: ${learning.recommendations[0]?.title || "optimize workflows"}`,
      pred.executive.needsAttention[0] || "Контроль Predictive risks",
    ],
    month: goals
      .filter((g) => daysToDeadline(g.deadline) < 120)
      .slice(0, 3)
      .map((g) => `${g.label} → ${g.deadline} (${g.progress}%)`),
    deviations: delayed
      .concat(atRisk)
      .slice(0, 4)
      .map((g) => `${g.label}: ${g.status.replace("_", " ")} · ${g.progress}%`),
    topRisks: pred.risks
      .slice(0, 3)
      .map((r) => r.title)
      .concat(atRisk.map((g) => `OKR At Risk · ${g.label}`))
      .slice(0, 4),
    topOpportunities: pred.opportunities
      .slice(0, 2)
      .map((o) => o.title)
      .concat(learning.recommendations.slice(0, 2).map((r) => r.title))
      .slice(0, 4),
  };

  const timeline: TimelineItem[] = goals.map((g) => ({
    id: g.id,
    label: g.label,
    deadline: g.deadline,
    status: g.status,
    progress: g.progress,
  }));

  const progressAvg = Math.round(goals.reduce((s, g) => s + g.progress, 0) / goals.length);
  const mc: McGoalsBlock = {
    progressAvg,
    riskCount: atRisk.length + delayed.length,
    forecast: pred.executive.likelyToday[0] || `Средний прогресс целей → ~${clamp(progressAvg + 5)}%`,
    blockers: [...new Set(goals.flatMap((g) => g.blockers))].slice(0, 4),
  };

  return {
    goals,
    okrCards,
    alignments,
    executive,
    timeline,
    mc,
    scenarioImpacts,
  };
}
