export type NavSurface =
  | "main"
  | "sidebar"
  | "top"
  | "context"
  | "module"
  | "workspace";

export type MenuItemStatus = "active" | "beta" | "disabled";

export type MenuItem = {
  id: string;
  name: string;
  icon: string;
  route: string;
  module: string;
  permissions: string[];
  badge?: string;
  status: MenuItemStatus;
  children?: MenuItem[];
  group?: string;
  tenantIds?: string[];
};

export type CommandKind =
  | "open_module"
  | "open_dashboard"
  | "open_report"
  | "open_ai_agent"
  | "create_entity"
  | "run_workflow"
  | "execute_command"
  | "search_everything";

export type CommandItem = {
  id: string;
  kind: CommandKind;
  label: string;
  route?: string;
  keywords: string[];
  shortcut?: string;
};

export type SearchCategory =
  | "modules"
  | "users"
  | "organizations"
  | "projects"
  | "documents"
  | "crm"
  | "erp"
  | "finance"
  | "hr"
  | "ai_agents"
  | "workflows"
  | "reports"
  | "tasks"
  | "marketplace"
  | "applications"
  | "dashboards"
  | "widgets"
  | "knowledge"
  | "commands";

export type SearchDocument = {
  id: string;
  category: SearchCategory;
  title: string;
  path: string;
  tokens: string[];
  rankBoost: number;
};

export type SearchHit = SearchDocument & {
  score: number;
  match: "exact" | "fuzzy" | "semantic_ready";
};

export type FavoriteKind =
  | "page"
  | "dashboard"
  | "report"
  | "customer"
  | "project"
  | "command"
  | "ai_agent"
  | "document"
  | "search";

export type FavoriteEntry = {
  id: string;
  kind: FavoriteKind;
  label: string;
  path: string;
};

export type HistoryKind = "page" | "command" | "search" | "document" | "report" | "ai_chat";

export type HistoryEntry = {
  id: string;
  kind: HistoryKind;
  label: string;
  path?: string;
  at: string;
};

export type ShortcutBinding = {
  id: string;
  scope: "global" | "workspace" | "user" | "ai";
  keys: string;
  action: string;
  customizable: boolean;
};

export type BreadcrumbPart = {
  label: string;
  path: string;
  level: "workspace" | "module" | "section" | "page" | "entity";
};

export type WorkspaceKind =
  | "personal"
  | "organization"
  | "department"
  | "project"
  | "customer"
  | "ai"
  | "temporary";

export type FederatedWorkspace = {
  id: string;
  kind: WorkspaceKind;
  name: string;
  route: string;
};

export type RegisteredApplication = {
  id: string;
  code: string;
  icon: string;
  name: string;
  status: string;
  owner: string;
  permissions: string[];
  version: string;
  health: string;
  lastUpdate: string;
  route: string;
};
