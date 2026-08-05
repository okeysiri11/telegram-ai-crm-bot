/**
 * Sprint 30.6 / 32.5 — Owner Mode subsystem directory (every major beta surface).
 */

export const OWNER_SUBSYSTEMS = [
  { id: "status", label: "Статус платформы", route: "/health", description: "CPU · Memory · Runtime · API · DB · Redis" },
  { id: "users", label: "Пользователи", route: "/identity/users", description: "ISAM users & sessions" },
  { id: "orgs", label: "Организации", route: "/identity/organizations", description: "Tenancy & orgs" },
  { id: "agents", label: "Агенты", route: "/ai-agents", description: "AI Agent Center" },
  { id: "runtime", label: "Runtime", route: "/platform-builder/runtime", description: "AI Runtime · очереди" },
  { id: "security", label: "Безопасность", route: "/identity/security", description: "Security Center · Zero Trust" },
  { id: "notifications", label: "Уведомления", route: "/notifications", description: "Notification center" },
  { id: "projects", label: "Проекты", route: "/projects", description: "Project hub" },
  { id: "crm", label: "CRM", route: "/crm", description: "Clients & deals" },
  { id: "knowledge", label: "Знания", route: "/knowledge", description: "Knowledge Base" },
  { id: "drive", label: "Документы", route: "/documents", description: "Enterprise Drive" },
  { id: "calendar", label: "Календарь", route: "/calendar", description: "Calendar" },
  { id: "marketplace", label: "Маркетплейс", route: "/marketplace", description: "Marketplace" },
  { id: "production", label: "Продакшн", route: "/production-studio", description: "Production Studio" },
  { id: "ai_studio", label: "AI Studio", route: "/ai-studio", description: "AI Production Studio" },
  { id: "city", label: "Город", route: "/city", description: "Enterprise City" },
  { id: "search", label: "Поиск", route: "/search", description: "Global search" },
  { id: "command", label: "Command Palette", route: "/command-center", description: "Universal command center" },
  { id: "settings", label: "Настройки", route: "/settings", description: "Platform settings" },
  { id: "logs", label: "Активность", route: "/identity/activity", description: "Activity & audit trail" },
  { id: "demo", label: "Живое демо", route: "/demo/scenario", description: "Beta live demo path" },
] as const;
