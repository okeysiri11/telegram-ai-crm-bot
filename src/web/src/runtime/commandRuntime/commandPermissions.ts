/**
 * Command permissions — Sprint 28.6.
 * Maps Admin · Developer · Manager · Operator · Client · Guest.
 */

import type { CommandRole } from "./commandTypes";

const ROLE_RANK: Record<CommandRole, number> = {
  guest: 0,
  client: 1,
  operator: 2,
  manager: 3,
  developer: 4,
  admin: 5,
};

/** Baseline permissions granted by each platform role. */
export const ROLE_PERMISSIONS: Record<CommandRole, string[]> = {
  admin: ["*"],
  developer: ["*", "developer", "read", "write", "builder", "crm", "erp"],
  manager: ["read", "write", "admin", "crm", "erp", "finance", "builder"],
  operator: ["read", "write", "crm", "erp", "projects"],
  client: ["read", "crm"],
  guest: ["read"],
};

export function roleRank(role: CommandRole): number {
  return ROLE_RANK[role] ?? 0;
}

export function meetsMinRole(current: CommandRole, min?: CommandRole): boolean {
  if (!min) return true;
  return roleRank(current) >= roleRank(min);
}

export function canExecutePermission(
  required: string | undefined,
  permissions: string[],
): boolean {
  if (!permissions.length) return false;
  if (permissions.includes("*") || !required || required === "*") return true;
  if (permissions.includes(required)) return true;
  const prefix = required.split("_")[0];
  return Boolean(prefix && permissions.includes(prefix));
}

/**
 * Resolve CommandRole from auth roleId / roles[] strings.
 */
export function resolveCommandRole(input: {
  roleId?: string | null;
  roles?: string[] | null;
}): CommandRole {
  const blob = [
    String(input.roleId || "").toLowerCase(),
    ...(input.roles || []).map((r) => r.toLowerCase()),
  ].join(" ");

  if (
    blob.includes("platform_owner") ||
    blob.includes("platform_admin") ||
    blob.includes("system_admin") ||
    /\bowner\b/.test(blob) ||
    /\badmin\b/.test(blob)
  ) {
    return "admin";
  }
  if (blob.includes("developer") || blob.includes("dev") || blob.includes("builder")) {
    return "developer";
  }
  if (blob.includes("manager") || blob.includes("lead") || blob.includes("org_owner")) {
    return "manager";
  }
  if (blob.includes("operator") || blob.includes("employee") || blob.includes("ops")) {
    return "operator";
  }
  if (blob.includes("client") || blob.includes("customer")) {
    return "client";
  }
  if (!blob.trim()) return "guest";
  return "operator";
}

export function permissionsForRole(role: CommandRole, extra: string[] = []): string[] {
  const base = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.guest;
  if (base.includes("*")) return ["*", ...extra];
  return [...new Set([...base, ...extra])];
}
