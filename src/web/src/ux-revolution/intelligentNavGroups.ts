/**
 * Sprint 33.2 — Intelligent Navigation groups (collapsible accordion).
 * Routes unchanged; presentation only.
 */

import type { RuNavItem } from "@/navigation/enterpriseRuNav";
import { OWNER_RU_NAV } from "@/navigation/enterpriseRuNav";
import type { ShellIconId } from "@/shell/enterprise";
import type { ExperienceMode } from "./experienceModeStore";

export type NavGroupId =
  | "workspace"
  | "business"
  | "ai"
  | "city"
  | "platform"
  | "owner";

export type IntelligentNavItem = RuNavItem & {
  opensPalette?: boolean;
  /** Visible in Simple Mode when true (default false for Pro-only) */
  simple?: boolean;
};

export type IntelligentNavGroup = {
  id: NavGroupId;
  label: string;
  labelEn: string;
  icon: ShellIconId;
  /** Simple Mode may show this group */
  simple: boolean;
  /** Only for Owner Mode (platform owner / owner view) */
  ownerOnly?: boolean;
  items: IntelligentNavItem[];
};

/** Canonical accordion catalog — Sprint 33.2 */
export const INTELLIGENT_NAV_GROUPS: IntelligentNavGroup[] = [
  {
    id: "workspace",
    label: "Рабочее пространство",
    labelEn: "Workspace",
    icon: "desktop",
    simple: true,
    items: [
      { id: "ws_home", label: "Главная", route: "/dashboard", icon: "dashboard", simple: true },
      { id: "ws_desktop", label: "Рабочий стол", route: "/desktop", icon: "desktop", simple: true },
      { id: "ws_calendar", label: "Календарь", route: "/calendar", icon: "dashboard", simple: true },
      { id: "ws_tasks", label: "Задачи", route: "/tasks", icon: "projects", simple: true },
      { id: "ws_documents", label: "Документы", route: "/documents", icon: "documents", simple: true },
      { id: "ws_notifications", label: "Уведомления", route: "/notifications", icon: "dashboard", simple: true },
      { id: "ws_settings", label: "Настройки", route: "/settings", icon: "settings", simple: true },
      {
        id: "ws_search",
        label: "Поиск",
        route: "/search",
        icon: "dashboard",
        simple: true,
        opensPalette: true,
      },
    ],
  },
  {
    id: "business",
    label: "Бизнес",
    labelEn: "Business",
    icon: "crm",
    simple: true,
    items: [
      { id: "biz_crm", label: "CRM", route: "/crm", icon: "crm", simple: true },
      { id: "biz_clients", label: "Клиенты", route: "/crm?view=clients", icon: "crm", simple: true },
      { id: "biz_projects", label: "Проекты", route: "/projects", icon: "projects", simple: true },
      { id: "biz_finance", label: "Финансы", route: "/analytics", icon: "analytics", simple: true },
      { id: "biz_erp", label: "ERP", route: "/erp", icon: "erp" },
      { id: "biz_mfg", label: "Производство", route: "/erp?view=production", icon: "erp" },
      { id: "biz_marketplace", label: "Маркетплейс", route: "/marketplace", icon: "marketplace" },
      { id: "biz_legal", label: "Юридический отдел", route: "/workspace/legal", icon: "security" },
      { id: "biz_analytics", label: "Аналитика", route: "/analytics", icon: "analytics" },
    ],
  },
  {
    id: "ai",
    label: "AI",
    labelEn: "AI",
    icon: "ai_agents",
    simple: true,
    items: [
      { id: "ai_agents", label: "AI-Ассистент", route: "/ai-agents", icon: "ai_agents", simple: true },
      { id: "ai_studio", label: "AI Studio", route: "/ai-studio", icon: "ai_studio" },
      { id: "ai_production", label: "Продакшн", route: "/production-studio", icon: "ai_studio" },
      { id: "ai_knowledge", label: "Знания", route: "/knowledge", icon: "knowledge" },
      { id: "ai_runtime", label: "AI Runtime", route: "/platform-builder/runtime", icon: "ai_agents" },
      { id: "ai_team", label: "AI Team", route: "/platform-builder/ai-team", icon: "ai_agents" },
    ],
  },
  {
    id: "city",
    label: "Enterprise City",
    labelEn: "Enterprise City",
    icon: "city",
    simple: false,
    items: [
      { id: "city_home", label: "Город", route: "/city", icon: "city" },
      { id: "city_viz", label: "Визуализация", route: "/city-visualization", icon: "city" },
      { id: "city_enterprise", label: "Enterprise City", route: "/enterprise-city", icon: "city" },
    ],
  },
  {
    id: "platform",
    label: "Платформа",
    labelEn: "Platform",
    icon: "settings",
    simple: false,
    items: [
      { id: "plat_users", label: "Пользователи", route: "/identity/users", icon: "settings" },
      { id: "plat_security", label: "Безопасность", route: "/identity/security", icon: "security" },
      { id: "plat_health", label: "Мониторинг", route: "/health", icon: "dashboard" },
      { id: "plat_kernel", label: "Архитектура", route: "/kernel", icon: "settings" },
      { id: "plat_builder", label: "Builder Studio", route: "/platform-builder/builder-studio", icon: "settings" },
      { id: "plat_governance", label: "Governance", route: "/platform-builder/governance", icon: "security" },
      { id: "plat_runtime", label: "Command Runtime", route: "/command-runtime", icon: "documents" },
      { id: "plat_admin", label: "Админ", route: "/admin", icon: "settings" },
      { id: "plat_flags", label: "Флаги функций", route: "/settings?tab=flags", icon: "settings" },
    ],
  },
  {
    id: "owner",
    label: "Владелец",
    labelEn: "Owner",
    icon: "dashboard",
    simple: false,
    ownerOnly: true,
    items: OWNER_RU_NAV.map((i) => ({ ...i, simple: false })),
  },
];

export const NAV_ACCORDION_KEY = "ewp_nav_accordion_group_v1";

export function groupsForMode(
  mode: ExperienceMode,
  opts?: { owner?: boolean },
): IntelligentNavGroup[] {
  const owner = opts?.owner ?? false;

  // Owner Mode: every group including Owner (full Pro item lists).
  if (owner) {
    return INTELLIGENT_NAV_GROUPS.map((g) => ({ ...g, items: [...g.items] }));
  }

  return INTELLIGENT_NAV_GROUPS.filter((g) => {
    if (g.ownerOnly) return false;
    if (mode === "simple") return g.simple;
    return true;
  }).map((g) => ({
    ...g,
    items: mode === "simple" ? g.items.filter((i) => i.simple) : [...g.items],
  }));
}

/** Resolve which group contains the current path (for auto-expand / highlight). */
export function resolveGroupForPath(pathname: string, search = ""): NavGroupId | null {
  const full = `${pathname}${search}`.toLowerCase();
  const path = pathname.toLowerCase();
  for (const g of INTELLIGENT_NAV_GROUPS) {
    for (const item of g.items) {
      const route = item.route.toLowerCase();
      const base = route.split("?")[0] || route;
      if (full === route || path === base || path.startsWith(`${base}/`)) {
        return g.id;
      }
      if (route.includes("?") && full.startsWith(base) && full.includes(route.split("?")[1] || "")) {
        return g.id;
      }
    }
  }
  return null;
}

export function isNavItemActive(item: IntelligentNavItem, pathname: string, search: string): boolean {
  const full = `${pathname}${search}`;
  const route = item.route;
  const base = route.split("?")[0] || route;
  if (route.includes("?")) {
    return full === route || (pathname === base && search.includes(route.split("?")[1] || ""));
  }
  if (base === "/dashboard") return pathname === "/dashboard";
  return pathname === base || pathname.startsWith(`${base}/`);
}
