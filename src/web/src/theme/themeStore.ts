import { wsKey } from "@/multi-role/workspaceSlot";
import { create } from "zustand";
import { applyTheme, type BrandOverrides, type ThemeId } from "../../design-system/theme";

/** Light | Dark | Auto (system) | Corporate */
export type ThemeMode = ThemeId | "system";

type ThemeState = {
  mode: ThemeMode;
  brand: BrandOverrides;
  setMode: (mode: ThemeMode) => void;
  setBrand: (brand: BrandOverrides) => void;
  apply: () => void;
};

function resolve(mode: ThemeMode): ThemeId {
  if (mode === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return mode;
}

const THEME_KEY = wsKey("ews_theme_mode_v1");

function readMode(): ThemeMode {
  try {
    const v = localStorage.getItem(THEME_KEY);
    if (v === "light" || v === "dark" || v === "system" || v === "corporate") return v;
    if (v === "auto") return "system";
  } catch {
    /* ignore */
  }
  return "system";
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: typeof window !== "undefined" ? readMode() : "system",
  brand: {},
  setMode: (mode) => {
    try {
      localStorage.setItem(THEME_KEY, mode);
    } catch {
      /* ignore */
    }
    set({ mode });
    get().apply();
  },
  setBrand: (brand) => {
    set({ brand });
    get().apply();
  },
  apply: () => {
    applyTheme(resolve(get().mode), get().brand);
  },
}));
