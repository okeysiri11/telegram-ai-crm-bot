/**
 * Sprint 30.3 / 31.0 / 42.1 — resolve post-login / home route by active role.
 */

import { loadFirstEntry, isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { isClientOnboardingComplete } from "@/multi-role/clientOnboardingStore";
import { demoUserByEmail } from "@/multi-role/demoUsers";

export type RoleHomeId =
  | "owner"
  | "administrator"
  | "manager"
  | "employee"
  | "dealer"
  | "partner"
  | "client"
  | "viewer"
  | "sales";

/** Sprint 42.1 — role-based homes */
const ROLE_HOME: Record<RoleHomeId, string> = {
  owner: "/owner",
  administrator: "/admin",
  manager: "/dashboards/manager",
  sales: "/crm?view=pipeline",
  employee: "/dashboards/employee",
  dealer: "/dashboards/dealer",
  partner: "/dashboards/dealer",
  client: "/dashboard",
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
  if (roleId === "sales") return "sales";
  if (roleId === "manager" || roleId === "support") return "manager";
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
  // Sprint 42.1 — canonical role homes win over first-entry catalog aliases
  if (roleId && (roleId as RoleHomeId) in ROLE_HOME) {
    return ROLE_HOME[roleId as RoleHomeId];
  }
  const mapped = mapToRoleHomeId(roleId);
  if (ROLE_HOME[mapped]) return ROLE_HOME[mapped];
  const entry = roleId ? firstEntryRoleCatalog.get(roleId) : undefined;
  if (entry?.workspaceRoute) return entry.workspaceRoute;
  return "/dashboard";
}

function isClientLike(roleId?: string | null, email?: string | null): boolean {
  if (roleId === "client") return true;
  if (email && demoUserByEmail(email)?.viewMode === "client") return true;
  return false;
}

/** After auth: client onboarding / first-run wizard if incomplete, else role home. */
export function postAuthDestination(activeRoleId?: string | null, email?: string | null): string {
  if (isClientLike(activeRoleId, email) && !isClientOnboardingComplete()) {
    return "/onboarding/client";
  }
  if (!isClientLike(activeRoleId, email) && !isFirstEntryComplete()) {
    return "/onboarding/first-entry";
  }
  const first = loadFirstEntry();
  const mapped = mapToRoleHomeId(activeRoleId || first.roleId);
  if (activeRoleId) {
    return homeRouteForRole(mapped);
  }
  const entry = firstEntryRoleCatalog.get(first.roleId);
  if (entry?.workspaceRoute) {
    if (entry.workspaceRoute.startsWith("/workspace/")) return entry.workspaceRoute;
    if (
      entry.workspaceRoute.startsWith("/dashboards/") ||
      entry.workspaceRoute === "/owner" ||
      entry.workspaceRoute === "/admin"
    ) {
      return entry.workspaceRoute;
    }
  }
  return homeRouteForRole(mapped);
}
