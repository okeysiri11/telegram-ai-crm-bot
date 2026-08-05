import type { DashboardProfileId, LiveDashboardLayout, LiveWidgetId, LiveWidgetPlacement } from "./types";

export type LiveWidgetDef = {
  id: LiveWidgetId;
  title: string;
  group: "runtime" | "enterprise";
  defaultSpan: 1 | 2 | 3 | 4;
};

export const LIVE_WIDGET_CATALOG: LiveWidgetDef[] = [
  { id: "runtime_cpu", title: "CPU Usage", group: "runtime", defaultSpan: 1 },
  { id: "runtime_memory", title: "Memory Usage", group: "runtime", defaultSpan: 1 },
  { id: "runtime_ai", title: "AI Runtime", group: "runtime", defaultSpan: 1 },
  { id: "runtime_providers", title: "Connected Providers", group: "runtime", defaultSpan: 1 },
  { id: "runtime_mcp", title: "MCP", group: "runtime", defaultSpan: 1 },
  { id: "runtime_agents", title: "Active Agents", group: "runtime", defaultSpan: 1 },
  { id: "runtime_jobs", title: "Background Jobs", group: "runtime", defaultSpan: 1 },
  { id: "runtime_queue", title: "Event Queue", group: "runtime", defaultSpan: 1 },
  { id: "runtime_notifications", title: "Notifications", group: "runtime", defaultSpan: 1 },
  { id: "runtime_sessions", title: "Active Sessions", group: "runtime", defaultSpan: 1 },
  { id: "enterprise_health", title: "System Health", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_ai", title: "AI Status", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_activity", title: "Recent Activity", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_notifications", title: "Notifications", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_tasks", title: "Tasks", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_projects", title: "Projects", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_crm", title: "CRM Summary", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_finance", title: "Finance Summary", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_knowledge", title: "Knowledge Base", group: "enterprise", defaultSpan: 2 },
  { id: "enterprise_calendar", title: "Calendar", group: "enterprise", defaultSpan: 2 },
];

export function placementFromIds(ids: LiveWidgetId[]): LiveWidgetPlacement[] {
  return ids.map((id, order) => {
    const def = LIVE_WIDGET_CATALOG.find((w) => w.id === id);
    return {
      id,
      order,
      colSpan: def?.defaultSpan || 1,
      collapsed: false,
      pinned: false,
    };
  });
}

export const DASHBOARD_PROFILES: Record<
  DashboardProfileId,
  { label: string; description: string; widgetIds: LiveWidgetId[] }
> = {
  ceo: {
    label: "CEO",
    description: "Executive pulse — health, finance, CRM, AI",
    widgetIds: [
      "enterprise_health",
      "enterprise_finance",
      "enterprise_crm",
      "enterprise_ai",
      "runtime_agents",
      "runtime_notifications",
      "enterprise_activity",
      "enterprise_projects",
    ],
  },
  manager: {
    label: "Manager",
    description: "Team delivery — tasks, projects, activity",
    widgetIds: [
      "enterprise_tasks",
      "enterprise_projects",
      "enterprise_activity",
      "runtime_jobs",
      "runtime_notifications",
      "enterprise_calendar",
      "enterprise_health",
      "enterprise_ai",
    ],
  },
  sales: {
    label: "Sales",
    description: "Pipeline focus — CRM, calendar, notifications",
    widgetIds: [
      "enterprise_crm",
      "enterprise_calendar",
      "enterprise_tasks",
      "enterprise_notifications",
      "enterprise_activity",
      "runtime_notifications",
      "enterprise_finance",
      "enterprise_ai",
    ],
  },
  developer: {
    label: "Developer",
    description: "Runtime ops — CPU, memory, MCP, queue, agents",
    widgetIds: [
      "runtime_cpu",
      "runtime_memory",
      "runtime_ai",
      "runtime_providers",
      "runtime_mcp",
      "runtime_agents",
      "runtime_jobs",
      "runtime_queue",
      "runtime_sessions",
      "enterprise_health",
    ],
  },
  finance: {
    label: "Finance",
    description: "Commercial pulse — finance, CRM, projects",
    widgetIds: [
      "enterprise_finance",
      "enterprise_crm",
      "enterprise_projects",
      "enterprise_health",
      "enterprise_notifications",
      "enterprise_activity",
      "runtime_jobs",
      "enterprise_calendar",
    ],
  },
  administrator: {
    label: "Administrator",
    description: "Full platform surface",
    widgetIds: LIVE_WIDGET_CATALOG.map((w) => w.id),
  },
};

export function layoutForProfile(profileId: DashboardProfileId): LiveDashboardLayout {
  const profile = DASHBOARD_PROFILES[profileId];
  return {
    id: `layout_${profileId}`,
    name: `${profile.label} layout`,
    widgets: placementFromIds(profile.widgetIds),
  };
}

export function bootstrapLayouts(): LiveDashboardLayout[] {
  return (Object.keys(DASHBOARD_PROFILES) as DashboardProfileId[]).map((id) => layoutForProfile(id));
}

export function widgetTitle(id: LiveWidgetId): string {
  return LIVE_WIDGET_CATALOG.find((w) => w.id === id)?.title || id;
}
