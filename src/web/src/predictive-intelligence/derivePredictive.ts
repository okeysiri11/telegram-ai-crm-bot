/**
 * Predictive Intelligence derivation — Sprint 33.4.
 * Pure client forecasts over EI / Twin / Fabric / Runtime signals.
 * No new Prediction Engine / AI Core / Analytics Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";

export type ForecastMetric = {
  id: string;
  label: string;
  current: number;
  forecast: number;
  unit: string;
  deltaPct: number;
  tone: "up" | "down" | "flat" | "risk";
  detail: string;
};

export type WhatIfScenario = {
  id: string;
  title: string;
  action: string;
  effect: string;
  impacts: string[];
  risks: string[];
  recommendation: string;
};

export type RiskSignal = {
  id: string;
  kind: "bottleneck" | "overload" | "error" | "missing_data" | "dependency";
  title: string;
  detail: string;
  severity: "low" | "medium" | "high";
  route?: string;
};

export type OpportunitySignal = {
  id: string;
  kind: "growth" | "automation" | "unused" | "ai_reco";
  title: string;
  detail: string;
  route?: string;
};

export type ExecutiveForecast = {
  likelyToday: string[];
  needsAttention: string[];
  risingRisks: string[];
  kpiChanges: string[];
};

export type TwinForecastZone = {
  id: string;
  label: string;
  tone: "risk" | "bottleneck" | "active" | "calm";
  detail: string;
};

export type PredictiveBundle = {
  forecasts: ForecastMetric[];
  scenarios: WhatIfScenario[];
  risks: RiskSignal[];
  opportunities: OpportunitySignal[];
  executive: ExecutiveForecast;
  twinZones: TwinForecastZone[];
};

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function delta(cur: number, next: number): number {
  if (cur === 0) return next > 0 ? 100 : 0;
  return Math.round(((next - cur) / cur) * 100);
}

export const WHAT_IF_SCENARIOS: WhatIfScenario[] = [
  {
    id: "grow_sales",
    title: "Увеличить команду продаж",
    action: "Hire / scale Sales team",
    effect: "Как изменится загрузка CRM",
    impacts: [
      "CRM pipeline +18–25%",
      "Deals throughput ↑",
      "AI Sales Ops queue +12%",
    ],
    risks: ["Временный backlog onboarding", "Нужна настройка Integration Hub"],
    recommendation: "Сначала усилить CRM sync и Concierge triage",
  },
  {
    id: "change_workflow",
    title: "Изменить Workflow",
    action: "Edit primary automation template",
    effect: "Какие процессы изменятся",
    impacts: [
      "Runtime active jobs перестроятся",
      "AI Team перераспределит шаги",
      "Data Fabric lineage обновит edges",
    ],
    risks: ["Paused jobs до валидации", "Краткий рост retries"],
    recommendation: "Прогнать Scenario в Runtime Monitor перед rollout",
  },
  {
    id: "disable_integration",
    title: "Отключить интеграцию",
    action: "Disable a connected integration",
    effect: "Какие сервисы пострадают",
    impacts: [
      "Sync clients/deals остановится",
      "Notification channels деградируют",
      "Twin External Systems покажет gap",
    ],
    risks: ["Missing data в Data Fabric", "Failed runtime steps"],
    recommendation: "Сначала найти зависимости в Impact Analysis",
  },
];

export function derivePredictive(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[] = [],
): PredictiveBundle {
  const intel = deriveIntelligence(snapshot, notifications);
  const runtime = deriveRuntime(snapshot, notifications);
  const fabric = deriveDataFabric(snapshot, { notifications });

  const aiLoad = clamp(20 + snapshot.aiOps.running.length * 22 + snapshot.aiOps.queue.length * 12);
  const aiForecast = clamp(aiLoad + (runtime.health.queueSize > 2 ? 15 : 5) - (runtime.counts.completed ? 4 : 0));

  const queueNow = runtime.health.queueSize;
  const queueForecast = clamp(queueNow + snapshot.aiOps.errors.length * 2 + (runtime.counts.paused ? 1 : 0), 0, 40);

  const clientActive = snapshot.activity.filter((a) => a.kind === "crm" || a.kind === "client" || a.kind === "deal").length;
  const clientForecast = clamp(clientActive * 12 + (snapshot.activeModules.includes("crm") ? 35 : 15));

  const wfDone = snapshot.aiOps.completed.length;
  const wfForecast = clamp(40 + wfDone * 15 + BUSINESS_WORKFLOW_TEMPLATES.length * 2 - runtime.counts.failed * 10);

  const kpiNow = clamp(55 + snapshot.health.filter((h) => h.ok).length * 4 - snapshot.aiOps.errors.length * 8);
  const kpiForecast = clamp(kpiNow + (intel.decision.opportunities.length ? 6 : 0) - (intel.decision.risks.length ? 5 : 0));

  const forecasts: ForecastMetric[] = [
    {
      id: "kpi",
      label: "Прогноз KPI",
      current: kpiNow,
      forecast: kpiForecast,
      unit: "index",
      deltaPct: delta(kpiNow, kpiForecast),
      tone: kpiForecast >= kpiNow ? "up" : "risk",
      detail: "Агрегат health + opportunities − risks",
    },
    {
      id: "ai_load",
      label: "Прогноз загрузки AI",
      current: aiLoad,
      forecast: aiForecast,
      unit: "%",
      deltaPct: delta(aiLoad, aiForecast),
      tone: aiForecast > 80 ? "risk" : aiForecast >= aiLoad ? "up" : "down",
      detail: `${snapshot.aiOps.running.length} running · Q ${snapshot.aiOps.queue.length}`,
    },
    {
      id: "queues",
      label: "Прогноз очередей",
      current: queueNow,
      forecast: queueForecast,
      unit: "jobs",
      deltaPct: delta(Math.max(queueNow, 1), queueForecast),
      tone: queueForecast > queueNow ? "risk" : "flat",
      detail: "Runtime queue + errors + paused",
    },
    {
      id: "clients",
      label: "Прогноз активности клиентов",
      current: clamp(clientActive * 10 + 20),
      forecast: clientForecast,
      unit: "signal",
      deltaPct: delta(Math.max(clientActive * 10 + 20, 1), clientForecast),
      tone: clientForecast >= 40 ? "up" : "flat",
      detail: "CRM / deal / client activity",
    },
    {
      id: "workflows",
      label: "Прогноз выполнения Workflow",
      current: clamp(30 + wfDone * 12),
      forecast: wfForecast,
      unit: "%",
      deltaPct: delta(Math.max(30 + wfDone * 12, 1), wfForecast),
      tone: wfForecast >= 50 ? "up" : "down",
      detail: `${BUSINESS_WORKFLOW_TEMPLATES.length} templates`,
    },
  ];

  const risks: RiskSignal[] = [];
  if (runtime.health.activeExecutions >= 2 && runtime.health.queueSize >= 2) {
    risks.push({
      id: "r_bottleneck",
      kind: "bottleneck",
      title: "Узкое место в Runtime",
      detail: "Активные executions + растущая очередь",
      severity: "high",
      route: "/platform-builder/runtime",
    });
  }
  if (aiForecast >= 80 || runtime.health.avgResponseMs > 200) {
    risks.push({
      id: "r_overload",
      kind: "overload",
      title: "Перегрузка AI",
      detail: `Прогноз загрузки ${aiForecast}% · avg ${runtime.health.avgResponseMs} ms`,
      severity: "high",
      route: "/platform-builder/ai-team",
    });
  }
  if (runtime.counts.failed > 0 || snapshot.aiOps.errors.length > 0) {
    risks.push({
      id: "r_errors",
      kind: "error",
      title: "Потенциальные ошибки",
      detail: `${runtime.counts.failed || snapshot.aiOps.errors.length} failed / error signals`,
      severity: "medium",
      route: "/platform-builder/mission-control",
    });
  }
  if (fabric.executive.missingData > 0) {
    risks.push({
      id: "r_missing",
      kind: "missing_data",
      title: "Отсутствие данных",
      detail: `${fabric.executive.missingData} entities с missing signals`,
      severity: "medium",
      route: "/platform-builder/data-fabric",
    });
  }
  if (fabric.executive.problemLinks > 0) {
    risks.push({
      id: "r_deps",
      kind: "dependency",
      title: "Конфликты зависимостей",
      detail: `${fabric.executive.problemLinks} проблемных связей в Data Fabric`,
      severity: fabric.executive.problemLinks > 2 ? "high" : "low",
      route: "/platform-builder/data-fabric",
    });
  }
  if (!risks.length) {
    risks.push({
      id: "r_calm",
      kind: "bottleneck",
      title: "Критических узких мест нет",
      detail: "Сигналы стабильны на горизонте прогноза",
      severity: "low",
    });
  }

  const opportunities: OpportunitySignal[] = [];
  for (const o of intel.decision.opportunities.slice(0, 3)) {
    opportunities.push({
      id: `o_${o.id}`,
      kind: "growth",
      title: o.title,
      detail: o.detail,
      route: o.route,
    });
  }
  if (BUSINESS_WORKFLOW_TEMPLATES.length > 3 && runtime.counts.active < 2) {
    opportunities.push({
      id: "o_auto",
      kind: "automation",
      title: "Процессы для автоматизации",
      detail: "Есть шаблоны Workflow при низкой runtime-нагрузке",
      route: "/platform-builder/workflow-center",
    });
  }
  if (fabric.executive.missingData > 0 || fabric.entities.some((e) => e.missing)) {
    opportunities.push({
      id: "o_unused",
      kind: "unused",
      title: "Неиспользуемые возможности данных",
      detail: "Подключить недостающие сущности через Integration Hub / Knowledge",
      route: "/platform-builder/integrations",
    });
  }
  for (const p of intel.decision.decideToday.slice(0, 2)) {
    opportunities.push({
      id: `o_ai_${p.id}`,
      kind: "ai_reco",
      title: p.title,
      detail: p.detail,
      route: p.route,
    });
  }
  if (!opportunities.length) {
    opportunities.push({
      id: "o_default",
      kind: "ai_reco",
      title: "Открыть Enterprise Intelligence",
      detail: "Собрать brief и приоритеты на сегодня",
      route: "/dashboard",
    });
  }

  const executive: ExecutiveForecast = {
    likelyToday: [
      intel.brief.bullets[0] || "Стабильная операционная активность",
      aiForecast > aiLoad ? "Рост загрузки AI Team" : "AI load стабилен",
      clientForecast > 40 ? "Активность клиентов выше среднего" : "Клиентский поток умеренный",
    ],
    needsAttention: [
      ...risks.filter((r) => r.severity !== "low").slice(0, 2).map((r) => r.title),
      ...(runtime.health.needsIntervention ? ["Runtime требует вмешательства"] : []),
    ].slice(0, 3),
    risingRisks: risks.filter((r) => r.severity === "high").map((r) => r.title).slice(0, 3),
    kpiChanges: forecasts.map((f) => `${f.label}: ${f.current}→${f.forecast} (${f.deltaPct >= 0 ? "+" : ""}${f.deltaPct}%)`),
  };
  if (!executive.needsAttention.length) executive.needsAttention.push("Критичных эскалаций нет");
  if (!executive.risingRisks.length) executive.risingRisks.push("Риски на контроле");

  const twinZones: TwinForecastZone[] = [
    {
      id: "zone_ai",
      label: "AI Team",
      tone: aiForecast >= 80 ? "risk" : aiForecast >= 55 ? "active" : "calm",
      detail: `Прогноз загрузки ${aiForecast}%`,
    },
    {
      id: "zone_runtime",
      label: "Runtime / Workflows",
      tone: queueForecast > queueNow + 1 ? "bottleneck" : runtime.counts.active ? "active" : "calm",
      detail: `Очередь ${queueNow}→${queueForecast}`,
    },
    {
      id: "zone_crm",
      label: "CRM / Clients",
      tone: clientForecast >= 50 ? "active" : "calm",
      detail: `Активность ${clientForecast}`,
    },
    {
      id: "zone_data",
      label: "Data Fabric",
      tone: fabric.executive.problemLinks || fabric.executive.missingData ? "risk" : "calm",
      detail: `${fabric.executive.problemLinks} problems · ${fabric.executive.missingData} missing`,
    },
  ];

  return {
    forecasts,
    scenarios: WHAT_IF_SCENARIOS,
    risks,
    opportunities,
    executive,
    twinZones,
  };
}
