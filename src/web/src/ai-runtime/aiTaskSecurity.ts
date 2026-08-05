/**
 * Sprint 30.5 — AI task security: roles, workspace/org isolation, audit.
 */

import { accessMiddleware, type AccessContext } from "../../auth/managers/enterpriseAccess";
import { appendAuditVault } from "@/audit-vault";

export type AiTaskSecurityContext = AccessContext & {
  orgId: string;
  workspaceId: string;
  actor: string;
};

export type AiTaskResource = {
  orgId?: string;
  workspaceId?: string;
};

const AI_PERMS = ["ai_agents", "ai_agents.write", "ai_agents.manage", "ai_agents.read"] as const;

export function canManageAiTasks(ctx: AccessContext): boolean {
  return (
    accessMiddleware(ctx, "ai_agents") ||
    accessMiddleware(ctx, "ai_agents.manage") ||
    accessMiddleware(ctx, "ai_agents.write") ||
    accessMiddleware(ctx, "*")
  );
}

export function canReadAiTasks(ctx: AccessContext): boolean {
  return canManageAiTasks(ctx) || accessMiddleware(ctx, "ai_agents.read") || accessMiddleware(ctx, "ai_agents");
}

/** Workspace + organization isolation — owner/platform may cross tenants. */
export function canAccessTaskResource(ctx: AiTaskSecurityContext, resource: AiTaskResource): boolean {
  if (!canReadAiTasks(ctx)) return false;
  const elevated = ctx.roles.some((r) =>
    ["owner", "Owner", "platform_owner", "administrator", "Administrator"].includes(r),
  );
  if (elevated) return true;
  if (resource.orgId && resource.orgId !== ctx.orgId) return false;
  if (resource.workspaceId && resource.workspaceId !== ctx.workspaceId) return false;
  return true;
}

export async function auditAiTask(
  ctx: Pick<AiTaskSecurityContext, "actor" | "orgId" | "workspaceId">,
  action: string,
  resource: string,
  detail?: string,
) {
  return appendAuditVault({
    actor: ctx.actor,
    action: `ai_task.${action}`,
    resource,
    detail: detail || `org=${ctx.orgId};ws=${ctx.workspaceId}`,
    correlationId: `ai_${ctx.orgId}_${ctx.workspaceId}`,
  });
}

export { AI_PERMS };
