/**
 * Sprint 41.1 — load GlobeFly demo into local UI stores after login.
 */

import { GLOBEFLY_STORAGE_KEY, GLOBEFLY_TENANT_ID, GLOBEFLY_ORG_LABEL } from "./tenant";
import { GLOBEFLY_SEED } from "./seedData";
import { globeFlyUserByEmail, isGlobeFlyEmail } from "./users";
import { useViewModeStore } from "@/ux-revolution";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useI18n } from "@/i18n";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";

export function persistGlobeFlySeed(): void {
  try {
    localStorage.setItem(GLOBEFLY_STORAGE_KEY, JSON.stringify(GLOBEFLY_SEED));
  } catch {
    /* ignore */
  }
}

export function readGlobeFlySeed(): typeof GLOBEFLY_SEED | null {
  try {
    const raw = localStorage.getItem(GLOBEFLY_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as typeof GLOBEFLY_SEED;
  } catch {
    return null;
  }
}

/** Apply View Mode, org, locale, and seed after a GlobeFly login. */
export function applyGlobeFlySession(email: string): void {
  if (!isGlobeFlyEmail(email)) return;
  persistGlobeFlySeed();
  useOrgSelector.getState().setOrganization(GLOBEFLY_TENANT_ID);
  useI18n.getState().setLocale("ru");
  const profile = globeFlyUserByEmail(email);
  const mode = profile?.defaultViewMode ?? "client";
  useViewModeStore.getState().setViewMode(mode);
  if (mode === "client") useRoleSwitcher.getState().setRole("client");
  else if (mode === "manager") useRoleSwitcher.getState().setRole("manager");
  else if (mode === "company_admin") useRoleSwitcher.getState().setRole("administrator");
  else if (mode === "platform_owner") useRoleSwitcher.getState().setRole("owner");
  else useRoleSwitcher.getState().setRole("administrator");
  try {
    localStorage.setItem("ewp_company_label_v1", GLOBEFLY_ORG_LABEL);
  } catch {
    /* ignore */
  }
}

export { GLOBEFLY_SEED, GLOBEFLY_TENANT_ID, GLOBEFLY_ORG_LABEL };
