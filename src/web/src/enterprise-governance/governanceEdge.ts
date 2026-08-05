/**
 * API Edge Governance — extension points (Sprint 1.1.1).
 * No new Engine. Documents + hooks for Policy → Permission → Approval → Execution
 * to move from UI composition toward API-edge checks (Roadmap 2.0).
 */

export type GovernanceDecision = "allow" | "deny" | "require_approval";

export type GovernanceEdgeContext = {
  action: string;
  resource?: string;
  roleId?: string;
  permissions?: string[];
  tenantId?: string;
  correlationId?: string;
};

export type GovernanceEdgeResult = {
  decision: GovernanceDecision;
  policyId?: string;
  reason: string;
  /** When require_approval — suggested approval category */
  approvalCategory?: string;
  /** Extension: server may attach request id for HITL */
  approvalRequestId?: string;
};

export type GovernanceEdgeHook = (
  ctx: GovernanceEdgeContext,
) => GovernanceEdgeResult | Promise<GovernanceEdgeResult>;

/** Default compositional check — mirrors UI Governance severity (not hard enforcement). */
export const defaultGovernanceEdgeHook: GovernanceEdgeHook = (ctx) => {
  const perms = ctx.permissions || [];
  if (ctx.action.startsWith("admin.") && !perms.includes("admin") && ctx.roleId !== "owner") {
    return {
      decision: "require_approval",
      policyId: "edge.admin_sensitive",
      reason: "Sensitive admin action requires owner approval (compositional edge stub).",
      approvalCategory: "admin",
    };
  }
  return {
    decision: "allow",
    policyId: "edge.default_allow",
    reason: "No blocking policy matched (UI Governance still authoritative until API edge lands).",
  };
};

let activeHook: GovernanceEdgeHook = defaultGovernanceEdgeHook;

/** Register a custom edge evaluator (tests / future API gateway adapter). */
export function registerGovernanceEdgeHook(hook: GovernanceEdgeHook): void {
  activeHook = hook;
}

export function resetGovernanceEdgeHook(): void {
  activeHook = defaultGovernanceEdgeHook;
}

export async function evaluateGovernanceEdge(
  ctx: GovernanceEdgeContext,
): Promise<GovernanceEdgeResult> {
  return activeHook(ctx);
}

export const GOVERNANCE_EDGE_MIGRATION = {
  version: "1.1.1",
  phases: [
    "document_extension_points",
    "client_precheck_hooks",
    "api_gateway_middleware",
    "hard_deny_on_critical",
  ] as const,
  currentPhase: "client_precheck_hooks" as const,
  note: "Hard API enforcement is Roadmap 2.0 — see docs/API_EDGE_GOVERNANCE_PLAN.md",
};
