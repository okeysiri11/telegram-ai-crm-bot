import {
  favoritesManager,
  recentActivity,
  widgetManager,
  workspaceManager,
} from "../managers";

export function buildWorkspaceDashboard() {
  const ws = workspaceManager.active();
  const widgets = widgetManager.list();
  return {
    workspace: ws,
    sections: {
      aiAssistant: widgets.find((w) => w.kind === "ai_assistant"),
      todaysTasks: widgets.find((w) => w.kind === "tasks"),
      calendar: widgets.find((w) => w.kind === "calendar"),
      notifications: widgets.find((w) => w.kind === "notifications"),
      activeWorkflows: widgets.find((w) => w.kind === "workflow_queue"),
      kpiOverview: widgets.find((w) => w.kind === "kpi_cards"),
      teamActivity: recentActivity.list().slice(0, 5),
      reports: favoritesManager.list().filter((f) => f.kind === "report"),
      marketplace: widgets.find((w) => w.kind === "marketplace"),
      systemStatus: widgets.find((w) => w.kind === "system_health"),
    },
  };
}
