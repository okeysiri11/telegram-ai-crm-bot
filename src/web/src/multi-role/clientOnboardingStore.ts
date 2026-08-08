/**
 * Sprint 42.1 — 6-step client onboarding wizard state.
 */

import { wsKey } from "./workspaceSlot";

export const CLIENT_ONBOARDING_KEY = "ewp_client_onboarding_v1";

export type ClientOnboardingStep =
  | "welcome"
  | "company"
  | "business"
  | "modules"
  | "import"
  | "finish";

export type ClientOnboardingState = {
  completed: boolean;
  step: ClientOnboardingStep;
  companyName: string;
  businessType: string;
  modules: string[];
  importChoice: "skip" | "demo" | "file";
  updatedAt: string;
};

const DEFAULTS: ClientOnboardingState = {
  completed: false,
  step: "welcome",
  companyName: "",
  businessType: "",
  modules: ["crm", "documents", "analytics", "tasks", "knowledge"],
  importChoice: "demo",
  updatedAt: "",
};

export const CLIENT_ONBOARDING_STEPS: ClientOnboardingStep[] = [
  "welcome",
  "company",
  "business",
  "modules",
  "import",
  "finish",
];

export function loadClientOnboarding(): ClientOnboardingState {
  try {
    return {
      ...DEFAULTS,
      ...(JSON.parse(localStorage.getItem(wsKey(CLIENT_ONBOARDING_KEY)) || "{}") as Partial<ClientOnboardingState>),
    };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveClientOnboarding(patch: Partial<ClientOnboardingState>): ClientOnboardingState {
  const next = {
    ...loadClientOnboarding(),
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(wsKey(CLIENT_ONBOARDING_KEY), JSON.stringify(next));
  return next;
}

export function isClientOnboardingComplete(): boolean {
  return loadClientOnboarding().completed === true;
}

export function markClientOnboardingComplete(patch: Partial<ClientOnboardingState> = {}): ClientOnboardingState {
  return saveClientOnboarding({ ...patch, completed: true, step: "finish" });
}

export function resetClientOnboarding(): ClientOnboardingState {
  localStorage.removeItem(wsKey(CLIENT_ONBOARDING_KEY));
  return saveClientOnboarding({ ...DEFAULTS, completed: false, step: "welcome" });
}
