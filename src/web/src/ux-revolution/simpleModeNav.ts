/**
 * Sprint 33.1 — Simple Mode primary navigation allowlist.
 * Maps to existing routes; Search opens the command palette (no route).
 */

import type { RuNavItem } from "@/navigation/enterpriseRuNav";
import type { ExperienceMode } from "./experienceModeStore";

export type SimpleNavItem = RuNavItem & {
  /** When true, UI opens Ctrl+K instead of navigating */
  opensPalette?: boolean;
};

export const SIMPLE_MODE_NAV: SimpleNavItem[] = [
  { id: "dashboard", label: "Главная", route: "/dashboard", icon: "dashboard" },
  { id: "ai_assistant", label: "AI-Ассистент", route: "/ai-agents", icon: "ai_agents" },
  { id: "crm", label: "CRM", route: "/crm", icon: "crm" },
  { id: "projects", label: "Проекты", route: "/projects", icon: "projects" },
  { id: "documents", label: "Документы", route: "/documents", icon: "documents" },
  { id: "calendar", label: "Календарь", route: "/calendar", icon: "dashboard" },
  { id: "finance", label: "Финансы", route: "/analytics", icon: "analytics" },
  { id: "settings", label: "Настройки", route: "/settings", icon: "settings" },
  { id: "notifications", label: "Уведомления", route: "/notifications", icon: "dashboard" },
  {
    id: "search",
    label: "Поиск",
    route: "/search",
    icon: "dashboard",
    opensPalette: true,
  },
];

export const SIMPLE_MODE_NAV_IDS = new Set(SIMPLE_MODE_NAV.map((i) => i.id));

/** Routes allowed in Simple Mode (deep-links outside this still work; nav hides them). */
const SIMPLE_ROUTE_PREFIXES = [
  "/dashboard",
  "/ai-agents",
  "/crm",
  "/projects",
  "/documents",
  "/calendar",
  "/analytics",
  "/settings",
  "/notifications",
  "/search",
  "/login",
  "/auth",
  "/onboarding",
  "/owner",
  "/tasks",
];

export function isSimpleModeRoute(pathname: string): boolean {
  const path = pathname.split("?")[0] || "/";
  return SIMPLE_ROUTE_PREFIXES.some((p) => path === p || path.startsWith(`${p}/`));
}

export function filterNavForMode<T extends { id: string; route?: string }>(
  items: T[],
  mode: ExperienceMode,
): T[] {
  if (mode === "pro") return items;
  const simpleIds = SIMPLE_MODE_NAV_IDS;
  const simpleRoutes = new Set(SIMPLE_MODE_NAV.map((i) => i.route.split("?")[0]));
  return items.filter((item) => {
    if (simpleIds.has(item.id)) return true;
    const route = (item.route || "").split("?")[0];
    return route ? simpleRoutes.has(route) : false;
  });
}
