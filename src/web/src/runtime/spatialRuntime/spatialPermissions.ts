/**
 * Spatial permissions — Sprint 29.4.
 */

export type SpatialPermissionScope =
  | "public"
  | "citizen"
  | "company"
  | "assigned"
  | "enterprise_admin";

const RANK: Record<SpatialPermissionScope, number> = {
  public: 0,
  citizen: 1,
  company: 2,
  assigned: 3,
  enterprise_admin: 4,
};

export function scopesForActor(input: {
  citizenId?: string;
  companyId?: string;
  assignedEntityId?: string;
  subjectCitizenId?: string;
  subjectCompanyId?: string;
  isAdmin?: boolean;
}): SpatialPermissionScope[] {
  const scopes: SpatialPermissionScope[] = ["public"];
  if (input.isAdmin) scopes.push("enterprise_admin");
  if (input.citizenId) scopes.push("citizen");
  if (input.companyId) scopes.push("company");
  if (
    input.citizenId &&
    input.subjectCitizenId &&
    input.citizenId === input.subjectCitizenId
  ) {
    scopes.push("assigned");
  }
  if (
    input.companyId &&
    input.subjectCompanyId &&
    input.companyId === input.subjectCompanyId
  ) {
    scopes.push("company", "assigned");
  }
  return [...new Set(scopes)];
}

export function canAccess(
  required: SpatialPermissionScope,
  actorScopes: SpatialPermissionScope[],
): boolean {
  if (required === "public") return true;
  if (actorScopes.includes("enterprise_admin")) return true;
  const need = RANK[required];
  return actorScopes.some((s) => RANK[s] >= need);
}

export function canAssignLocation(actorScopes: SpatialPermissionScope[]): boolean {
  return canAccess("assigned", actorScopes) || canAccess("enterprise_admin", actorScopes);
}

export function canViewPrivateLocation(actorScopes: SpatialPermissionScope[]): boolean {
  return canAccess("company", actorScopes) || canAccess("assigned", actorScopes);
}

export const spatialPermissions = {
  RANK,
  scopesForActor,
  canAccess,
  canAssignLocation,
  canViewPrivateLocation,
};
