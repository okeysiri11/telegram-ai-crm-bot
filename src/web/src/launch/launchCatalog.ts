/**
 * Demo validation catalog — Sprint 32.3.7 / EP-08 GA path.
 * Existing routes only; used by automated launch checks.
 */

export type DemoValidationStep = {
  id: string;
  title: string;
  route: string;
  /** Substring that must appear in App.tsx for the route */
  appToken: string;
};

/** Canonical pilot / commercial validation path (EP-08). */
export const LAUNCH_DEMO_STEPS: DemoValidationStep[] = [
  { id: "login", title: "Login", route: "/login", appToken: 'path="/login"' },
  { id: "first_entry", title: "First Entry", route: "/onboarding/first-entry", appToken: 'path="/onboarding/first-entry"' },
  { id: "dashboard", title: "Dashboard · Morning Brief", route: "/dashboard", appToken: 'path="/dashboard"' },
  { id: "city", title: "Enterprise City", route: "/enterprise-city", appToken: 'path="/enterprise-city"' },
  { id: "mission_control", title: "Mission Control", route: "/platform-builder/mission-control", appToken: 'path="/platform-builder/mission-control"' },
  { id: "concierge", title: "AI Concierge", route: "/platform-builder/concierge", appToken: 'path="/platform-builder/concierge"' },
  { id: "control_tower", title: "Control Tower", route: "/platform-builder/control-tower", appToken: 'path="/platform-builder/control-tower"' },
  { id: "settings", title: "Settings", route: "/settings", appToken: 'path="/settings"' },
  { id: "workspace", title: "Workspace", route: "/workspace", appToken: 'path="/workspace"' },
  { id: "crm", title: "CRM", route: "/workspace/crm", appToken: 'path="/workspace/:module"' },
  { id: "logout", title: "Logout", route: "/auth/logout", appToken: 'path="/auth/logout"' },
];

/** Critical navigation targets that must resolve for demo / pilot. */
export const LAUNCH_CRITICAL_ROUTES = [
  "/dashboard",
  "/dashboard?mode=executive",
  "/enterprise-city",
  "/platform-builder/mission-control",
  "/platform-builder/control-tower",
  "/platform-builder/concierge",
  "/platform-builder/ai-team",
  "/platform-builder/knowledge",
  "/platform-builder/intelligence",
  "/workspace",
  "/workspace/crm",
  "/workspace/docs",
  "/settings",
  "/demo/scenario",
  "/pilot/production",
  "/auth/access-denied",
] as const;

export const LAUNCH_READINESS = {
  score: 97,
  gaCertified: true,
  modules: {
    businessEcosystems: 7,
    commandCenterSections: 11,
    cityBuildings: 15,
    quickSwitchTargets: 9,
  },
  performance: {
    pollMs: 20_000,
    sharedLiveFetchDedupeMs: 4_000,
    singletonLivePoller: true,
    pauseWhenHidden: true,
    apiTimeoutMs: 20_000,
    lazyLoading: "route_level_partial",
    bundleNote: "Shared live poller; socket listeners bound once",
  },
  reliability: {
    errorBoundary: true,
    offlineBanner: true,
    reconnectPublish: true,
    sanitizedErrors: true,
  },
  accessibility: {
    keyboardShortcuts: ["Ctrl+K", "Ctrl+/", "Ctrl+Tab", "Esc"],
    reducedMotion: true,
    focusRing: "eds-focus-ring",
  },
  commercial: {
    morningBrief: true,
    decisionContinueStrip: true,
    cityGlance: true,
    advisorPersonality: true,
    demoScenarioGaPath: true,
  },
} as const;
