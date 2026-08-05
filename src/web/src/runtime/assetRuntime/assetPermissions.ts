/**
 * Asset permissions — Sprint 29.3.
 */

import type { AssetPermissionScope, AssetOwnership, EnterpriseAsset } from "./assetTypes";

const RANK: Record<AssetPermissionScope, number> = {
  public: 0,
  partner: 1,
  company: 2,
  department: 3,
  assignee: 4,
  owner: 5,
  enterprise_admin: 6,
};

export function scopesForActor(input: {
  asset: EnterpriseAsset;
  citizenId?: string;
  companyId?: string;
  isAdmin?: boolean;
}): AssetPermissionScope[] {
  const scopes: AssetPermissionScope[] = ["public"];
  if (input.isAdmin) scopes.push("enterprise_admin", "owner");
  const o = input.asset.ownership;
  if (input.citizenId && o.citizenId === input.citizenId) scopes.push("owner");
  if (input.companyId && o.companyId === input.companyId) scopes.push("owner", "company");
  if (input.citizenId && input.asset.assignedCitizenId === input.citizenId) scopes.push("assignee");
  if (input.companyId && input.asset.assignedCompanyId === input.companyId) scopes.push("company");
  if (input.companyId && o.partnerCompanyId === input.companyId) scopes.push("partner");
  if (
    o.kind === "department" &&
    input.companyId &&
    o.companyId === input.companyId
  ) {
    scopes.push("department");
  }
  // asset.permissions = ACL labels on the asset, not scopes granted to every viewer
  return [...new Set(scopes)];
}

export function canAccess(
  required: AssetPermissionScope,
  actorScopes: AssetPermissionScope[],
): boolean {
  if (required === "public") return true;
  if (actorScopes.includes("enterprise_admin")) return true;
  if (required === "owner") return actorScopes.includes("owner") || actorScopes.includes("enterprise_admin");
  const org = actorScopes.filter((s) => s !== "public");
  const need = RANK[required];
  return org.some((s) => RANK[s] >= need);
}

export function canTransfer(actorScopes: AssetPermissionScope[]): boolean {
  return canAccess("owner", actorScopes);
}

export function canAssign(actorScopes: AssetPermissionScope[]): boolean {
  return canAccess("assignee", actorScopes) || canAccess("owner", actorScopes);
}

export const assetPermissions = {
  RANK,
  scopesForActor,
  canAccess,
  canTransfer,
  canAssign,
};

export type { AssetOwnership };
