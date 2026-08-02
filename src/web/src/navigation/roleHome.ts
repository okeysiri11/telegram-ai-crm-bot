/**
 * Sprint 30.3 / 31.0 — resolve post-login / home route by active role.
 * Closed Beta: map first-entry role ids → role homes.
 */

import { loadFirstEntry, isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";

export type RoleHomeId =
  | "owner"
  | "administrator"
  | "manager"
  | "employee"
  | "dealer"
  | "partner"
  | "client"
  | "viewer";

const ROLE_HOME: Record<RoleHomeId, string> = {
  owner: "/owner",
  administrator: "/admin",
  manager: "/dashboards/manager",
  employee: "/dashboards/employee",
  dealer: "/dashboards/dealer",
  partner: "/dashboards/dealer",
  client: "/dashboards/client",
  viewer: "/dashboard",
};

export function mapToRoleHomeId(roleId: string | undefined | null): RoleHomeId {
  if (!roleId) return "employee";
  if (
    roleId === "owner" ||
    roleId === "business_owner" ||
    roleId === "executive" ||
    roleId === "platform_owner" ||
    roleId === "ceo"
  ) {
    return "owner";
  }
  if (roleId === "administrator" || roleId === "admin" || roleId === "system_admin") return "administrator";
  if (roleId === "manager" || roleId === "sales") return "manager";
  if (roleId === "employee" || roleId === "finance" || roleId === "production" || roleId === "ai_engineer") {
    return "employee";
  }
  if (roleId === "developer") return "administrator";
  if (roleId === "client") return "client";
  if (roleId === "dealer" || roleId.includes("dealer") || roleId === "auto" || roleId === "auto_service") {
    return "dealer";
  }
  if (roleId === "partner") return "partner";
  if (roleId === "viewer" || roleId === "read_only") return "viewer";
  const entry = firstEntryRoleCatalog.get(roleId);
  if (entry?.workspaceRoute?.startsWith("/owner")) return "owner";
  if (entry?.workspaceRoute?.startsWith("/admin")) return "administrator";
  if (entry?.workspaceRoute?.includes("manager")) return "manager";
  if (entry?.workspaceRoute?.includes("employee")) return "employee";
  if (entry?.workspaceRoute?.includes("client")) return "client";
  if (entry?.workspaceRoute?.includes("dealer")) return "dealer";
  return "employee";
}

/** Prefer explicit workspaceRoute from first-entry / UX catalog when present. */
export function homeRouteForRole(roleId: string | undefined | null): string {
  const entry = roleId ? firstEntryRoleCatalog.get(roleId) : undefined;
  if (entry?.workspaceRoute) return entry.workspaceRoute;
  const id = (roleId || "employee") as RoleHomeId;
  return ROLE_HOME[id] || "/dashboard";
}

/** After auth: first-run wizard if incomplete, else role home. */
export function postAuthDestination(activeRoleId?: string | null): string {
  if (!isFirstEntryComplete()) {
    return "/onboarding/first-entry";
  }
  const first = loadFirstEntry();
  const mapped = mapToRoleHomeId(activeRoleId || first.roleId);
  const entry = firstEntryRoleCatalog.get(first.roleId);
  // Prefer explicit workspaceRoute from first-entry catalog when present
  if (!activeRoleId && entry?.workspaceRoute) {
    if (entry.workspaceRoute.startsWith("/workspace/")) return entry.workspaceRoute;
    if (entry.workspaceRoute.startsWith("/dashboards/") || entry.workspaceRoute === "/owner" || entry.workspaceRoute === "/admin") {
      return entry.workspaceRoute;
    }
  }
  return homeRouteForRole(mapped);
}
