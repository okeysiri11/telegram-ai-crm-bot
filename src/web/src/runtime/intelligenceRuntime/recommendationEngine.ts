/**
 * Recommendation engine — Sprint 29.7.
 * Advisory only: requiresApproval is always true. Never executes actions.
 */

import type {
  EnterpriseInsight,
  EnterpriseRecommendation,
  EnterpriseRisk,
  RecommendationAudience,
} from "./intelligenceTypes";
import type { LiveSignals } from "./liveSignals";
import { publishIntelligenceEvent } from "./intelligenceEvents";

function uid() {
  return `rec_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

function rec(input: Omit<EnterpriseRecommendation, "id" | "createdAt" | "requiresApproval">): EnterpriseRecommendation {
  const recommendation: EnterpriseRecommendation = {
    ...input,
    id: uid(),
    requiresApproval: true,
    createdAt: now(),
  };
  publishIntelligenceEvent("RecommendationCreated", {
    recommendationId: recommendation.id,
    audience: recommendation.audience,
    suggestedActionId: recommendation.suggestedActionId,
    requiresApproval: true,
    autoExecute: false,
  });
  return recommendation;
}

export const recommendationEngine = {
  /**
   * Produce advisory recommendations. Callers must use Interaction/Workflow
   * with explicit user approval — this engine never executes.
   */
  generate(
    signals: LiveSignals,
    insights: EnterpriseInsight[],
    risks: EnterpriseRisk[],
  ): EnterpriseRecommendation[] {
    const out: EnterpriseRecommendation[] = [];
    const insightIds = insights.map((i) => i.id);
    const riskByKind = (kind: EnterpriseRisk["kind"]) => risks.filter((r) => r.kind === kind);

    const audiences: RecommendationAudience[] = [
      "manager",
      "owner",
      "department",
      "project",
      "asset",
      "partner",
      "citizen",
    ];

    // Owner
    out.push(
      rec({
        audience: "owner",
        title: "Review morning operational pulse",
        rationale: `Business activity signals online=${signals.citizensOnline}, meetings=${signals.meetingsActive}`,
        suggestedRoute: "/intelligence",
        priority: "info",
        relatedInsightIds: insightIds.filter((_, i) => insights[i]?.category === "business_activity"),
        relatedRiskIds: [],
        subjectIds: [],
      }),
    );

    // Manager — overload
    for (const r of riskByKind("overloaded_employee")) {
      out.push(
        rec({
          audience: "manager",
          title: "Balance load at busy buildings",
          rationale: r.detail,
          suggestedActionId: "create_meeting",
          suggestedRoute: "/interactions",
          priority: r.severity,
          relatedInsightIds: [],
          relatedRiskIds: [r.id],
          subjectIds: r.subjectIds,
        }),
      );
    }

    // Department / workflow
    if (signals.workflowFailed > 0 || signals.automationPending > 0) {
      out.push(
        rec({
          audience: "department",
          title: "Inspect workflow & automation queues",
          rationale: "Bottlenecks or failures detected — approve any remediation manually",
          suggestedRoute: "/workflow-runtime",
          priority: signals.workflowFailed > 0 ? "medium" : "low",
          relatedInsightIds: insights.filter((i) => i.category === "workflow").map((i) => i.id),
          relatedRiskIds: riskByKind("workflow_failure").map((r) => r.id),
          subjectIds: [],
        }),
      );
    }

    // Project
    for (const p of signals.projects.filter((x) => x.members <= 1).slice(0, 3)) {
      out.push(
        rec({
          audience: "project",
          title: `Strengthen participation · ${p.name}`,
          rationale: "Low participant count may affect delivery",
          suggestedActionId: "assign_task",
          suggestedRoute: "/life-engine",
          priority: "low",
          relatedInsightIds: insights.filter((i) => i.subjectIds.includes(p.id)).map((i) => i.id),
          relatedRiskIds: [],
          subjectIds: [p.id],
        }),
      );
    }

    // Assets
    for (const r of riskByKind("idle_asset")) {
      out.push(
        rec({
          audience: "asset",
          title: "Review idle asset inventory",
          rationale: r.detail,
          suggestedRoute: "/assets",
          suggestedActionId: "open_asset",
          priority: r.severity,
          relatedInsightIds: insights.filter((i) => i.category === "asset").map((i) => i.id),
          relatedRiskIds: [r.id],
          subjectIds: [],
        }),
      );
    }

    // Partners
    for (const r of riskByKind("missing_approval")) {
      out.push(
        rec({
          audience: "partner",
          title: "Approve or decline pending partners",
          rationale: r.detail,
          suggestedRoute: "/business-network",
          suggestedActionId: "open_company",
          priority: r.severity,
          relatedInsightIds: insights.filter((i) => i.category === "partner").map((i) => i.id),
          relatedRiskIds: [r.id],
          subjectIds: [],
        }),
      );
    }

    // Citizens
    out.push(
      rec({
        audience: "citizen",
        title: "Update presence & workspace focus",
        rationale: "Keep Digital Citizen presence aligned with City occupancy",
        suggestedRoute: "/digital-citizens",
        suggestedActionId: "open_citizen",
        priority: "info",
        relatedInsightIds: insights.filter((i) => i.category === "citizen").map((i) => i.id),
        relatedRiskIds: [],
        subjectIds: [],
      }),
    );

    // Ensure every audience appears at least once when possible
    for (const a of audiences) {
      if (!out.some((r) => r.audience === a)) {
        out.push(
          rec({
            audience: a,
            title: `Advisory check-in · ${a}`,
            rationale: "No critical signals — continue monitoring (no auto-action)",
            suggestedRoute: "/intelligence",
            priority: "info",
            relatedInsightIds: [],
            relatedRiskIds: [],
            subjectIds: [],
          }),
        );
      }
    }

    return out;
  },
};
