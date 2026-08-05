/**
 * Sprint 32.5 — Closed Beta surface map (launch readiness, no new engines).
 * Collision: Enterprise Intelligence also uses sprint id 32.5 — see SPRINT_32_5_RESULT.md.
 */

export const CLOSED_BETA_SURFACES = [
  { id: "auth", label: "Authentication", route: "/login" },
  { id: "register", label: "Registration", route: "/auth/register" },
  { id: "google", label: "Google Login", route: "/login" },
  { id: "first_run", label: "First Run Wizard", route: "/onboarding/first-entry" },
  { id: "owner", label: "Owner Dashboard", route: "/owner" },
  { id: "admin", label: "Admin Dashboard", route: "/admin" },
  { id: "manager", label: "Manager Dashboard", route: "/dashboards/manager" },
  { id: "employee", label: "Employee Dashboard", route: "/dashboards/employee" },
  { id: "client", label: "Client Dashboard", route: "/dashboards/client" },
  { id: "dealer", label: "Dealer Dashboard", route: "/dashboards/dealer" },
  { id: "crm", label: "CRM", route: "/crm" },
  { id: "projects", label: "Projects", route: "/projects" },
  { id: "knowledge", label: "Knowledge", route: "/knowledge" },
  { id: "calendar", label: "Calendar", route: "/calendar" },
  { id: "notifications", label: "Notifications", route: "/notifications" },
  { id: "drive", label: "Enterprise Drive", route: "/documents" },
  { id: "marketplace", label: "Marketplace", route: "/marketplace" },
  { id: "ai_studio", label: "AI Studio", route: "/ai-studio" },
  { id: "production", label: "Production Studio", route: "/production-studio" },
  { id: "city", label: "Enterprise City", route: "/city" },
  { id: "enterprise_city", label: "Enterprise City (alias)", route: "/enterprise-city" },
  { id: "runtime", label: "AI Runtime", route: "/platform-builder/runtime" },
  { id: "agents", label: "AI Agents", route: "/ai-agents" },
  { id: "orchestrator", label: "Orchestrator", route: "/orchestrator" },
  { id: "command", label: "Command Palette", route: "/command-center" },
  { id: "security", label: "Security Center", route: "/identity/security" },
  { id: "settings", label: "Settings", route: "/settings" },
  { id: "profile", label: "User Profile", route: "/identity/profile" },
  { id: "health", label: "Health", route: "/health" },
  { id: "search", label: "Global Search", route: "/search" },
] as const;

export const CLOSED_BETA_VERSION = "32.5-closed-beta";
export const CLOSED_BETA_META = {
  sprint: "32.5",
  track: "Closed Beta Launch Preparation",
  collisionNote: "Enterprise Intelligence also uses Sprint 32.5 numbering",
  defaultLocale: "ru",
} as const;

export function assertClosedBetaSurfacesReachable(registered: string[]): {
  ok: boolean;
  missing: string[];
} {
  const set = new Set(registered);
  const missing = CLOSED_BETA_SURFACES.map((s) => s.route.split("?")[0]).filter((p) => !set.has(p));
  return { ok: missing.length === 0, missing: [...new Set(missing)] };
}
