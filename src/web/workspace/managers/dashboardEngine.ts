import type { DashboardKind, DashboardRecord } from "../types";

const dashboards: DashboardRecord[] = [
  { dashboardId: "dash_personal", name: "Personal Dashboard", kind: "personal", workspaceId: "ws_personal", widgetIds: ["w_kpi", "w_tasks", "w_ai", "w_calendar", "w_notif", "w_health"] },
  { dashboardId: "dash_exec", name: "Executive Dashboard", kind: "executive", workspaceId: "ws_org", widgetIds: ["w_kpi", "w_charts", "w_finance", "w_crm"] },
  { dashboardId: "dash_ops", name: "Operations Dashboard", kind: "operations", workspaceId: "ws_team_ops", widgetIds: ["w_workflow", "w_tasks", "w_erp", "w_health"] },
  { dashboardId: "dash_fin", name: "Finance Dashboard", kind: "finance", workspaceId: "ws_dept_finance", widgetIds: ["w_finance", "w_charts", "w_kpi"] },
  { dashboardId: "dash_ai", name: "AI Dashboard", kind: "ai", workspaceId: "ws_personal", widgetIds: ["w_ai", "w_workflow", "w_analytics"] },
  { dashboardId: "dash_analytics", name: "Analytics Dashboard", kind: "analytics", workspaceId: "ws_project_web", widgetIds: ["w_analytics", "w_charts", "w_kpi"] },
];

export const dashboardEngine = {
  list(): DashboardRecord[] {
    return [...dashboards];
  },
  byWorkspace(workspaceId: string) {
    return dashboards.filter((d) => d.workspaceId === workspaceId);
  },
  kinds(): DashboardKind[] {
    return ["personal", "executive", "operations", "finance", "ai", "analytics", "custom"];
  },
  createCustom(name: string, workspaceId: string, widgetIds: string[]): DashboardRecord {
    const dash: DashboardRecord = {
      dashboardId: `dash_custom_${Math.random().toString(36).slice(2, 8)}`,
      name,
      kind: "custom",
      workspaceId,
      widgetIds,
    };
    dashboards.push(dash);
    return dash;
  },
};
