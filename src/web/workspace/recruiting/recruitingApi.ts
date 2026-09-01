/**
 * Canonical authenticated Recruiting Ops client.
 * Browser → same-origin /api/recruiting-ops/v1 → session JWT (apiFetch) → Recruiting Ops.
 * Secrets stay server-side. Never expose JWT or ingest secrets in this module.
 *
 * Owner JWT/org-selector often uses demo-corp while Vanguard HMAC ingest writes to ados.
 * recruitingWorkspaceHeaders maps that read identity without putting secrets in the browser.
 */

export {
  asList,
  pick,
  recruitingOpsFirstError,
  recruitingOpsGet,
  recruitingOpsPost,
  recruitingOpsPrefix,
  recruitingOpsUserError,
} from "../business-ops/opsApi";
export type { OpsResult } from "../business-ops/opsApi";

/** Canonical Vanguard ingest organization. Must match server VANGUARD_ORGANIZATION_ID default. */
export const VANGUARD_INGEST_ORGANIZATION_ID = "ados";

const OWNER_ROLES = new Set(["platform_owner", "owner"]);
const VANGUARD_READ_ALIASES = new Set(["ados", "demo-corp", "default", ""]);

export function recruitingReadOrganizationId(uiOrganizationId: string, recruitingRole: string): string {
  const requested = (uiOrganizationId || "").trim();
  if (OWNER_ROLES.has(recruitingRole) && VANGUARD_READ_ALIASES.has(requested)) {
    return VANGUARD_INGEST_ORGANIZATION_ID;
  }
  return requested || VANGUARD_INGEST_ORGANIZATION_ID;
}

export function recruitingWorkspaceHeaders(
  organizationId: string,
  recruitingRole: string,
): Record<string, string> {
  const readOrg = recruitingReadOrganizationId(organizationId, recruitingRole);
  return {
    "X-Organization-Id": readOrg,
    "X-Recruiting-Organization-Id": readOrg,
    "X-Role": recruitingRole,
  };
}
