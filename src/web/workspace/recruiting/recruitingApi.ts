/**
 * Canonical authenticated Recruiting Ops client.
 * Browser → same-origin /api/recruiting-ops/v1 → session JWT (apiFetch) → Recruiting Ops.
 * Secrets stay server-side. Never expose JWT or ingest secrets in this module.
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
