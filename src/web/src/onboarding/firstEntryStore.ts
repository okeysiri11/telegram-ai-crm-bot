/**
 * First-entry progress — Sprint 32.3.1.
 * Client persistence only; does not replace tenancy/EON/EPR engines.
 */

import type { FirstEntryStepId } from "./firstEntryRoles";

const KEY = "ewp_first_entry_v1";

export type FirstEntryState = {
  completed: boolean;
  step: FirstEntryStepId;
  roleId: string;
  companyName: string;
  country: string;
  timezone: string;
  language: string;
  currency: string;
  industry: string;
  teamSize: string;
  logoDataUrl: string;
  workspaceId: string;
  aiTeamMode: "ready" | "custom" | "";
  conciergeName: string;
  conciergeAvatar: string;
  conciergeVoice: string;
  conciergeStyle: string;
  conciergeLanguage: string;
  updatedAt: string;
};

const DEFAULTS: FirstEntryState = {
  completed: false,
  step: "welcome",
  roleId: "",
  companyName: "",
  country: "UA",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  language: "ru",
  currency: "UAH",
  industry: "other",
  teamSize: "2-10",
  logoDataUrl: "",
  workspaceId: "",
  aiTeamMode: "",
  conciergeName: "",
  conciergeAvatar: "avatar_guide",
  conciergeVoice: "warm",
  conciergeStyle: "professional",
  conciergeLanguage: "ru",
  updatedAt: "",
};

export function loadFirstEntry(): FirstEntryState {
  try {
    return { ...DEFAULTS, ...(JSON.parse(localStorage.getItem(KEY) || "{}") as Partial<FirstEntryState>) };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveFirstEntry(patch: Partial<FirstEntryState>): FirstEntryState {
  const next = {
    ...loadFirstEntry(),
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function isFirstEntryComplete(): boolean {
  return loadFirstEntry().completed === true;
}

export function resetFirstEntry(): FirstEntryState {
  localStorage.removeItem(KEY);
  return saveFirstEntry({ ...DEFAULTS, completed: false, step: "welcome" });
}

export function markFirstEntryComplete(): FirstEntryState {
  return saveFirstEntry({ completed: true, step: "dashboard" });
}
