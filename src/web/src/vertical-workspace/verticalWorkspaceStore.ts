/**
 * Sprint 42.8 — active vertical workspace preference.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import { VERTICAL_BY_ID, verticalHomePath } from "./catalog";

const KEY = wsKey("ewp_vertical_workspace_v1");

function loadId(): string {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw && VERTICAL_BY_ID[raw]) return raw;
  } catch {
    /* ignore */
  }
  return "owner";
}

type State = {
  verticalId: string;
  setVerticalId: (id: string) => void;
  homePath: () => string;
};

export const useVerticalWorkspaceStore = create<State>((set, get) => ({
  verticalId: typeof localStorage !== "undefined" ? loadId() : "owner",
  setVerticalId: (id) => {
    if (!VERTICAL_BY_ID[id]) return;
    try {
      localStorage.setItem(KEY, id);
    } catch {
      /* ignore */
    }
    set({ verticalId: id });
  },
  homePath: () => verticalHomePath(get().verticalId),
}));
