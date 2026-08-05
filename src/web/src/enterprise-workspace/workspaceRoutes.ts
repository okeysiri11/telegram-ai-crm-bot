/**
 * Sprint 30.7 — Canonical workspace module routes (must all resolve in App).
 */

export const WORKSPACE_MODULE_ROUTES = [
  { id: "crm", label: "CRM", route: "/crm" },
  { id: "erp", label: "ERP", route: "/erp" },
  { id: "knowledge", label: "Граф знаний", route: "/knowledge" },
  { id: "ai", label: "AI Runtime", route: "/ai-agents" },
  { id: "production", label: "Продакшн", route: "/production-studio" },
  { id: "marketplace", label: "Маркетплейс", route: "/marketplace" },
  { id: "analytics", label: "Аналитика", route: "/analytics" },
  { id: "notifications", label: "Уведомления", route: "/notifications" },
  { id: "documents", label: "Документы", route: "/documents" },
  { id: "calendar", label: "Календарь", route: "/calendar" },
  { id: "finance", label: "Финансы", route: "/workspace/finance" },
  { id: "tasks", label: "Задачи", route: "/tasks" },
  { id: "users", label: "Пользователи", route: "/identity/users" },
  { id: "settings", label: "Настройки", route: "/settings" },
  { id: "city", label: "Город", route: "/city" },
] as const;

export function assertNoDeadWorkspaceRoutes(registered: string[]): { ok: boolean; missing: string[] } {
  const set = new Set(registered);
  const missing = WORKSPACE_MODULE_ROUTES.map((r) => r.route).filter((p) => !set.has(p));
  return { ok: missing.length === 0, missing };
}
