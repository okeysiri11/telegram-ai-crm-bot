/**
 * Sprint 42.8 — active vertical workspace preference.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import { VERTICAL_BY_ID, verticalHomePath } from "./catalog";

const KEY = wsKey("ewp_vertical_workspace_v2");
const LEGACY_KEY = wsKey("ewp_vertical_workspace_v1");

// Sprint 46.6 — versioned migration. v1 state could get stuck pointing at a
// vertical id that no longer resolves (e.g. Beauty was previously merged
// into Cafe with no standalone catalog entry). Carry the value forward only
// if it still resolves against the current catalog; otherwise reset to the
// safe default instead of silently keeping a stale/misleading selection.
function loadId(): string {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw && VERTICAL_BY_ID[raw]) return raw;
    const legacy = localStorage.getItem(LEGACY_KEY);
    if (legacy) {
      localStorage.removeItem(LEGACY_KEY);
      if (VERTICAL_BY_ID[legacy]) {
        localStorage.setItem(KEY, legacy);
        return legacy;
      }
    }
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
