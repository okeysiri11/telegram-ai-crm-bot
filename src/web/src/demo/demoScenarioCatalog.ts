/** Demo scenario catalog — Sprint 32.3.5 / EP-08 GA path. Existing routes only. */

export type DemoStep = {
  id: string;
  title: string;
  description: string;
  route: string;
  cta: string;
  duration: string;
};

/** Canonical commercial / pilot demo path (EP-08). */
export const DEMO_SCENARIO_STEPS: DemoStep[] = [
  {
    id: "login",
    title: "Login",
    description: "Secure enterprise entry · demo identity ready",
    route: "/login",
    cta: "Sign in",
    duration: "30 s",
  },
  {
    id: "first_entry",
    title: "Organization · First Entry",
    description: "Welcome → role → company → ready → Dashboard (AI defaults applied)",
    route: "/onboarding/first-entry",
    cta: "First Entry",
    duration: "2 min",
  },
  {
    id: "morning_brief",
    title: "Morning Brief",
    description: "Observation · Attention · Recommendation · Risks · Opportunities",
    route: "/dashboard?mode=executive",
    cta: "Morning Brief",
    duration: "1 min",
  },
  {
    id: "dashboard",
    title: "Dashboard",
    description: "Executive Decision Flow · KPI · Continue strip",
    route: "/dashboard?mode=executive",
    cta: "Dashboard",
    duration: "1 min",
  },
  {
    id: "city",
    title: "Enterprise City",
    description: "Company map · RU/UA states · one-glance health",
    route: "/enterprise-city",
    cta: "City",
    duration: "1 min",
  },
  {
    id: "mission_control",
    title: "Mission Control",
    description: "Live health · ops pulse",
    route: "/platform-builder/mission-control",
    cta: "Mission Control",
    duration: "1 min",
  },
  {
    id: "concierge",
    title: "AI Concierge · Advisor",
    description: "Top decisions · Observation / Why / Action / Impact",
    route: "/platform-builder/concierge",
    cta: "Ask Advisor",
    duration: "1 min",
  },
  {
    id: "control_tower",
    title: "Control Tower",
    description: "Owner escalations · decide now",
    route: "/platform-builder/control-tower",
    cta: "Decide",
    duration: "1 min",
  },
  {
    id: "settings",
    title: "Settings",
    description: "Notifications · preferences · profile",
    route: "/settings",
    cta: "Settings",
    duration: "45 s",
  },
  {
    id: "logout",
    title: "Logout",
    description: "Safe sign-out",
    route: "/auth/logout",
    cta: "Logout",
    duration: "15 s",
  },
];

export const GA_DEMO_VALUE = {
  product: "Enterprise Platform v1.0 GA",
  pitch:
    "Owner sees the company in 10 seconds, decides in one click, and acts without hunting navigation.",
  durationMin: 20,
  durationMax: 35,
} as const;
