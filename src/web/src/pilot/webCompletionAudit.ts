/**
 * Enterprise Web Completion audit — Sprint 32.0.
 * Validates seven workspaces + shared platform surfaces without new ecosystems.
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
] as const;

export const PRODUCTION_CHECKLIST = [
  { id: "auth", label: "Authentication (ISAM / JWT)", status: "ready" as const },
  { id: "rbac", label: "Authorization / RBAC", status: "ready" as const },
  { id: "gateway", label: "API Gateway", status: "ready" as const },
  { id: "cache", label: "Caching (existing stores)", status: "ready" as const },
  { id: "logging", label: "Centralized logging (OBS)", status: "ready" as const },
  { id: "audit", label: "Audit trail", status: "ready" as const },
  { id: "monitoring", label: "Monitoring / OBS", status: "ready" as const },
  { id: "backups", label: "Backups (documented)", status: "partial" as const },
  { id: "health", label: "Health checks", status: "ready" as const },
  { id: "rate_limit", label: "Rate limiting", status: "ready" as const },
  { id: "secrets", label: "Secrets / env config", status: "partial" as const },
  { id: "pilot_invite", label: "Pilot invitation UI", status: "gap" as const },
] as const;

export const PILOT_OPS_STEPS = [
  { id: "org", label: "Organization onboarding", route: "/pilot" },
  { id: "workspace", label: "Workspace creation", route: "/workspace" },
  { id: "invite", label: "User invitation", route: "/pilot", note: "API exists; web invite UI deferred" },
  { id: "role", label: "Role assignment", route: "/pilot" },
  { id: "login", label: "First login", route: "/login" },
  { id: "business", label: "Business activation", route: "/pilot" },
  { id: "ai", label: "AI activation", route: "/platform-builder/ai-team" },
] as const;

export function webCompletionSummary() {
  return {
    ecosystems: WORKSPACE_HEALTH_PROBES.length,
    workspaceRoutes: WORKSPACE_HEALTH_PROBES.map((w) => w.route),
    platformProbes: PLATFORM_HEALTH_PROBES.length,
    productionItems: PRODUCTION_CHECKLIST.length,
    readyCount: PRODUCTION_CHECKLIST.filter((c) => c.status === "ready").length,
    partialCount: PRODUCTION_CHECKLIST.filter((c) => c.status === "partial").length,
    gapCount: PRODUCTION_CHECKLIST.filter((c) => c.status === "gap").length,
  };
}

/** Rough production readiness score 0–100 from checklist weights. */
export function productionReadinessScore(): number {
  const weights = { ready: 1, partial: 0.55, gap: 0 };
  const total = PRODUCTION_CHECKLIST.length;
  const sum = PRODUCTION_CHECKLIST.reduce((acc, c) => acc + weights[c.status], 0);
  return Math.round((sum / total) * 1000) / 10;
}
