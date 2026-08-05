/**
 * Sprint 33.1 — Simple | Pro experience mode (default: Simple).
 */

import { create } from "zustand";

export type ExperienceMode = "simple" | "pro";

export const EXPERIENCE_MODE_KEY = "ewp_ux_mode_v1";

function readMode(): ExperienceMode {
  try {
    const raw = localStorage.getItem(EXPERIENCE_MODE_KEY);
    if (raw === "pro" || raw === "simple") return raw;
  } catch {
    /* ignore */
  }
  return "simple";
}

type ExperienceModeState = {
  mode: ExperienceMode;
  setMode: (mode: ExperienceMode) => void;
  toggle: () => void;
  isSimple: () => boolean;
  isPro: () => boolean;
};

export const useExperienceModeStore = create<ExperienceModeState>((set, get) => ({
  mode: typeof window !== "undefined" ? readMode() : "simple",
  setMode: (mode) => {
    if (get().mode === mode) return;
    try {
      localStorage.setItem(EXPERIENCE_MODE_KEY, mode);
    } catch {
      /* ignore */
    }
    set({ mode });
  },
  toggle: () => {
    const next = get().mode === "simple" ? "pro" : "simple";
    get().setMode(next);
  },
  isSimple: () => get().mode === "simple",
  isPro: () => get().mode === "pro",
}));
