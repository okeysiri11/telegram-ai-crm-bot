/**
 * Sprint 30.2 — in-app role switcher (view-as role for navigation).
 */

import { create } from "zustand";
import { ROLE_SWITCHER_OPTIONS, type RoleSwitcherOption } from "./enterpriseRuNav";

const STORAGE_KEY = "ewp_role_switcher_v1";

function loadRole(): string {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw && ROLE_SWITCHER_OPTIONS.some((o) => o.id === raw)) return raw;
  } catch {
    /* ignore */
  }
  return "owner";
}

type RoleSwitcherState = {
  activeRoleId: string;
  setRole: (roleId: string) => void;
  options: () => RoleSwitcherOption[];
  activeOption: () => RoleSwitcherOption | undefined;
  isOwnerView: () => boolean;
};

export const useRoleSwitcher = create<RoleSwitcherState>((set, get) => ({
  activeRoleId: typeof localStorage !== "undefined" ? loadRole() : "owner",
  setRole: (roleId) => {
    if (get().activeRoleId === roleId) return;
    if (ROLE_SWITCHER_OPTIONS.some((o) => o.id === roleId)) {
      try {
        localStorage.setItem(STORAGE_KEY, roleId);
      } catch {
        /* ignore */
      }
      set({ activeRoleId: roleId });
    }
  },
  options: () => ROLE_SWITCHER_OPTIONS,
  activeOption: () => ROLE_SWITCHER_OPTIONS.find((o) => o.id === get().activeRoleId),
  isOwnerView: () => get().activeRoleId === "owner",
}));

export function resolveRoleLabel(roleId: string | undefined | null): string {
  if (!roleId) return "Сотрудник";
  const hit = ROLE_SWITCHER_OPTIONS.find(
    (o) => o.id === roleId || o.roleIds.includes(roleId),
  );
  return hit?.label || roleId;
}
