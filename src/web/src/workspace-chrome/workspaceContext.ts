/**
 * Unified workspace context helpers — Sprint 32.3.6.
 * Reads existing stores / path; no new Workspace Engine.
 */

import { moduleRegistry } from "../../workspace/managers/moduleRegistry";

export type QuickSwitchItem = {
  id: string;
  label: string;
  route: string;
  hint: string;
};

/** Enterprise OS quick switch — existing routes only. */
export const GLOBAL_QUICK_SWITCH: QuickSwitchItem[] = [
  { id: "dashboard", label: "Dashboard", route: "/dashboard", hint: "CC" },
  { id: "mission_control", label: "Mission Control", route: "/platform-builder/mission-control", hint: "MC" },
  { id: "city", label: "Enterprise City", route: "/enterprise-city", hint: "City" },
  { id: "crm", label: "CRM", route: "/workspace/crm", hint: "CRM" },
  { id: "analytics", label: "Analytics", route: "/platform-builder/intelligence", hint: "BI" },
  { id: "documents", label: "Documents", route: "/workspace/docs", hint: "Docs" },
  { id: "ai_team", label: "AI Team", route: "/platform-builder/ai-team", hint: "AI" },
  { id: "knowledge", label: "Knowledge", route: "/platform-builder/knowledge", hint: "KB" },
  { id: "settings", label: "Settings", route: "/settings", hint: "Cfg" },
];

const ECOSYSTEM_LABELS: Record<string, string> = {
  auto: "Automotive",
  beauty: "Beauty",
  cafe: "Cafe",
  agro: "Agriculture",
  legal: "Legal",
  crypto: "Bidex",
  drone: "Drone",
};

const LABEL_OVERRIDES: Record<string, string> = {
  dashboard: "Dashboard",
  "enterprise-city": "Enterprise City",
  "platform-builder": "Platform Builder",
  "mission-control": "Mission Control",
  "ai-team": "AI Team",
  crm: "CRM",
  docs: "Documents",
  documents: "Documents",
  finance: "Finance",
  hr: "HR",
  settings: "Settings",
  onboarding: "Onboarding",
  "first-entry": "First Entry",
  demo: "Demo",
  scenario: "Scenario",
  workspace: "Workspace",
  intelligence: "Analytics",
  knowledge: "Knowledge",
  concierge: "AI Concierge",
  ...ECOSYSTEM_LABELS,
};

export function labelForSegment(segment: string): string {
  const key = segment.toLowerCase();
  if (LABEL_OVERRIDES[key]) return LABEL_OVERRIDES[key];
  try {
    const meta = moduleRegistry.resolve(key);
    if (meta?.title) return meta.title;
  } catch {
    /* ignore */
  }
  return segment.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function detectActiveEcosystem(pathname: string): string | null {
  const parts = pathname.split("/").filter(Boolean);
  const wsIdx = parts.indexOf("workspace");
  if (wsIdx >= 0 && parts[wsIdx + 1]) {
    const id = parts[wsIdx + 1]!;
    if (moduleRegistry.ecosystems().includes(id as never)) {
      return ECOSYSTEM_LABELS[id] || id;
    }
  }
  for (const eco of moduleRegistry.ecosystems()) {
    if (pathname.includes(`/${eco}`)) return ECOSYSTEM_LABELS[eco] || eco;
  }
  return null;
}

export function workspaceStatusLabel(activeModules: string[]): string {
  if (!activeModules.length) return "Idle";
  return activeModules.length >= 4 ? "Operational" : "Partial";
}
