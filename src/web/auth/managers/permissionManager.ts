import type { Permission, PermissionDomain } from "../types";

const domains: PermissionDomain[] = [
  "crm",
  "erp",
  "ai_agents",
  "finance",
  "hr",
  "analytics",
  "marketplace",
  "administration",
  "api_access",
];

const permissions: Permission[] = domains.flatMap((domain) =>
  ["read", "write", "manage"].map((action) => ({
    permissionId: `perm_${domain}_${action}`,
    domain,
    action,
    syncedWithRbac: true,
  })),
);

export const permissionManager = {
  domains: () => [...domains],
  list(): Permission[] {
    return [...permissions];
  },
  byDomain(domain: PermissionDomain) {
    return permissions.filter((p) => p.domain === domain);
  },
  syncWithCoreRbac() {
    return { synced: true, count: permissions.length, source: "enterprise_core_rbac" };
  },
};
