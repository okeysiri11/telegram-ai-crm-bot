/**
 * Resolve the current workspace label, role, and section nav from existing catalogs.
 * No hardcoded AGRO-only menu.
 */

import { OWNER_RU_NAV } from "@/navigation/enterpriseRuNav";
import { resolveModuleContext } from "@/ux-revolution/moduleContextNav";
import { getVertical, sectionPath, VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";
import type { MobileNavLink } from "./opsCabinetNavStore";

export const PLATFORM_MANAGEMENT_NAV: MobileNavLink[] = [
  { id: "pm_orgs", label: "Организации", href: "/identity/users" },
  { id: "pm_workspace", label: "Workspace", href: "/workspace" },
  { id: "pm_users", label: "Пользователи", href: "/identity/users" },
  { id: "pm_roles", label: "Роли", href: "/settings?tab=interface" },
  { id: "pm_ai", label: "AI Agents", href: "/ai-agents" },
  { id: "pm_integrations", label: "Integrations", href: "/integrations" },
  { id: "pm_health", label: "System Health", href: "/health" },
  { id: "pm_admin", label: "Developer / Admin", href: "/admin" },
  ...OWNER_RU_NAV.filter((item) => !["owner_ai", "owner_admin", "owner_health"].includes(item.id)).map(
    (item) => ({
      id: item.id,
      label: item.label,
      href: item.route,
    }),
  ),
].filter((item, index, all) => all.findIndex((x) => x.href === item.href && x.label === item.label) === index);

export function verticalIdFromPath(pathname: string, fallback = "owner"): string {
  const parts = pathname.split("/").filter(Boolean);
  if ((parts[0] === "workspace" || parts[0] === "vertical") && parts[1]) {
    return parts[1];
  }
  const ctx = resolveModuleContext(pathname, { pro: true });
  if (ctx?.moduleId) return ctx.moduleId;
  return fallback;
}

export function workspaceHomePath(verticalId: string): string {
  const vertical = getVertical(verticalId);
  return vertical?.legacyRoute || vertical?.route || `/vertical/${verticalId}`;
}

export function workspaceLabel(verticalId: string): string {
  return getVertical(verticalId)?.label || verticalId;
}

export function navFromVertical(verticalId: string): MobileNavLink[] {
  const vertical = getVertical(verticalId);
  if (!vertical) return [];
  return vertical.nav.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.href || sectionPath(verticalId, item.id),
  }));
}

export function navFromContext(pathname: string, search = ""): MobileNavLink[] {
  const ctx = resolveModuleContext(`${pathname}${search}`, { pro: true });
  if (!ctx) return [];
  return ctx.items.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.route,
  }));
}

export function sectionTitle(
  pathname: string,
  search: string,
  verticalId: string,
  cabinetItems: MobileNavLink[],
): string | null {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const view = params.get("view");
  if (view) {
    const hit = cabinetItems.find((item) => item.id === view) || navFromVertical(verticalId).find((item) => item.id === view);
    if (hit && hit.id !== "home") return hit.label;
  }
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "vertical" && parts[2]) {
    const hit = navFromVertical(verticalId).find((item) => item.id === parts[2]);
    if (hit && hit.id !== "home") return hit.label;
  }
  if (parts[0] === "workspace" && parts[2]) {
    const hit = cabinetItems.find((item) => item.id === parts[2]) || navFromVertical(verticalId).find((item) => item.id === parts[2]);
    if (hit && hit.id !== "home") return hit.label;
  }
  const ctx = resolveModuleContext(`${pathname}${search}`, { pro: true });
  if (ctx && pathname !== "/dashboard") return ctx.label;
  return null;
}

export function quickActionsForWorkspace(verticalId: string): MobileNavLink[] {
  const vertical = getVertical(verticalId);
  if (vertical?.quickActions?.length) {
    return vertical.quickActions.slice(0, 5).map((action, index) => ({
      id: `qa_${index}`,
      label: action.label,
      href: action.route,
    }));
  }
  return navFromVertical(verticalId)
    .filter((item) => item.id !== "home")
    .slice(0, 5);
}

export function workspaceSwitcherItems(): MobileNavLink[] {
  return VERTICAL_WORKSPACES.map((item) => ({
    id: item.id,
    label: item.label,
    href: item.legacyRoute || item.route,
  }));
}

export function isDemoAccount(email?: string | null, tenantId?: string | null): boolean {
  const mail = (email || "").toLowerCase();
  const tenant = (tenantId || "").toLowerCase();
  return mail.includes("@demo.") || tenant.includes("demo");
}
