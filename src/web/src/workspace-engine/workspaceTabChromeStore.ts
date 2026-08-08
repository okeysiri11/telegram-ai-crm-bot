/**
 * Sprint 42.6 — Developer opt-in for the duplicate workspace tab strip.
 * Default OFF for every role. Only visible when viewMode === developer AND enabled.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";

export const WORKSPACE_TAB_CHROME_KEY = wsKey("ewp_workspace_tab_chrome_v1");

function loadEnabled(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    return localStorage.getItem(WORKSPACE_TAB_CHROME_KEY) === "1";
  } catch {
    return false;
  }
}

type State = {
  /** Technical tab strip preference (Developer Mode only). Default false. */
  enabled: boolean;
  setEnabled: (v: boolean) => void;
  toggle: () => void;
};

export const useWorkspaceTabChromeStore = create<State>((set, get) => ({
  enabled: typeof localStorage !== "undefined" ? loadEnabled() : false,
  setEnabled: (v) => {
    try {
      localStorage.setItem(WORKSPACE_TAB_CHROME_KEY, v ? "1" : "0");
    } catch {
      /* ignore */
    }
    set({ enabled: v });
  },
  toggle: () => get().setEnabled(!get().enabled),
}));

/** Gate used by FullLayout — Owner/Admin/Manager/Client never see the strip. */
export function shouldShowWorkspaceTabBar(viewMode: string, enabled: boolean): boolean {
  return viewMode === "developer" && enabled;
}
