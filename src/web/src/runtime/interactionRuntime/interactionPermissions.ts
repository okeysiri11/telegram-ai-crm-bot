/**
 * Interaction permissions — Sprint 29.6.
 */

export type InteractionPermissionScope =
  | "public"
  | "citizen"
  | "company"
  | "manager"
  | "enterprise_admin";

const RANK: Record<InteractionPermissionScope, number> = {
  public: 0,
  citizen: 1,
  company: 2,
  manager: 3,
  enterprise_admin: 4,
};

const ACTION_REQUIRED: Record<string, InteractionPermissionScope> = {
  open_company: "public",
  open_citizen: "citizen",
  open_asset: "company",
  open_building: "public",
  open_district: "public",
  open_project: "citizen",
  open_meeting: "citizen",
  open_vehicle: "company",
  navigate: "public",
  launch_ai: "citizen",
  assign_task: "manager",
  create_meeting: "citizen",
  invite_partner: "company",
  start_workflow: "company",
};

export function scopesForActor(input: {
  citizenId?: string;
  companyId?: string;
  isAdmin?: boolean;
  isManager?: boolean;
}): InteractionPermissionScope[] {
  const scopes: InteractionPermissionScope[] = ["public"];
  if (input.citizenId) scopes.push("citizen");
  if (input.companyId) scopes.push("company");
  if (input.isManager) scopes.push("manager");
  if (input.isAdmin) scopes.push("enterprise_admin", "manager", "company");
  return [...new Set(scopes)];
}

export function canAccess(
  required: InteractionPermissionScope,
  actorScopes: InteractionPermissionScope[],
): boolean {
  if (required === "public") return true;
  if (actorScopes.includes("enterprise_admin")) return true;
  const need = RANK[required];
  return actorScopes.some((s) => RANK[s] >= need);
}

export function canExecuteAction(
  actionId: string,
  actorScopes: InteractionPermissionScope[],
): boolean {
  const need = ACTION_REQUIRED[actionId] || "citizen";
  return canAccess(need, actorScopes);
}

export const interactionPermissions = {
  RANK,
  ACTION_REQUIRED,
  scopesForActor,
  canAccess,
  canExecuteAction,
};
