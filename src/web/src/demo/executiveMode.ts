/**
 * Executive Mode helpers — Sprint 32.3.5.
 * Condenses Command Center for leaders — not a new Dashboard Engine.
 */

import type { CommandWidgetId } from "@/dashboard/commandCenterCatalog";

export const EXECUTIVE_ROLE_IDS = new Set([
  "business_owner",
  "executive",
  "owner",
  "ceo",
  "platform_owner",
]);

/** Lean layout: KPI, health, AI, critical feed, recommendations — one screen. */
export const EXECUTIVE_LAYOUT: CommandWidgetId[] = [
  "mission_control",
  "enterprise_health",
  "business_kpi",
  "activity_feed",
  "ai_activity",
  "ai_recommendations",
];

export function isExecutiveRole(roleId?: string | null, roles?: string[] | null): boolean {
  if (roleId && EXECUTIVE_ROLE_IDS.has(roleId)) return true;
  if (roles?.some((r) => EXECUTIVE_ROLE_IDS.has(r))) return true;
  return false;
}

export function resolveExecutiveMode(opts: {
  queryMode?: string | null;
  roleId?: string | null;
  roles?: string[] | null;
  storedPref?: boolean | null;
}): boolean {
  if (opts.queryMode === "executive") return true;
  if (opts.queryMode === "full") return false;
  if (opts.storedPref === true) return true;
  if (opts.storedPref === false) return false;
  return isExecutiveRole(opts.roleId, opts.roles);
}

const PREF_KEY = "ewp_executive_mode_v1";

export function loadExecutivePref(): boolean | null {
  try {
    const v = localStorage.getItem(PREF_KEY);
    if (v === "1") return true;
    if (v === "0") return false;
  } catch {
    /* ignore */
  }
  return null;
}

export function saveExecutivePref(on: boolean) {
  localStorage.setItem(PREF_KEY, on ? "1" : "0");
}
