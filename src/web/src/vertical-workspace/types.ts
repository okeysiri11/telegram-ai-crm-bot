/**
 * Sprint 42.8 — Universal Vertical Workspace Framework types.
 */

export type VerticalNavItem = {
  id: string;
  label: string;
  /** Optional deep link into existing module; default /vertical/:vid/:id */
  href?: string;
};

export type VerticalAgent = {
  id: string;
  name: string;
  role: string;
};

export type VerticalStat = {
  label: string;
  value: string;
};

export type VerticalAction = {
  label: string;
  route: string;
};

export type VerticalDef = {
  id: string;
  label: string;
  /** Short subtitle under title */
  purpose: string;
  /** Home path for switcher */
  route: string;
  /** Optional legacy deep surface (live workflow) */
  legacyRoute?: string;
  nav: VerticalNavItem[];
  agents: VerticalAgent[];
  stats: VerticalStat[];
  quickActions: VerticalAction[];
  recommendations: string[];
  primaryAction: VerticalAction;
  recentObjects: Array<{ title: string; detail: string; route?: string }>;
  events: Array<{ title: string; detail: string }>;
  tasks: Array<{ title: string; status: string }>;
  aiGuide: {
    greeting: string;
    bullets: string[];
    recommendedAction: VerticalAction;
  };
};
