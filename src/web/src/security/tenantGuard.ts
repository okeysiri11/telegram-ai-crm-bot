/**
 * Sprint 30.9 — Client tenant / auth request validation helpers.
 * Complements apiClient headers — does not replace server tenant_scope.
 */

import { getIdentityContext } from "@/integrations/apiClient";

export type TenantValidationResult = {
  ok: boolean;
  reasons: string[];
  tenantId: string | null;
  organization: string | null;
  hasBearer: boolean;
};

export function validateTenantContext(): TenantValidationResult {
  const ctx = getIdentityContext();
  const reasons: string[] = [];
  if (!ctx.tenantId && !ctx.organization) reasons.push("missing_tenant");
  if (!ctx.accessToken) reasons.push("missing_bearer");
  if (!ctx.userId && !ctx.email) reasons.push("missing_principal");
  return {
    ok: reasons.length === 0,
    reasons,
    tenantId: ctx.tenantId,
    organization: ctx.organization || null,
    hasBearer: Boolean(ctx.accessToken),
  };
}

/** Assert caller may only act within current tenant (cross-tenant guard for client ops). */
export function assertSameTenant(resourceTenantId: string | null | undefined): void {
  const ctx = getIdentityContext();
  const elevated =
    ctx.roleId === "owner" ||
    ctx.roleId === "platform_owner" ||
    ctx.roleId === "administrator" ||
    ctx.permissions.includes("*") ||
    ctx.permissions.includes("admin");
  if (elevated) return;
  const current = ctx.tenantId || ctx.organization;
  if (!resourceTenantId || !current) return;
  if (resourceTenantId !== current && resourceTenantId !== ctx.organization) {
    throw new Error("tenant_isolation: cross-tenant access denied");
  }
}

export function sanitizeApiErrorMessage(message: string): string {
  return message
    .replace(/Bearer\s+[A-Za-z0-9._\-]+/gi, "Bearer [redacted]")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[email]")
    .replace(/sk-[A-Za-z0-9]{10,}/g, "[secret]");
}
