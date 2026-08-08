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
  { id: "dashboard", label: "Панель управления", route: "/dashboard", icon: "dashboard" },
  { id: "crm", label: "CRM", route: "/crm", icon: "crm" },
  { id: "erp", label: "ERP", route: "/erp", icon: "erp" },
  { id: "projects", label: "Проекты", route: "/projects", icon: "projects" },
  { id: "ai_studio", label: "Студия AI", route: "/ai-studio", icon: "ai_studio" },
  { id: "ai_agents", label: "AI-агенты", route: "/ai-agents", icon: "ai_agents" },
  { id: "knowledge", label: "База знаний", route: "/knowledge", icon: "knowledge" },
  { id: "documents", label: "Документы", route: "/documents", icon: "documents" },
  { id: "analytics", label: "Аналитика", route: "/analytics", icon: "analytics" },
  { id: "marketplace", label: "Маркетплейс", route: "/marketplace", icon: "marketplace" },
  { id: "automation", label: "Автоматизация", route: "/platform-builder/automation", icon: "automation" },
  { id: "integrations", label: "Интеграции", route: "/platform-builder/integrations", icon: "integrations" },
  { id: "security", label: "Безопасность", route: "/identity/security", icon: "security" },
  {
    id: "city",
    label: "Корпоративный город",
    route: "/enterprise-city",
    icon: "city",
  },
  { id: "settings", label: "Настройки", route: "/settings", icon: "settings" },
];
