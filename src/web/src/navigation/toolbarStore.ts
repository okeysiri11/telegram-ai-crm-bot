/**
 * Sprint 41.3 — top toolbar expand/collapse preference.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";

export const TOOLBAR_KEY = wsKey("ewp_toolbar_collapsed_v1");

type ToolbarState = {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  toggle: () => void;
};

function read(): boolean {
  try {
    return localStorage.getItem(TOOLBAR_KEY) === "1";
  } catch {
    return false;
  }
}

export const useToolbarStore = create<ToolbarState>((set, get) => ({
  collapsed: typeof localStorage !== "undefined" ? read() : false,
  setCollapsed: (v) => {
    try {
      localStorage.setItem(TOOLBAR_KEY, v ? "1" : "0");
    } catch {
      /* ignore */
    }
    set({ collapsed: v });
  },
  toggle: () => get().setCollapsed(!get().collapsed),
}));
