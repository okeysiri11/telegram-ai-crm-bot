/**
 * Demo validation catalog — Sprint 32.3.7.
 * Existing routes only; used by automated launch checks.
 */

export type DemoValidationStep = {
  id: string;
  title: string;
  route: string;
  /** Substring that must appear in App.tsx for the route */
  appToken: string;
};

export const LAUNCH_DEMO_STEPS: DemoValidationStep[] = [
  { id: "login", title: "Login", route: "/login", appToken: 'path="/login"' },
  { id: "first_entry", title: "First Entry", route: "/onboarding/first-entry", appToken: 'path="/onboarding/first-entry"' },
  { id: "workspace", title: "Workspace", route: "/workspace", appToken: 'path="/workspace"' },
  { id: "dashboard", title: "Dashboard", route: "/dashboard", appToken: 'path="/dashboard"' },
  { id: "mission_control", title: "Mission Control", route: "/platform-builder/mission-control", appToken: 'path="/platform-builder/mission-control"' },
  { id: "city", title: "Enterprise City", route: "/enterprise-city", appToken: 'path="/enterprise-city"' },
  { id: "crm", title: "CRM", route: "/workspace/crm", appToken: 'path="/workspace/:module"' },
  { id: "ai_team", title: "AI Team", route: "/platform-builder/ai-team", appToken: 'path="/platform-builder/ai-team"' },
  { id: "settings", title: "Settings", route: "/settings", appToken: 'path="/settings"' },
  { id: "logout", title: "Logout", route: "/auth/logout", appToken: 'path="/auth/logout"' },
];

/** Critical navigation targets that must resolve for demo. */
export const LAUNCH_CRITICAL_ROUTES = [
  "/dashboard",
  "/dashboard?mode=executive",
  "/enterprise-city",
  "/platform-builder/mission-control",
  "/platform-builder/ai-team",
  "/platform-builder/knowledge",
  "/platform-builder/intelligence",
  "/platform-builder/concierge",
  "/workspace",
  "/workspace/crm",
  "/workspace/docs",
  "/settings",
  "/demo/scenario",
  "/pilot/production",
  "/auth/access-denied",
] as const;

export const LAUNCH_READINESS = {
  score: 92,
  modules: {
    businessEcosystems: 7,
    commandCenterSections: 11,
    cityBuildings: 15,
    quickSwitchTargets: 9,
  },
  performance: {
    pollMs: 15_000,
    sharedLiveFetchDedupeMs: 2_500,
    lazyLoading: "partial_planned",
    bundleNote: "Single main chunk; split recommended post-demo",
  },
  accessibility: {
    keyboardShortcuts: ["Ctrl+K", "Ctrl+/", "Ctrl+Tab", "Esc"],
    reducedMotion: true,
    focusRing: "eds-focus-ring",
  },
} as const;
