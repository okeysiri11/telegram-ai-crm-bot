/**
 * External pilot onboarding + invitation audit — Sprint 32.1.
 * Extends 32.0 web completion without new ecosystems.
 */

export type WorkspaceAuditItem = {
  id: string;
  label: string;
  route: string;
  healthUrl: string;
  expects: string[];
};

/** Primary health probes for each live workspace (existing domain APIs only). */
export const WORKSPACE_HEALTH_PROBES: WorkspaceAuditItem[] = [
  {
    id: "auto",
    label: "Automotive",
    route: "/workspace/auto",
    healthUrl: "/api/auto/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "beauty",
    label: "Beauty",
    route: "/workspace/beauty",
    healthUrl: "/api/enterprise-bos/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "cafe",
    label: "Cafe",
    route: "/workspace/cafe",
    healthUrl: "/api/enterprise-cos/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "agro",
    label: "Agriculture",
    route: "/workspace/agro",
    healthUrl: "/api/agro/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "legal",
    label: "Legal",
    route: "/workspace/legal",
    healthUrl: "/api/legal-enterprise/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "crypto",
    label: "Bidex",
    route: "/workspace/crypto",
    healthUrl: "/api/finance-da/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
  {
    id: "drone",
    label: "Drone",
    route: "/workspace/drone",
    healthUrl: "/api/drone/v1/health",
    expects: ["navigation", "permissions", "loading", "empty", "error", "forms", "tables", "dashboard"],
  },
];

export const PLATFORM_HEALTH_PROBES = [
  { id: "obs", label: "Observability", healthUrl: "/api/enterprise-obs/v1/health" },
  { id: "epd", label: "Production Readiness", healthUrl: "/api/enterprise-epd/v1/health" },
  { id: "epr", label: "Pilot Readiness", healthUrl: "/api/enterprise-epr/v1/health" },
  { id: "mc", label: "Mission Control", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "isam", label: "Authentication", healthUrl: "/api/enterprise-isam/v1/health" },
  { id: "tenancy", label: "Tenancy", healthUrl: "/api/enterprise-tenancy/v1/health" },
  { id: "eon", label: "Onboarding", healthUrl: "/api/enterprise-eon/v1/health" },
  { id: "esh", label: "Secrets (ESH)", healthUrl: "/api/enterprise-esh/v1/health" },
  { id: "erl", label: "Release / DR (ERL)", healthUrl: "/api/enterprise-erl/v1/health" },
  { id: "ecosystem", label: "Ecosystem Identity", healthUrl: "/api/ecosystem/v1/health" },
] as const;

export const PRODUCTION_CHECKLIST = [
  { id: "auth", label: "Authentication (ISAM / JWT)", status: "ready" as const },
  { id: "rbac", label: "Authorization / RBAC", status: "ready" as const },
  { id: "gateway", label: "API Gateway", status: "ready" as const },
  { id: "cache", label: "Caching (existing stores)", status: "ready" as const },
  { id: "logging", label: "Centralized logging (OBS)", status: "ready" as const },
  { id: "audit", label: "Audit trail", status: "ready" as const },
  { id: "monitoring", label: "Monitoring / OBS", status: "ready" as const },
  { id: "backups", label: "Backups (drill documented)", status: "partial" as const },
  { id: "health", label: "Health checks", status: "ready" as const },
  { id: "rate_limit", label: "Rate limiting", status: "ready" as const },
  { id: "secrets", label: "Secrets / env (ESH probed)", status: "ready" as const },
  { id: "pilot_invite", label: "Pilot invitation UI", status: "ready" as const },
  { id: "tenant_onboard", label: "External tenant onboarding", status: "ready" as const },
] as const;

export const IDENTITY_HARDENING_CHECKLIST = [
  { id: "invite_tokens", label: "Invitation tokens", status: "ready" as const },
  { id: "password_reset", label: "Password reset pages", status: "partial" as const },
  { id: "email_verify", label: "Email verification", status: "partial" as const },
  { id: "jwt_rotation", label: "JWT refresh / rotation", status: "ready" as const },
  { id: "session_expiry", label: "Session expiration", status: "ready" as const },
  { id: "multi_org", label: "Multi-organization access", status: "ready" as const },
  { id: "permissions", label: "Permission validation", status: "ready" as const },
  { id: "audit_log", label: "Audit logging", status: "ready" as const },
] as const;

export const PILOT_OPS_STEPS: {
  id: string;
  label: string;
  route: string;
  note?: string;
}[] = [
  { id: "org", label: "Organization onboarding", route: "/pilot/onboard" },
  { id: "workspace", label: "Workspace creation", route: "/workspace" },
  { id: "invite", label: "User invitation", route: "/pilot/invite" },
  { id: "accept", label: "Accept invitation", route: "/invite/accept" },
  { id: "role", label: "Role assignment", route: "/identity/roles" },
  { id: "login", label: "First login", route: "/login" },
  { id: "business", label: "Business activation", route: "/pilot/onboard" },
  { id: "ai", label: "AI activation", route: "/platform-builder/ai-team" },
];

export const ONBOARDING_ECOSYSTEMS = [
  { id: "auto", label: "Automotive", route: "/workspace/auto" },
  { id: "beauty", label: "Beauty", route: "/workspace/beauty" },
  { id: "cafe", label: "Cafe", route: "/workspace/cafe" },
  { id: "agro", label: "Agriculture", route: "/workspace/agro" },
  { id: "legal", label: "Legal", route: "/workspace/legal" },
  { id: "crypto", label: "Bidex", route: "/workspace/crypto" },
  { id: "drone", label: "Drone", route: "/workspace/drone" },
] as const;

export function webCompletionSummary() {
  return {
    ecosystems: WORKSPACE_HEALTH_PROBES.length,
    workspaceRoutes: WORKSPACE_HEALTH_PROBES.map((w) => w.route),
    platformProbes: PLATFORM_HEALTH_PROBES.length,
    productionItems: PRODUCTION_CHECKLIST.length,
    readyCount: PRODUCTION_CHECKLIST.filter((c) => c.status === "ready").length,
    partialCount: PRODUCTION_CHECKLIST.filter((c) => c.status === "partial").length,
    gapCount: PRODUCTION_CHECKLIST.filter((c) => (c.status as string) === "gap").length,
  };
}

/** Rough production readiness score 0–100 from checklist weights. */
export function productionReadinessScore(): number {
  const weights = { ready: 1, partial: 0.55, gap: 0 };
  const total = PRODUCTION_CHECKLIST.length;
  const sum = PRODUCTION_CHECKLIST.reduce((acc, c) => acc + weights[c.status], 0);
  return Math.round((sum / total) * 1000) / 10;
}

export function identityHardeningScore(): number {
  const weights = { ready: 1, partial: 0.55, gap: 0 };
  const total = IDENTITY_HARDENING_CHECKLIST.length;
  const sum = IDENTITY_HARDENING_CHECKLIST.reduce((acc, c) => acc + weights[c.status], 0);
  return Math.round((sum / total) * 1000) / 10;
}
