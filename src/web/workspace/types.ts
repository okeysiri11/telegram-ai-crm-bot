export type WorkspaceKind = "personal" | "team" | "department" | "organization" | "project";

export type WorkspaceRecord = {
  workspaceId: string;
  name: string;
  owner: string;
  organization: string;
  kind: WorkspaceKind;
  activeModules: string[];
  layout: string;
  permissions: string[];
  theme: "light" | "dark" | "corporate" | "system";
  status: "active" | "archived";
};

export type DashboardKind =
  | "personal"
  | "executive"
  | "operations"
  | "finance"
  | "ai"
  | "analytics"
  | "custom";

export type DashboardRecord = {
  dashboardId: string;
  name: string;
  kind: DashboardKind;
  workspaceId: string;
  widgetIds: string[];
};

export type WidgetKind =
  | "kpi_cards"
  | "charts"
  | "ai_assistant"
  | "tasks"
  | "calendar"
  | "notifications"
  | "workflow_queue"
  | "crm_summary"
  | "erp_summary"
  | "finance_summary"
  | "hr_summary"
  | "analytics"
  | "marketplace"
  | "system_health";

export type WidgetInstance = {
  widgetId: string;
  kind: WidgetKind;
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
  config: Record<string, string | number | boolean>;
  realtime: boolean;
};

export type LayoutSnapshot = {
  layoutId: string;
  workspaceId: string;
  widgets: WidgetInstance[];
  multiMonitorReady: boolean;
};

export type QuickActionId =
  | "create_task"
  | "create_workflow"
  | "open_ai_assistant"
  | "start_chat"
  | "new_crm_record"
  | "upload_document"
  | "launch_automation";

export type FavoriteKind = "module" | "dashboard" | "report" | "ai_agent" | "document";

export type FavoriteItem = {
  id: string;
  kind: FavoriteKind;
  label: string;
  path: string;
};

export type ActivityItem = {
  id: string;
  kind: "document" | "task" | "workflow" | "ai" | "security" | "report";
  summary: string;
  at: string;
};

export type SearchCategory =
  | "modules"
  | "users"
  | "organizations"
  | "documents"
  | "workflows"
  | "ai_agents"
  | "reports"
  | "tasks";

export type SearchHit = {
  id: string;
  category: SearchCategory;
  label: string;
  path: string;
};

export type Personalization = {
  dashboardLayout: string;
  widgets: string[];
  theme: WorkspaceRecord["theme"];
  language: "en" | "ru" | "uk";
  timeZone: string;
  homePage: string;
  defaultWorkspace: string;
  notificationPreferences: { email: boolean; push: boolean; inApp: boolean };
};
