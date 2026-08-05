/**
 * EBN permissions — Sprint 29.0.
 */

import type { VisibilityScope, BusinessRelationship, RelationshipType } from "./ebnTypes";

const SCOPE_RANK: Record<VisibilityScope, number> = {
  public: 0,
  friends: 1,
  partners: 2,
  internal: 3,
  private: 4,
  enterprise_admin: 5,
  organization_owner: 6,
};

const RELATIONSHIP_TO_SCOPE: Partial<Record<RelationshipType, VisibilityScope>> = {
  friend: "friends",
  partner: "partners",
  trusted_partner: "partners",
  strategic_partner: "partners",
  supplier: "partners",
  client: "partners",
  dealer: "partners",
  contractor: "partners",
  internal_organization: "internal",
};

export function scopeAllows(required: VisibilityScope, actorScopes: VisibilityScope[]): boolean {
  if (required === "public") return true;
  if (actorScopes.includes("organization_owner") || actorScopes.includes("enterprise_admin")) {
    return true;
  }
  const need = SCOPE_RANK[required];
  return actorScopes.some((s) => SCOPE_RANK[s] >= need);
}

export function scopesFromRelationships(
  relationships: BusinessRelationship[],
  viewerProfileId: string,
  targetProfileId: string,
): VisibilityScope[] {
  const scopes: VisibilityScope[] = ["public"];
  for (const r of relationships) {
    if (r.state !== "approved") continue;
    const involves =
      (r.fromProfileId === viewerProfileId && r.toProfileId === targetProfileId) ||
      (r.toProfileId === viewerProfileId && r.fromProfileId === targetProfileId);
    if (!involves) continue;
    const mapped = RELATIONSHIP_TO_SCOPE[r.type];
    if (mapped) scopes.push(mapped);
    scopes.push(...r.permissions);
  }
  return [...new Set(scopes)];
}

export function canViewProfile(
  visibility: VisibilityScope,
  viewerScopes: VisibilityScope[],
  isOwner: boolean,
): boolean {
  if (isOwner) return true;
  return scopeAllows(visibility, viewerScopes);
}

export function canMutateRelationship(
  actorScopes: VisibilityScope[],
  action: "create" | "approve" | "reject" | "delete" | "update",
): boolean {
  if (action === "create" || action === "update") {
    return (
      actorScopes.includes("partners") ||
      actorScopes.includes("internal") ||
      actorScopes.includes("organization_owner") ||
      actorScopes.includes("enterprise_admin") ||
      actorScopes.includes("public")
    );
  }
  return (
    actorScopes.includes("organization_owner") ||
    actorScopes.includes("enterprise_admin") ||
    actorScopes.includes("partners") ||
    actorScopes.includes("internal")
  );
}

export const ebnPermissions = {
  scopeAllows,
  scopesFromRelationships,
  canViewProfile,
  canMutateRelationship,
  SCOPE_RANK,
};
