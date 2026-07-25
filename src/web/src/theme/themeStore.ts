import { create } from "zustand";
import { applyTheme, type BrandOverrides, type ThemeId } from "../../design-system/theme";

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

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: "system",
  brand: {},
  setMode: (mode) => {
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
