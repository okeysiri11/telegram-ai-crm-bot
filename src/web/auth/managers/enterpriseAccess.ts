/**
 * Frontend access helpers — Sprint 30.1.
 * Complements backend ISAM + platform_security.permission_engine.
 */

import { roleManager } from "./roleManager";
import { permissionManager } from "./permissionManager";

export type AccessContext = {
  roles: string[];
  permissions: string[];
  tenantId?: string;
};

const ELEVATED = new Set([
  "owner",
  "Owner",
  "platform_owner",
  "administrator",
  "Administrator",
  "super_admin",
]);

export const roleResolver = {
  resolve(roleNames: string[]) {
    return roleNames.map((n) => roleManager.resolve(n)).filter(Boolean);
  },
  permissionGroups(roleNames: string[]): string[] {
    const groups = new Set<string>();
    for (const role of this.resolve(roleNames)) {
      for (const g of role?.permissionGroups || []) groups.add(g);
    }
    return [...groups];
  },
};

export const permissionResolver = {
  allow(ctx: AccessContext, permission: string): boolean {
    if (ctx.permissions.includes("*") || ctx.permissions.includes(permission)) return true;
    if (ctx.roles.some((r) => ELEVATED.has(r))) return true;
    const groups = roleResolver.permissionGroups(ctx.roles);
    if (groups.includes(permission) || groups.some((g) => permission.startsWith(`${g}.`) || permission.startsWith(`${g}_`))) {
      return true;
    }
    // Known domain catalog from permissionManager
    const domains = permissionManager.domains();
    if (domains.includes(permission as never)) {
      return groups.includes(permission);
    }
    return false;
  },
};

export function accessMiddleware(ctx: AccessContext, permission: string): boolean {
  return permissionResolver.allow(ctx, permission);
}
