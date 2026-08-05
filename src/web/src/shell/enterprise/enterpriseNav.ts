/**
 * Sprint 27.1 — Enterprise Application Shell primary navigation.
 * Canonical sidebar sections; routes reuse existing modules (no parallel apps).
 */

export type ShellNavItem = {
  id: string;
  label: string;
  route: string;
  icon: ShellIconId;
  badge?: string;
  comingSoon?: boolean;
};

export type ShellIconId =
  | "dashboard"
  | "desktop"
  | "builder"
  | "crm"
  | "erp"
  | "projects"
  | "ai_studio"
  | "ai_agents"
  | "knowledge"
  | "documents"
  | "analytics"
  | "marketplace"
  | "automation"
  | "integrations"
  | "security"
  | "city"
  | "settings";

export const ENTERPRISE_SHELL_NAV: ShellNavItem[] = [
  { id: "dashboard", label: "Dashboard", route: "/dashboard", icon: "dashboard" },
  { id: "crm", label: "CRM", route: "/workspace/crm", icon: "crm" },
  { id: "erp", label: "ERP", route: "/workspace/erp", icon: "erp" },
  { id: "projects", label: "Projects", route: "/workspace", icon: "projects" },
  { id: "ai_studio", label: "AI Studio", route: "/platform-builder/builder-studio", icon: "ai_studio" },
  { id: "ai_agents", label: "AI Agents", route: "/platform-builder/ai-team", icon: "ai_agents" },
  { id: "knowledge", label: "Knowledge Base", route: "/platform-builder/knowledge", icon: "knowledge" },
  { id: "documents", label: "Documents", route: "/workspace/docs", icon: "documents" },
  { id: "analytics", label: "Analytics", route: "/workspace/analytics", icon: "analytics" },
  { id: "marketplace", label: "Marketplace", route: "/platform-builder/solution-hub", icon: "marketplace" },
  { id: "automation", label: "Automation", route: "/platform-builder/automation", icon: "automation" },
  { id: "integrations", label: "Integrations", route: "/platform-builder/integrations", icon: "integrations" },
  { id: "security", label: "Security", route: "/identity/security", icon: "security" },
  {
    id: "city",
    label: "Enterprise City",
    route: "/enterprise-city",
    icon: "city",
    badge: "Soon",
    comingSoon: true,
  },
  { id: "settings", label: "Settings", route: "/settings", icon: "settings" },
];
