/**
 * Sprint 30.2 — organization (company) selector for top bar.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import { ORG_SELECTOR_OPTIONS } from "./enterpriseRuNav";

const STORAGE_KEY = wsKey("ewp_org_selector_v1");

function loadOrg(): string {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return raw;
  } catch {
    /* ignore */
  }
  return "ados";
}

type OrgState = {
  organizationId: string;
  setOrganization: (id: string) => void;
  options: () => typeof ORG_SELECTOR_OPTIONS;
  label: () => string;
};

export const useOrgSelector = create<OrgState>((set, get) => ({
  organizationId: typeof localStorage !== "undefined" ? loadOrg() : "ados",
  setOrganization: (id) => {
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* ignore */
    }
    set({ organizationId: id });
  },
  options: () => ORG_SELECTOR_OPTIONS,
  label: () =>
    ORG_SELECTOR_OPTIONS.find((o) => o.id === get().organizationId)?.label ||
    get().organizationId,
}));
