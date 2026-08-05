/**
 * Digital Citizen permissions — Sprint 29.1.
 */

import type { CitizenPermissionScope, OrganizationMember, OrganizationRole } from "./citizenTypes";

const SCOPE_RANK: Record<CitizenPermissionScope, number> = {
  public: 0,
  partners: 1,
  company: 2,
  department: 3,
  manager: 4,
  self: 5,
  enterprise_admin: 6,
};

const ROLE_SCOPES: Record<OrganizationRole, CitizenPermissionScope[]> = {
  owner: ["self", "manager", "department", "company", "enterprise_admin"],
  admin: ["self", "manager", "department", "company"],
  manager: ["self", "manager", "department", "company"],
  member: ["self", "department", "company"],
  contractor: ["self", "company"],
  guest: ["self", "public"],
};

export function scopesForMember(member: OrganizationMember | null, isSelf: boolean): CitizenPermissionScope[] {
  const scopes: CitizenPermissionScope[] = ["public"];
  if (isSelf) scopes.push("self");
  if (member?.active) scopes.push(...(ROLE_SCOPES[member.role] || ["self"]));
  return [...new Set(scopes)];
}

export function canAccess(
  required: CitizenPermissionScope,
  actorScopes: CitizenPermissionScope[],
): boolean {
  if (required === "public") return true;
  if (actorScopes.includes("enterprise_admin")) return true;
  if (required === "self") {
    return actorScopes.includes("self") || actorScopes.includes("enterprise_admin");
  }
  // `self` / `public` do not imply org scopes (department, company, …)
  const orgScopes = actorScopes.filter((s) => s !== "self" && s !== "public");
  const need = SCOPE_RANK[required];
  return orgScopes.some((s) => SCOPE_RANK[s] >= need);
}

export function canManageMember(
  actor: OrganizationMember | null,
  target: OrganizationMember,
): boolean {
  if (!actor?.active) return false;
  if (actor.role === "owner" || actor.role === "admin") return true;
  if (actor.role === "manager" && target.managerCitizenId === actor.citizenId) return true;
  return actor.citizenId === target.citizenId && actor.role !== "guest";
}

export const citizenPermissions = {
  SCOPE_RANK,
  ROLE_SCOPES,
  scopesForMember,
  canAccess,
  canManageMember,
};
