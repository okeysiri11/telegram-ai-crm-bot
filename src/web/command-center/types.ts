export type CommandKind =
  | "navigate"
  | "search"
  | "create"
  | "open"
  | "ai_execute"
  | "run_workflow"
  | "run_automation"
  | "open_module"
  | "open_dashboard"
  | "open_report"
  | "open_settings"
  | "mass_update";

export type OmniboxSource =
  | "crm"
  | "erp"
  | "knowledge"
  | "documents"
  | "projects"
  | "tasks"
  | "users"
  | "organizations"
  | "ai_agents"
  | "workflows"
  | "marketplace"
  | "applications"
  | "verticals"
  | "dashboards"
  | "reports"
  | "settings"
  | "modules"
  | "commands"
  | "pages"
  | "routes"
  | "widgets";

export type CommandItem = {
  id: string;
  kind: CommandKind;
  action: string;
  label: string;
  route?: string;
  keywords: string[];
  permission?: string;
  shortcut?: string;
};

export type SearchHit = {
  id: string;
  title: string;
  type: OmniboxSource | string;
  route?: string;
  score: number;
  kind?: string;
  action?: string;
  signals?: Record<string, number | string | boolean>;
};

export type ContextState = {
  workspace: string;
  organization: string;
  openedPages: string[];
  openedDocuments: string[];
  recentAiConversations: { utterance: string; intent: string }[];
  currentDashboard: string | null;
  currentModule: string | null;
  selectedCustomer: string | null;
  selectedProject: string | null;
  activeWorkflow: string | null;
  role: string;
  department: string;
  permissions: string[];
};

export type ProductivitySnapshot = {
  widgets: string[];
  recentActivity: unknown[];
  favorites: string[];
  recentSearches: { query?: string }[];
  mostUsedCommands: { id: string; count: number }[];
  recentlyOpened: string[];
  pinnedObjects: string[];
};

export const COMMAND_CENTER_VERSION = "9.2.0";
export const COMMAND_CENTER_PATH = "src/web/command-center";
export const COMMAND_CENTER_API = "/api/enterprise-command/v1";

export const HOTKEYS = [
  "Ctrl+K",
  "Cmd+K",
  "Ctrl+P",
  "Ctrl+Shift+P",
  "Ctrl+Space",
  "Ctrl+/",
  "Esc",
  "Enter",
  "ArrowUp",
  "ArrowDown",
  "Tab",
  "Shift+Tab",
] as const;
