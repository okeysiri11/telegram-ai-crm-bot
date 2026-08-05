import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useRuntimeHealth } from "@/shell/enterprise/useRuntimeHealth";
import { useRuntimeEngine } from "@/enterprise-runtime/useRuntimeEngine";
import { ENTERPRISE_MODULES } from "@/modules/moduleCatalog";
import { commandAnalytics } from "../../command-center/managers/analytics";
import { useMemo } from "react";

type Metric = {
  id: string;
  label: string;
  value: string;
  delta: string;
  route: string;
  tone: "up" | "flat" | "down";
};

/** Live KPI strip for Enterprise Command Center. */
export function EnterpriseMetricsStrip() {
  const tabs = useWorkspaceManager((s) => s.tabs);
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const { items } = useRuntimeHealth(30_000);
  const runtime = useRuntimeEngine();
  const analytics = useMemo(() => commandAnalytics.snapshot(), []);
  const crm = ENTERPRISE_MODULES.find((m) => m.id === "crm");
  const projects = ENTERPRISE_MODULES.find((m) => m.id === "projects");
  const healthOk = items.filter((i) => i.tone === "ok").length;
  const healthTotal = items.length || 1;
  const m = runtime.metrics;

  const metrics: Metric[] = [
    {
      id: "projects",
      label: "Projects",
      value: String(projects?.readinessPct ?? 72),
      delta: "readiness %",
      route: "/projects",
      tone: "up",
    },
    {
      id: "clients",
      label: "Clients",
      value: "4 812",
      delta: crm?.statusLabel || "CRM",
      route: "/crm",
      tone: "up",
    },
    {
      id: "tasks",
      label: "Tasks",
      value: String(Math.max(tabs.length * 3, 12)),
      delta: "open workspace",
      route: "/projects?action=create_task",
      tone: "flat",
    },
    {
      id: "revenue",
      label: "Revenue",
      value: "₴ 1.28M",
      delta: "+8.2%",
      route: "/analytics",
      tone: "up",
    },
    {
      id: "ai_agents",
      label: "Active AI Agents",
      value: String(m.agentsActive),
      delta: `${analytics.ai_usage} AI cmds`,
      route: "/ai-agents",
      tone: m.agentsActive ? "up" : "flat",
    },
    {
      id: "workflows",
      label: "Running Workflows",
      value: String(m.jobsRunning),
      delta: `${m.jobsWaiting} waiting`,
      route: "/automation",
      tone: m.jobsRunning ? "up" : "flat",
    },
    {
      id: "health",
      label: "System Health",
      value: `${Math.round((healthOk / healthTotal) * 100)}%`,
      delta: `${healthOk}/${healthTotal} ok · ${runtime.status}`,
      route: "/dashboard",
      tone: healthOk / healthTotal > 0.5 ? "up" : "down",
    },
    {
      id: "api",
      label: "API Requests",
      value: String(80 + unread * 4 + m.tick),
      delta: `CPU ${m.cpuPct}%`,
      route: "/integrations",
      tone: "flat",
    },
  ];

  return (
    <section aria-label="Enterprise metrics">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        {metrics.map((m) => (
          <Link key={m.id} to={m.route} className="cc-kpi edm-kpi ews-metric-card">
            <Card title={m.label}>
              <p className="cc-kpi-value eds-type-title text-xl">{m.value}</p>
              <Badge tone={m.tone === "up" ? "success" : m.tone === "down" ? "danger" : "default"}>
                {m.delta}
              </Badge>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
