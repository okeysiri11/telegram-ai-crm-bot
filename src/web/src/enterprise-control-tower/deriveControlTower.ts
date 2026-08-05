/**
 * Enterprise Control Tower derivation — Sprint 33.6.
 * Composes Mission Control / Twin / Runtime / EI / Predictive / Autonomy / Integrations / Fabric.
 * No new Dashboard Engine / AI Core / Runtime Engine / Store.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveAutonomy } from "@/autonomous-enterprise/deriveAutonomy";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveEnterpriseTwin } from "@/enterprise-twin/deriveTwin";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";

export type GlobalOverviewItem = {
  id: string;
  label: string;
  value: string;
  detail: string;
  route: string;
  tone?: "ok" | "warn" | "risk";
};

export type OperationsWallItem = {
  id: string;
  kind: "runtime" | "alert" | "predictive" | "approval" | "failed" | "critical";
  title: string;
  detail: string;
  route?: string;
};

export type CockpitKpi = {
  id: string;
  label: string;
  value: string;
  delta: string;
  tone: "up" | "down" | "flat" | "risk";
  route?: string;
};

export type EcosystemStatus = {
  id: string;
  label: string;
  route: string;
  ok: boolean;
  detail: string;
};

export type IncidentItem = {
  id: string;
  severity: "error" | "warning" | "degraded" | "overload" | "info";
  title: string;
  detail: string;
  route?: string;
};

export type CommandAction = {
  id: string;
  label: string;
  route: string;
};

export type ControlTowerBundle = {
  overview: GlobalOverviewItem[];
  operations: OperationsWallItem[];
  cockpit: CockpitKpi[];
  ecosystems: EcosystemStatus[];
  incidents: IncidentItem[];
  commands: CommandAction[];
};

const ECOSYSTEMS: Array<{ id: string; label: string; route: string; tokens: RegExp }> = [
  { id: "beauty", label: "Beauty", route: "/workspace/beauty", tokens: /beauty/ },
  { id: "legal", label: "Legal", route: "/workspace/legal", tokens: /legal/ },
  { id: "cafe", label: "Cafe", route: "/workspace/cafe", tokens: /cafe/ },
  { id: "agro", label: "Agriculture", route: "/workspace/agro", tokens: /agro|agriculture/ },
  { id: "auto", label: "Automotive", route: "/workspace/auto", tokens: /auto|automotive/ },
  { id: "drone", label: "Drone", route: "/workspace/drone", tokens: /drone/ },
  { id: "crypto", label: "Bidex", route: "/workspace/crypto", tokens: /crypto|bidex/ },
];

export const CONTROL_TOWER_COMMANDS: CommandAction[] = [
  { id: "cmd_ws", label: "Открыть Workspace", route: "/workspace" },
  { id: "cmd_twin", label: "Открыть Digital Twin", route: "/platform-builder/digital-twin" },
  { id: "cmd_runtime", label: "Перейти в Runtime", route: "/platform-builder/runtime" },
  { id: "cmd_approval", label: "Approval Center", route: "/platform-builder/autonomy" },
  { id: "cmd_builder", label: "AI Builder", route: "/platform-builder/builder-studio" },
  { id: "cmd_mkt", label: "Marketplace", route: "/platform-builder/solution-hub" },
];

export function deriveControlTower(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    company?: string;
    notifications?: AppNotification[];
    roleId?: string;
  } = {},
): ControlTowerBundle {
  const notifications = opts.notifications || [];
  const company = opts.company || "Enterprise";
  const runtime = deriveRuntime(snapshot, notifications);
  const pred = derivePredictive(snapshot, notifications);
  const auto = deriveAutonomy(snapshot, { roleId: opts.roleId, notifications });
  const intHub = deriveIntegrationHub(snapshot);
  const fabric = deriveDataFabric(snapshot, { company, notifications, roleId: opts.roleId });
  const intel = deriveIntelligence(snapshot, notifications);
  const twin = deriveEnterpriseTwin(snapshot, { company, notifications, roleId: opts.roleId });

  const healthy = snapshot.health.filter((h) => h.ok).length;
  const healthTotal = snapshot.health.length || 1;

  const overview: GlobalOverviewItem[] = [
    {
      id: "orgs",
      label: "Organizations",
      value: "1+",
      detail: company,
      route: "/identity/organizations",
      tone: "ok",
    },
    {
      id: "workspaces",
      label: "Workspaces",
      value: String(Math.max(1, twin.nodes.filter((n) => n.kind === "department").length)),
      detail: "active contexts",
      route: "/workspace",
      tone: "ok",
    },
    {
      id: "ai_teams",
      label: "AI Teams",
      value: String(Math.max(1, snapshot.aiOps.running.length || 1)),
      detail: `${snapshot.aiOps.running.length} running`,
      route: "/platform-builder/ai-team",
      tone: snapshot.aiOps.errors.length ? "risk" : "ok",
    },
    {
      id: "runtime",
      label: "Active Runtime",
      value: String(runtime.counts.active),
      detail: `Q ${runtime.health.queueSize}`,
      route: "/platform-builder/runtime",
      tone: runtime.health.needsIntervention ? "warn" : "ok",
    },
    {
      id: "integrations",
      label: "Integrations",
      value: String(intHub.dashboard.active),
      detail: intHub.dashboard.statusSummary,
      route: "/platform-builder/integrations",
      tone: intHub.dashboard.errors ? "risk" : intHub.dashboard.needsSetup ? "warn" : "ok",
    },
    {
      id: "twins",
      label: "Digital Twins",
      value: "1",
      detail: `${twin.nodes.length} nodes`,
      route: "/platform-builder/digital-twin",
      tone: "ok",
    },
    {
      id: "knowledge",
      label: "Knowledge Bases",
      value: intel.knowledgeAware ? "1+" : "0–1",
      detail: intel.knowledgeAware ? "KB aware" : "weak signals",
      route: "/platform-builder/knowledge",
      tone: intel.knowledgeAware ? "ok" : "warn",
    },
  ];

  const operations: OperationsWallItem[] = [
    {
      id: "op_runtime",
      kind: "runtime",
      title: `Runtime · ${runtime.counts.active} active`,
      detail: `${runtime.monitor.currentStep} → ${runtime.monitor.nextStep}`,
      route: "/platform-builder/runtime",
    },
    ...snapshot.health
      .filter((h) => !h.ok)
      .slice(0, 2)
      .map((h) => ({
        id: `op_alert_${h.id}`,
        kind: "alert" as const,
        title: `Alert · ${h.label}`,
        detail: h.detail || "check",
        route: "/platform-builder/mission-control",
      })),
    ...pred.risks
      .filter((r) => r.severity !== "low")
      .slice(0, 2)
      .map((r) => ({
        id: `op_pred_${r.id}`,
        kind: "predictive" as const,
        title: `Predictive · ${r.title}`,
        detail: r.detail,
        route: r.route || "/platform-builder/predictive",
      })),
    ...auto.approvals
      .filter((a) => a.status === "pending")
      .slice(0, 3)
      .map((a) => ({
        id: `op_ap_${a.id}`,
        kind: "approval" as const,
        title: `Pending · ${a.title}`,
        detail: `${a.risk} · ${a.category}`,
        route: "/platform-builder/autonomy",
      })),
    ...runtime.jobs
      .filter((j) => j.state === "failed")
      .slice(0, 2)
      .map((j) => ({
        id: `op_fail_${j.id}`,
        kind: "failed" as const,
        title: `Failed · ${j.title}`,
        detail: j.currentStep,
        route: "/platform-builder/runtime",
      })),
    ...auto.twin.criticalDecisions.slice(0, 2).map((c, i) => ({
      id: `op_crit_${i}`,
      kind: "critical" as const,
      title: `Critical · ${c}`,
      detail: "Autonomy / Predictive",
      route: "/platform-builder/autonomy",
    })),
  ];

  const kpiIndex = pred.forecasts.find((f) => f.id === "kpi");
  const aiLoad = pred.forecasts.find((f) => f.id === "ai_load");
  const wf = pred.forecasts.find((f) => f.id === "workflows");
  const clients = pred.forecasts.find((f) => f.id === "clients");

  const cockpit: CockpitKpi[] = [
    {
      id: "revenue",
      label: "Revenue",
      value: `${kpiIndex?.forecast ?? 60}`,
      delta: `${(kpiIndex?.deltaPct ?? 0) >= 0 ? "+" : ""}${kpiIndex?.deltaPct ?? 0}%`,
      tone: (kpiIndex?.tone as CockpitKpi["tone"]) || "flat",
      route: "/workspace/finance",
    },
    {
      id: "sales",
      label: "Sales",
      value: `${clients?.forecast ?? 40}`,
      delta: `${(clients?.deltaPct ?? 0) >= 0 ? "+" : ""}${clients?.deltaPct ?? 0}%`,
      tone: (clients?.tone as CockpitKpi["tone"]) || "flat",
      route: "/workspace/crm",
    },
    {
      id: "ops",
      label: "Operations",
      value: `${runtime.counts.active}/${runtime.health.queueSize}`,
      delta: runtime.health.needsIntervention ? "attention" : "stable",
      tone: runtime.health.needsIntervention ? "risk" : "up",
      route: "/platform-builder/runtime",
    },
    {
      id: "ai_prod",
      label: "AI Productivity",
      value: `${aiLoad?.current ?? 0}→${aiLoad?.forecast ?? 0}%`,
      delta: `${(aiLoad?.deltaPct ?? 0) >= 0 ? "+" : ""}${aiLoad?.deltaPct ?? 0}%`,
      tone: (aiLoad?.tone as CockpitKpi["tone"]) || "flat",
      route: "/platform-builder/ai-team",
    },
    {
      id: "automation",
      label: "Automation Rate",
      value: `${wf?.forecast ?? 40}%`,
      delta: `${BUSINESS_WORKFLOW_TEMPLATES.length} templates`,
      tone: (wf?.tone as CockpitKpi["tone"]) || "up",
      route: "/platform-builder/workflow-center",
    },
    {
      id: "team",
      label: "Team Health",
      value: auto.dashboard.levelTitle,
      delta: `L${auto.dashboard.level}`,
      tone: auto.dashboard.needsIntervention ? "risk" : "up",
      route: "/platform-builder/autonomy",
    },
    {
      id: "system",
      label: "System Health",
      value: `${healthy}/${healthTotal}`,
      delta: snapshot.mcOk ? "MC ok" : "MC check",
      tone: healthy === healthTotal ? "up" : "risk",
      route: "/platform-builder/mission-control",
    },
  ];

  const activeBlob = snapshot.activeModules.join(" ").toLowerCase();
  const ecosystems: EcosystemStatus[] = ECOSYSTEMS.map((e) => {
    const hit = e.tokens.test(activeBlob) || snapshot.activity.some((a) => e.tokens.test(`${a.title} ${a.moduleHint || ""}`.toLowerCase()));
    return {
      id: e.id,
      label: e.label,
      route: e.route,
      ok: hit || snapshot.mcOk,
      detail: hit ? "signals active" : "idle / ready",
    };
  });

  const incidents: IncidentItem[] = [];
  for (const h of snapshot.health.filter((x) => !x.ok)) {
    incidents.push({
      id: `inc_err_${h.id}`,
      severity: "error",
      title: h.label,
      detail: h.detail || "service check",
      route: "/platform-builder/mission-control",
    });
  }
  for (const r of pred.risks.filter((x) => x.severity === "high").slice(0, 3)) {
    incidents.push({
      id: `inc_w_${r.id}`,
      severity: r.kind === "overload" ? "overload" : "warning",
      title: r.title,
      detail: r.detail,
      route: r.route,
    });
  }
  if (fabric.executive.problemLinks > 0) {
    incidents.push({
      id: "inc_deg_fabric",
      severity: "degraded",
      title: "Data Fabric problem links",
      detail: `${fabric.executive.problemLinks} проблемных связей`,
      route: "/platform-builder/data-fabric",
    });
  }
  if (runtime.health.queueSize >= 3 || (aiLoad?.forecast ?? 0) >= 80) {
    incidents.push({
      id: "inc_overload",
      severity: "overload",
      title: "Runtime / AI overload risk",
      detail: `Queue ${runtime.health.queueSize} · AI forecast ${aiLoad?.forecast ?? "—"}%`,
      route: "/platform-builder/runtime",
    });
  }
  for (const p of intel.decision.decideToday.slice(0, 2)) {
    incidents.push({
      id: `inc_ai_${p.id}`,
      severity: "info",
      title: `AI · ${p.title}`,
      detail: p.detail,
      route: p.route || "/dashboard",
    });
  }
  if (!incidents.length) {
    incidents.push({
      id: "inc_calm",
      severity: "info",
      title: "No critical incidents",
      detail: "System signals stable",
      route: "/platform-builder/mission-control",
    });
  }

  return {
    overview,
    operations: operations.slice(0, 14),
    cockpit,
    ecosystems,
    incidents,
    commands: CONTROL_TOWER_COMMANDS,
  };
}
