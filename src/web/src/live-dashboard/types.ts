/**
 * Sprint 27.6 — Live Dashboard types & persistence keys.
 */

export const LIVE_DASHBOARD_KEY = "ews_live_dashboard_v1";

export type DashboardProfileId =
  | "ceo"
  | "manager"
  | "sales"
  | "developer"
  | "finance"
  | "administrator";

export type LiveWidgetId =
  | "runtime_cpu"
  | "runtime_memory"
  | "runtime_ai"
  | "runtime_providers"
  | "runtime_mcp"
  | "runtime_agents"
  | "runtime_jobs"
  | "runtime_queue"
  | "runtime_notifications"
  | "runtime_sessions"
  | "enterprise_health"
  | "enterprise_ai"
  | "enterprise_activity"
  | "enterprise_notifications"
  | "enterprise_tasks"
  | "enterprise_projects"
  | "enterprise_crm"
  | "enterprise_finance"
  | "enterprise_knowledge"
  | "enterprise_calendar";

export type LiveWidgetPlacement = {
  id: LiveWidgetId;
  order: number;
  /** Grid column span 1–4 */
  colSpan: 1 | 2 | 3 | 4;
  collapsed: boolean;
  pinned: boolean;
};

export type LiveDashboardLayout = {
  id: string;
  name: string;
  widgets: LiveWidgetPlacement[];
};

export type LiveDashboardState = {
  version: 1;
  profileId: DashboardProfileId;
  activeLayoutId: string;
  layouts: LiveDashboardLayout[];
  fullscreenId: LiveWidgetId | null;
  activityFilter: string;
  updatedAt: string;
};
