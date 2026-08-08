/**
 * Sprint 42.1 — apply demo user session (view mode, org, seed, role home).
 */

import { demoUserByEmail, type DemoUserDef } from "./demoUsers";
import { useViewModeStore } from "@/ux-revolution/viewModeStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useI18n } from "@/i18n";
import { applyGlobeFlySession } from "@/demo/globefly";
import { seedClientDemoData } from "./clientDemoSeed";
import { markClientOnboardingComplete } from "./clientOnboardingStore";

export function applyDemoUserSession(email: string): DemoUserDef | undefined {
  const user = demoUserByEmail(email);
  if (!user) {
    // GlobeFly fallback
    applyGlobeFlySession(email);
    return undefined;
  }

  try {
    useOrgSelector.getState().setOrganization(user.tenantId);
  } catch {
    /* ignore */
  }
  try {
    localStorage.setItem("ewp_company_label_v1", user.company);
  } catch {
    /* ignore */
  }
  try {
    useI18n.getState().setLocale("ru");
  } catch {
    /* ignore */
  }

  useViewModeStore.getState().setViewMode(user.viewMode);
  const primaryRole = user.roleIds[0] || "client";
  useRoleSwitcher.getState().setRole(primaryRole);

  if (user.viewMode === "client" || user.homeRole === "client") {
    seedClientDemoData(user);
    // Returning clients skip wizard when already completed; first time keeps wizard.
  }

  return user;
}

/** One-click Client Demo Mode — loads seeded workspace as travel client. */
export function openClientDemoWorkspace(): { email: string; password: string; tenantId: string } {
  const travel = demoUserByEmail("travel@globefly.demo")!;
  seedClientDemoData(travel);
  markClientOnboardingComplete({
    companyName: travel.company,
    businessType: travel.businessType,
    modules: travel.modules,
  });
  useViewModeStore.getState().setViewMode("client");
  useRoleSwitcher.getState().setRole("client");
  try {
    useOrgSelector.getState().setOrganization(travel.tenantId);
    localStorage.setItem("ewp_company_label_v1", travel.company);
  } catch {
    /* ignore */
  }
  return { email: travel.email, password: travel.password, tenantId: travel.tenantId };
}
