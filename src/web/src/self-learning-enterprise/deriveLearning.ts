/**
 * Self-Learning Enterprise derivation — Sprint 33.7.
 * Continuous optimization signals over EI / Runtime / Predictive / Fabric / Workflows.
 * No new Learning Engine / AI Core / Analytics Engine / Store.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";

export type LearningMetric = {
  id: string;
  label: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "flat";
  detail: string;
};

export type WorkflowOptimization = {
  id: string;
  title: string;
  kind: "longest" | "errors" | "bottleneck" | "repeat";
  detail: string;
  suggestion: string;
  route?: string;
};

export type AiPerformanceRow = {
  id: string;
  name: string;
  tasksDone: number;
  successPct: number;
  avgSec: number;
  knowledgeUse: "high" | "medium" | "low";
  improvement: string;
};

export type KnowledgeEvolution = {
  topUsed: string[];
  stale: string[];
  gaps: string[];
  updates: string[];
};

export type LearningRecommendation = {
  id: string;
  category: "workflow" | "ai_team" | "crm" | "integrations" | "knowledge" | "automation";
  title: string;
  detail: string;
  impact: string;
  route?: string;
};

export type ExecutiveLearningReport = {
  learned: string[];
  faster: string[];
  moreEffective: string[];
  recommended: string[];
};

export type LearningBundle = {
  metrics: LearningMetric[];
  workflowOpts: WorkflowOptimization[];
  aiReview: AiPerformanceRow[];
  knowledge: KnowledgeEvolution;
  recommendations: LearningRecommendation[];
  executive: ExecutiveLearningReport;
  timeSavedMin: number;
};

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

export function deriveLearning(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[] = [],
): LearningBundle {
  const runtime = deriveRuntime(snapshot, notifications);
  const pred = derivePredictive(snapshot, notifications);
  const intel = deriveIntelligence(snapshot, notifications);
  const fabric = deriveDataFabric(snapshot, { notifications });
  const intHub = deriveIntegrationHub(snapshot);

  const completed = Math.max(1, runtime.counts.completed + snapshot.aiOps.completed.length);
  const failed = runtime.counts.failed + snapshot.aiOps.errors.length;
  const successPct = clamp(Math.round((completed / (completed + failed)) * 100));
  const avgSec = Math.max(20, Math.round(runtime.health.avgResponseMs / 10) + runtime.monitor.elapsedSec);
  const recoQuality = clamp(55 + intel.decision.decideToday.length * 8 - pred.risks.filter((r) => r.severity === "high").length * 10);
  const autoSuccess = clamp(40 + completed * 12 - failed * 15);

  const metrics: LearningMetric[] = [
    {
      id: "ai_eff",
      label: "Эффективность AI Team",
      value: successPct,
      unit: "%",
      trend: successPct >= 70 ? "up" : "down",
      detail: `${completed} done · ${failed} fail`,
    },
    {
      id: "wf_eff",
      label: "Эффективность Workflow",
      value: clamp(45 + BUSINESS_WORKFLOW_TEMPLATES.length * 3 + runtime.counts.completed * 8),
      unit: "%",
      trend: runtime.counts.failed ? "flat" : "up",
      detail: `${BUSINESS_WORKFLOW_TEMPLATES.length} templates`,
    },
    {
      id: "speed",
      label: "Скорость выполнения",
      value: avgSec,
      unit: "s avg",
      trend: avgSec < 90 ? "up" : "down",
      detail: `latency ${runtime.health.avgResponseMs} ms`,
    },
    {
      id: "reco_q",
      label: "Качество рекомендаций",
      value: recoQuality,
      unit: "%",
      trend: recoQuality >= 60 ? "up" : "flat",
      detail: `${intel.decision.decideToday.length} decide-today`,
    },
    {
      id: "auto_ok",
      label: "Успешные автоматизации",
      value: autoSuccess,
      unit: "score",
      trend: autoSuccess >= 50 ? "up" : "down",
      detail: `${runtime.counts.completed} completed autos`,
    },
  ];

  const longest = [...runtime.jobs].sort((a, b) => b.elapsedSec - a.elapsedSec)[0];
  const workflowOpts: WorkflowOptimization[] = [
    {
      id: "wo_long",
      kind: "longest",
      title: longest ? `Длинный процесс: ${longest.title}` : "Длинные процессы не зафиксированы",
      detail: longest ? `${longest.elapsedSec}s · ${longest.currentStep}` : "Runtime idle",
      suggestion: longest
        ? "Разбить шаг на параллельные AI specialists или кэшировать Knowledge lookup"
        : "Собрать baseline после первой недели Runtime",
      route: "/platform-builder/runtime",
    },
    {
      id: "wo_err",
      kind: "errors",
      title: failed ? `Частые ошибки: ${failed}` : "Частые ошибки: низкий уровень",
      detail: snapshot.aiOps.errors[0] || "нет критичных error signals",
      suggestion: failed
        ? "Добавить retry policy + Approval для high-risk шагов"
        : "Сохранить текущие guardrails Autonomy L2–L3",
      route: "/platform-builder/autonomy",
    },
    {
      id: "wo_bn",
      kind: "bottleneck",
      title: runtime.health.queueSize >= 2 ? "Узкое место: очередь Runtime" : "Узкие места под контролем",
      detail: `Queue ${runtime.health.queueSize} · active ${runtime.counts.active}`,
      suggestion:
        runtime.health.queueSize >= 2
          ? "Scale AI concurrency или упростить Workflow template"
          : "Мониторить Predictive queue forecast",
      route: "/platform-builder/workflow-center",
    },
    {
      id: "wo_rep",
      kind: "repeat",
      title: "Повторяющиеся действия",
      detail: snapshot.activity.slice(0, 3).map((a) => a.title).join(" · ") || "мало повторов",
      suggestion: "Вынести повторы в Marketplace prompt pack / Workflow template",
      route: "/platform-builder/solution-hub",
    },
  ];

  const agents = [
    ...new Set(
      snapshot.aiOps.running.concat(snapshot.aiOps.recent).concat(["Concierge", "Sales Specialist", "Ops Copilot"]),
    ),
  ].slice(0, 6);

  const aiReview: AiPerformanceRow[] = agents.map((name, i) => {
    const tasksDone = 2 + (hash(name) % 9) + (i === 0 ? snapshot.aiOps.completed.length : 0);
    const success = clamp(60 + (hash(name + "s") % 35) - failed * 5);
    const avg = 25 + (hash(name) % 80);
    const kb: AiPerformanceRow["knowledgeUse"] =
      intel.knowledgeAware && hash(name) % 3 !== 0 ? "high" : hash(name) % 2 === 0 ? "medium" : "low";
    return {
      id: `ai_${i}_${hash(name)}`,
      name,
      tasksDone,
      successPct: success,
      avgSec: avg,
      knowledgeUse: kb,
      improvement:
        kb === "low"
          ? "Подключить Knowledge Base в skill pack"
          : success < 75
            ? "Добавить HITL на failed paths"
            : "Можно повысить autonomy для low-risk задач",
    };
  });

  const knowledge: KnowledgeEvolution = {
    topUsed: intel.knowledgeAware
      ? ["Policy playbook", "CRM objection scripts", "Refund FAQ"]
      : ["Seed FAQ", "Onboarding checklist"],
    stale: fabric.executive.missingData
      ? ["Legacy pricing sheet", "Old SLA draft"]
      : ["Q1 campaign brief (review)"],
    gaps: fabric.entities
      .filter((e) => e.missing)
      .map((e) => `Gap · ${e.label}`)
      .concat(intel.knowledgeAware ? [] : ["Weak KB awareness signals"])
      .slice(0, 4),
    updates: [
      "Обновить Knowledge из последних Documents",
      "Синхронизировать CRM win notes → KB",
      intHub.dashboard.needsSetup ? "Закрыть setup gaps интеграций для KB sync" : "KB sync каналы в норме",
    ],
  };

  const recommendations: LearningRecommendation[] = [
    {
      id: "rec_wf",
      category: "workflow",
      title: workflowOpts[0]!.suggestion.slice(0, 64),
      detail: workflowOpts[0]!.detail,
      impact: "−15–25% cycle time",
      route: "/platform-builder/workflow-center",
    },
    {
      id: "rec_ai",
      category: "ai_team",
      title: aiReview[0]?.improvement || "Улучшить AI Team skills",
      detail: `${aiReview[0]?.name || "AI"} · success ${aiReview[0]?.successPct ?? "—"}%`,
      impact: "+AI productivity",
      route: "/platform-builder/ai-team",
    },
    {
      id: "rec_crm",
      category: "crm",
      title: "Автоматизировать follow-up после Hot leads",
      detail: pred.forecasts.find((f) => f.id === "clients")?.detail || "CRM activity signals",
      impact: "+pipeline velocity",
      route: "/workspace/crm",
    },
    {
      id: "rec_int",
      category: "integrations",
      title: intHub.dashboard.needsSetup
        ? "Закрыть integrations needing setup"
        : "Стабилизировать sync latency",
      detail: intHub.dashboard.statusSummary,
      impact: "−sync errors",
      route: "/platform-builder/integrations",
    },
    {
      id: "rec_kb",
      category: "knowledge",
      title: knowledge.updates[0]!,
      detail: knowledge.gaps[0] || "KB coverage",
      impact: "+recommendation quality",
      route: "/platform-builder/knowledge",
    },
    {
      id: "rec_auto",
      category: "automation",
      title: "Поднять autonomy для low-risk document archive",
      detail: "Learning: low-risk actions с высокой success rate",
      impact: `${Math.round(autoSuccess / 4)} мин/день`,
      route: "/platform-builder/autonomy",
    },
    ...intel.decision.decideToday.slice(0, 2).map((p) => ({
      id: `rec_intel_${p.id}`,
      category: "automation" as const,
      title: p.title,
      detail: p.detail,
      impact: "EI priority",
      route: p.route,
    })),
  ];

  const timeSavedMin = Math.round(autoSuccess * 0.4 + completed * 3 + recoQuality * 0.15);

  const executive: ExecutiveLearningReport = {
    learned: [
      `AI success ≈ ${successPct}% на текущем горизонте`,
      intel.knowledgeAware ? "Knowledge awareness улучшает рекомендации" : "Нужно усилить KB signals",
      `Runtime avg step ~${avgSec}s`,
    ],
    faster: [
      avgSec < 120 ? "Среднее время шага в целевом диапазоне" : "Есть потенциал ускорения очереди",
      workflowOpts[2]!.kind === "bottleneck" && runtime.health.queueSize < 2
        ? "Очередь не растёт"
        : "Очередь — кандидат на оптимизацию",
    ],
    moreEffective: [
      `Автоматизации score ${autoSuccess}`,
      `Качество рекомендаций ${recoQuality}%`,
      fabric.executive.problemLinks
        ? "Data Fabric всё ещё имеет проблемные связи"
        : "Связность данных стабильна",
    ],
    recommended: recommendations.slice(0, 4).map((r) => r.title),
  };

  return {
    metrics,
    workflowOpts,
    aiReview,
    knowledge,
    recommendations,
    executive,
    timeSavedMin,
  };
}
