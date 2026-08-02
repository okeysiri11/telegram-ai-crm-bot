/**
 * Sprint 33.1 — Context navigation: module-scoped left menu.
 */

export type ContextNavItem = {
  id: string;
  label: string;
  route: string;
  icon?: string;
};

export type ModuleContext = {
  moduleId: string;
  label: string;
  /** Path prefixes that activate this context */
  match: string[];
  /** Simple mode may hide some contexts that are Pro-only */
  proOnly?: boolean;
  items: ContextNavItem[];
};

export const MODULE_CONTEXT_NAV: ModuleContext[] = [
  {
    moduleId: "crm",
    label: "CRM",
    match: ["/crm", "/workspace/crm"],
    items: [
      { id: "crm_customers", label: "Клиенты", route: "/crm?view=clients", icon: "crm" },
      { id: "crm_deals", label: "Сделки", route: "/crm?view=deals", icon: "crm" },
      { id: "crm_contacts", label: "Контакты", route: "/crm?view=contacts", icon: "crm" },
      { id: "crm_leads", label: "Лиды", route: "/crm?view=leads", icon: "crm" },
      { id: "crm_comms", label: "Коммуникации", route: "/crm?view=communications", icon: "crm" },
      { id: "crm_reports", label: "Отчёты", route: "/crm?view=reports", icon: "analytics" },
    ],
  },
  {
    moduleId: "projects",
    label: "Проекты",
    match: ["/projects", "/tasks"],
    items: [
      { id: "proj_all", label: "Все проекты", route: "/projects", icon: "projects" },
      { id: "proj_tasks", label: "Задачи", route: "/tasks", icon: "projects" },
      { id: "proj_board", label: "Доска", route: "/projects?view=board", icon: "projects" },
      { id: "proj_overdue", label: "Просроченные", route: "/projects?view=overdue", icon: "projects" },
      { id: "proj_reports", label: "Отчёты", route: "/projects?view=reports", icon: "analytics" },
    ],
  },
  {
    moduleId: "finance",
    label: "Финансы",
    match: ["/analytics"],
    items: [
      { id: "fin_overview", label: "Обзор", route: "/analytics", icon: "analytics" },
      { id: "fin_invoices", label: "Счета", route: "/analytics?view=invoices", icon: "analytics" },
      { id: "fin_payments", label: "Платежи", route: "/analytics?view=payments", icon: "analytics" },
      { id: "fin_reports", label: "Отчёты", route: "/analytics?view=reports", icon: "analytics" },
      { id: "fin_kpi", label: "KPI", route: "/analytics?view=kpi", icon: "analytics" },
    ],
  },
  {
    moduleId: "documents",
    label: "Документы",
    match: ["/documents"],
    items: [
      { id: "doc_all", label: "Все документы", route: "/documents", icon: "documents" },
      { id: "doc_recent", label: "Недавние", route: "/documents?view=recent", icon: "documents" },
      { id: "doc_shared", label: "Общие", route: "/documents?view=shared", icon: "documents" },
      { id: "doc_templates", label: "Шаблоны", route: "/documents?view=templates", icon: "documents" },
    ],
  },
  {
    moduleId: "calendar",
    label: "Календарь",
    match: ["/calendar"],
    items: [
      { id: "cal_today", label: "Сегодня", route: "/calendar", icon: "dashboard" },
      { id: "cal_week", label: "Неделя", route: "/calendar?view=week", icon: "dashboard" },
      { id: "cal_meetings", label: "Встречи", route: "/calendar?view=meetings", icon: "dashboard" },
    ],
  },
  {
    moduleId: "ai",
    label: "AI",
    match: ["/ai-agents", "/ai-studio"],
    items: [
      { id: "ai_agents", label: "Агенты", route: "/ai-agents", icon: "ai_agents" },
      { id: "ai_studio", label: "AI Studio", route: "/ai-studio", icon: "ai_studio" },
      { id: "ai_runtime", label: "Runtime", route: "/platform-builder/runtime", icon: "ai_agents" },
      { id: "ai_team", label: "AI Team", route: "/platform-builder/ai-team", icon: "ai_agents" },
    ],
  },
  {
    moduleId: "settings",
    label: "Настройки",
    match: ["/settings", "/identity", "/admin"],
    items: [
      { id: "set_general", label: "Общие", route: "/settings", icon: "settings" },
      { id: "set_users", label: "Пользователи", route: "/identity/users", icon: "settings" },
      { id: "set_security", label: "Безопасность", route: "/identity/security", icon: "security" },
      { id: "set_flags", label: "Флаги", route: "/settings?tab=flags", icon: "settings" },
      { id: "set_admin", label: "Админ", route: "/admin", icon: "settings" },
    ],
  },
  {
    moduleId: "erp",
    label: "ERP",
    match: ["/erp"],
    proOnly: true,
    items: [
      { id: "erp_overview", label: "Обзор", route: "/erp", icon: "erp" },
      { id: "erp_production", label: "Производство", route: "/erp?view=production", icon: "erp" },
      { id: "erp_inventory", label: "Склад", route: "/erp?view=inventory", icon: "erp" },
      { id: "erp_procurement", label: "Закупки", route: "/erp?view=procurement", icon: "erp" },
    ],
  },
  {
    moduleId: "knowledge",
    label: "Знания",
    match: ["/knowledge", "/platform-builder/knowledge"],
    proOnly: true,
    items: [
      { id: "kg_home", label: "База знаний", route: "/knowledge", icon: "knowledge" },
      { id: "kg_graph", label: "Граф знаний", route: "/platform-builder/knowledge", icon: "knowledge" },
    ],
  },
  {
    moduleId: "marketplace",
    label: "Маркетплейс",
    match: ["/marketplace"],
    proOnly: true,
    items: [
      { id: "mp_home", label: "Каталог", route: "/marketplace", icon: "marketplace" },
      { id: "mp_apps", label: "Приложения", route: "/marketplace?view=apps", icon: "marketplace" },
    ],
  },
  {
    moduleId: "governance",
    label: "Управление",
    match: ["/platform-builder/governance", "/platform-builder/god-mode"],
    proOnly: true,
    items: [
      { id: "gov_home", label: "Governance", route: "/platform-builder/governance", icon: "security" },
      { id: "gov_audit", label: "Аудит", route: "/platform-builder/governance?view=audit", icon: "security" },
      { id: "gov_god", label: "God Mode", route: "/platform-builder/god-mode", icon: "dashboard" },
    ],
  },
];

export function resolveModuleContext(
  pathname: string,
  opts?: { pro?: boolean },
): ModuleContext | null {
  const path = (pathname.split("?")[0] || "/").toLowerCase();
  const pro = opts?.pro ?? true;
  for (const ctx of MODULE_CONTEXT_NAV) {
    if (ctx.proOnly && !pro) continue;
    if (ctx.match.some((m) => path === m || path.startsWith(`${m}/`) || path.startsWith(m))) {
      // Prefer longer / more specific matches — first listed wins; CRM before generic
      return ctx;
    }
  }
  return null;
}
