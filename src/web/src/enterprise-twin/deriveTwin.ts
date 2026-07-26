/**
 * Enterprise Digital Twin derivation — Sprint 33.0.
 * Pure client mirror over live-ops / City / Intelligence / Workflows.
 * No new AI Core / Dashboard / Workspace Engine / Graph Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { CITY_BUILDINGS, type CityBuildingId } from "@/enterprise-city/cityCatalog";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";

export type TwinNodeKind =
  | "department"
  | "ai"
  | "people"
  | "process"
  | "document"
  | "crm"
  | "ecosystem"
  | "integration";

export type TwinNode = {
  id: string;
  kind: TwinNodeKind;
  label: string;
  detail: string;
  heat: number; // 0–100
  route?: string;
  status: "idle" | "active" | "busy" | "risk" | "unused";
};

export type TwinEdge = {
  id: string;
  from: string;
  to: string;
  label: string;
};

export type HeatCell = {
  id: string;
  label: string;
  heat: number;
  tone: "hot" | "warm" | "cool" | "cold" | "risk";
  detail: string;
};

export type DecisionImpact = {
  objectId: string;
  objectLabel: string;
  change: string;
  effects: string[];
  risks: string[];
  recommendation: string;
};

export type TwinTimelineItem = {
  id: string;
  at: string;
  source: "workflow" | "ai" | "crm" | "knowledge" | "documents" | "system";
  title: string;
  detail: string;
};

export type TwinExecutive = {
  happening: string[];
  working: string[];
  risks: string[];
  growth: string[];
  aiRecommends: string[];
};

export type EnterpriseTwinBundle = {
  company: string;
  nodes: TwinNode[];
  graph: TwinEdge[];
  heatmap: HeatCell[];
  timeline: TwinTimelineItem[];
  executive: TwinExecutive;
  impacts: Record<string, DecisionImpact>;
};

const RELATIONSHIP_CHAIN: Array<{ id: string; label: string }> = [
  { id: "clients", label: "Клиенты" },
  { id: "crm", label: "CRM" },
  { id: "sales", label: "Продажи" },
  { id: "documents", label: "Документы" },
  { id: "finance", label: "Finance" },
  { id: "knowledge", label: "Knowledge" },
  { id: "ai_team", label: "AI Team" },
];

const ECOSYSTEMS = ["auto", "beauty", "cafe", "agro", "legal", "crypto", "drone"] as const;

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function heatTone(heat: number, risk = false): HeatCell["tone"] {
  if (risk || heat >= 85) return "risk";
  if (heat >= 70) return "hot";
  if (heat >= 45) return "warm";
  if (heat >= 20) return "cool";
  return "cold";
}

function statusFromHeat(heat: number, unused = false): TwinNode["status"] {
  if (unused || heat < 12) return "unused";
  if (heat >= 85) return "risk";
  if (heat >= 60) return "busy";
  if (heat >= 30) return "active";
  return "idle";
}

export function deriveEnterpriseTwin(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    company?: string;
    notifications?: AppNotification[];
    roleId?: string;
  } = {},
): EnterpriseTwinBundle {
  const notifications = opts.notifications || [];
  const intel = deriveIntelligence(snapshot, notifications);
  const company = opts.company || "Enterprise";

  const activityBlob = snapshot.activity.map((a) => `${a.title} ${a.moduleHint || ""}`).join(" ").toLowerCase();
  const activeSet = new Set(snapshot.activeModules.map((m) => m.toLowerCase()));

  const nodes: TwinNode[] = [];

  // Departments from city districts
  const districts = ["commerce", "ops", "people", "intel", "hub"] as const;
  for (const d of districts) {
    const buildings = CITY_BUILDINGS.filter((b) => b.district === d);
    const heat = clamp(
      buildings.reduce((s, b) => s + (activeSet.has(b.id) ? 25 : 8), 0) +
        (d === "commerce" && /crm|sales|client/.test(activityBlob) ? 30 : 0),
    );
    nodes.push({
      id: `dept_${d}`,
      kind: "department",
      label: d === "hub" ? "Headquarters" : d[0]!.toUpperCase() + d.slice(1),
      detail: `${buildings.length} модулей`,
      heat,
      route: "/enterprise-city",
      status: statusFromHeat(heat),
    });
  }

  // AI Team
  const aiHeat = clamp(
    20 + snapshot.aiOps.running.length * 22 + snapshot.aiOps.queue.length * 10 + snapshot.aiOps.errors.length * 15,
  );
  nodes.push({
    id: "ai_team",
    kind: "ai",
    label: "AI Team",
    detail: `${snapshot.aiOps.running.length} active · Q ${snapshot.aiOps.queue.length}`,
    heat: aiHeat,
    route: "/platform-builder/ai-team",
    status: snapshot.aiOps.errors.length ? "risk" : statusFromHeat(aiHeat),
  });

  // People / employees signal
  const peopleHeat = clamp(15 + notifications.filter((n) => n.kind === "task").length * 20 + (opts.roleId ? 20 : 10));
  nodes.push({
    id: "people",
    kind: "people",
    label: "Сотрудники",
    detail: "Identity / HR signals",
    heat: peopleHeat,
    route: "/identity/users",
    status: statusFromHeat(peopleHeat),
  });

  // Processes / workflows
  const processHeat = clamp(18 + BUSINESS_WORKFLOW_TEMPLATES.length * 4 + snapshot.aiOps.completed.length * 8);
  nodes.push({
    id: "processes",
    kind: "process",
    label: "Процессы",
    detail: `${BUSINESS_WORKFLOW_TEMPLATES.length} templates · ${snapshot.aiOps.completed.length} done`,
    heat: processHeat,
    route: "/platform-builder/workflow-center",
    status: statusFromHeat(processHeat),
  });

  // Clients (value-chain head) + Documents + Knowledge + CRM + Sales + Finance
  const crmHeatBase = /crm|client|сделк|клиент|sales/.test(activityBlob) ? 55 : 22;
  nodes.push({
    id: "clients",
    kind: "crm",
    label: "Клиенты",
    detail: "входящий поток CRM",
    heat: clamp(crmHeatBase + 8),
    route: "/workspace/crm",
    status: statusFromHeat(crmHeatBase),
  });
  nodes.push({
    id: "sales",
    kind: "process",
    label: "Продажи",
    detail: "sales pipeline",
    heat: clamp(crmHeatBase + 5),
    route: "/workspace/crm",
    status: statusFromHeat(crmHeatBase),
  });
  nodes.push({
    id: "finance",
    kind: "department",
    label: "Finance",
    detail: "finance signals",
    heat: clamp(20 + (/finance|оплат|invoice/.test(activityBlob) ? 40 : 0)),
    route: "/workspace/finance",
    status: statusFromHeat(20 + (/finance|оплат|invoice/.test(activityBlob) ? 40 : 0)),
  });

  for (const [id, kind, label, route, tokens] of [
    ["documents", "document", "Документы", "/workspace/docs", /doc|документ/],
    ["knowledge", "document", "Knowledge", "/platform-builder/knowledge", /knowledge|баз/],
    ["crm", "crm", "CRM", "/workspace/crm", /crm|client|сделк|клиент/],
  ] as const) {
    const hit = tokens.test(activityBlob) || activeSet.has(id);
    const health = snapshot.health.find((h) => h.id === id || (id === "documents" && h.id === "knowledge"));
    const heat = clamp((hit ? 55 : 18) + (health && !health.ok ? 35 : 10) + (id === "crm" ? 15 : 0));
    nodes.push({
      id,
      kind,
      label,
      detail: health ? (health.ok ? "healthy" : health.detail) : "mirrored",
      heat,
      route,
      status: health && !health.ok ? "risk" : statusFromHeat(heat, !hit && heat < 20),
    });
  }

  // Ecosystems
  for (const eco of ECOSYSTEMS) {
    const hit = activeSet.has(eco) || activityBlob.includes(eco);
    const heat = hit ? 48 + (eco === "auto" || eco === "beauty" ? 12 : 0) : 8;
    nodes.push({
      id: `eco_${eco}`,
      kind: "ecosystem",
      label: eco === "crypto" ? "Bidex" : eco[0]!.toUpperCase() + eco.slice(1),
      detail: hit ? "сигналы активности" : "idle ecosystem",
      heat,
      route: `/workspace/${eco}`,
      status: statusFromHeat(heat, !hit),
    });
  }

  // Integrations
  for (const h of snapshot.health.slice(0, 6)) {
    const heat = h.ok ? 35 : 90;
    nodes.push({
      id: `int_${h.id}`,
      kind: "integration",
      label: h.label,
      detail: h.detail || (h.ok ? "ok" : "check"),
      heat,
      route: "/platform-builder/mission-control",
      status: h.ok ? "active" : "risk",
    });
  }

  const graph: TwinEdge[] = [];
  for (let i = 0; i < RELATIONSHIP_CHAIN.length - 1; i++) {
    const a = RELATIONSHIP_CHAIN[i]!;
    const b = RELATIONSHIP_CHAIN[i + 1]!;
    graph.push({ id: `e_${a.id}_${b.id}`, from: a.id, to: b.id, label: `${a.label} → ${b.label}` });
  }

  const heatmap: HeatCell[] = nodes
    .filter((n) => n.kind === "department" || n.kind === "process" || n.kind === "ai" || n.kind === "crm")
    .map((n) => ({
      id: n.id,
      label: n.label,
      heat: n.heat,
      tone: heatTone(n.heat, n.status === "risk"),
      detail:
        n.status === "unused"
          ? "Неиспользуемый / низкая активность"
          : n.status === "risk"
            ? "Узкое место / перегруз"
            : n.heat >= 70
              ? "Самый активный контур"
              : "Стабильная нагрузка",
    }))
    .sort((a, b) => b.heat - a.heat);

  const timeline: TwinTimelineItem[] = [];
  for (const a of snapshot.activity.slice(0, 8)) {
    let source: TwinTimelineItem["source"] = "system";
    if (a.kind === "ai" || a.kind === "automation") source = "ai";
    else if (a.kind === "crm" || a.kind === "client" || a.kind === "deal") source = "crm";
    else if (a.kind === "document") source = "documents";
    else if (/knowledge/i.test(a.title)) source = "knowledge";
    else if (a.kind === "task") source = "workflow";
    timeline.push({ id: a.id, at: a.at, source, title: a.title, detail: a.detail || a.source });
  }
  for (const done of snapshot.aiOps.completed.slice(0, 3)) {
    timeline.push({
      id: `wf_${done}`,
      at: snapshot.updatedAt,
      source: "workflow",
      title: `Workflow · ${done}`,
      detail: "AI automation completed",
    });
  }
  for (const r of snapshot.aiOps.recent.slice(0, 2)) {
    timeline.push({
      id: `ai_${r}`,
      at: snapshot.updatedAt,
      source: "ai",
      title: r,
      detail: "AI Team activity",
    });
  }

  const executive: TwinExecutive = {
    happening: intel.brief.bullets.slice(0, 3),
    working: [
      snapshot.mcOk ? "Mission Control в норме" : "Mission Control требует проверки",
      `${snapshot.health.filter((h) => h.ok).length}/${snapshot.health.length || 1} сервисов healthy`,
      snapshot.aiOps.completed[0] ? `AI завершил: ${snapshot.aiOps.completed[0]}` : "AI idle",
    ],
    risks: intel.insights.filter((i) => i.category === "risk" || i.category === "anomaly").slice(0, 3).map((i) => i.title),
    growth: intel.insights.filter((i) => i.category === "opportunity" || i.category === "achievement").slice(0, 3).map((i) => i.title),
    aiRecommends: intel.decision.decideToday.slice(0, 3).map((p) => p.title),
  };

  const impacts: Record<string, DecisionImpact> = {};
  for (const n of nodes) {
    impacts[n.id] = buildImpact(n);
  }
  // relationship chain aliases
  for (const step of RELATIONSHIP_CHAIN) {
    const node = nodes.find((n) => n.id === step.id) || nodes.find((n) => n.label === step.label);
    if (node) impacts[step.id] = buildImpact({ ...node, id: step.id, label: step.label });
  }

  return { company, nodes, graph, heatmap, timeline: timeline.slice(0, 16), executive, impacts };
}

function buildImpact(n: TwinNode): DecisionImpact {
  const change =
    n.kind === "ai"
      ? "Изменить состав / приоритет AI Team"
      : n.kind === "process"
        ? "Изменить Workflow / процесс"
        : n.kind === "people"
          ? "Изменить роль сотрудника"
          : "Изменить конфигурацию модуля";

  const effects = [
    `Нагрузка «${n.label}» сместится (heat ${n.heat}→${clamp(n.heat + (n.heat > 50 ? -15 : 20))})`,
    n.kind === "crm" || n.id === "crm" ? "Продажи и Finance получат новый поток сигналов" : "Связанные узлы пересчитают приоритеты",
    n.kind === "ai" ? "Concierge перераспределит задачи specialists" : "AI Team обновит рекомендации",
  ];

  const risks =
    n.status === "risk" || n.heat >= 80
      ? ["Возможен временный backlog", "Нужен контроль Mission Control"]
      : n.status === "unused"
        ? ["Модуль может остаться неиспользуемым без onboarding"]
        : ["Минимальный операционный риск при поэтапном rollout"];

  return {
    objectId: n.id,
    objectLabel: n.label,
    change,
    effects,
    risks,
    recommendation:
      n.status === "risk"
        ? "Сначала снять перегруз (очередь / ошибки), затем менять конфигурацию"
        : n.status === "unused"
          ? "Подключить через Marketplace / Builder Studio"
          : "Применить изменение через Workflow Center или AI Team Builder",
  };
}

export { RELATIONSHIP_CHAIN };
