import { create } from "zustand";

export type ThemeMode = "light" | "dark" | "system";

type ThemeState = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  apply: () => void;
};

function resolve(mode: ThemeMode): "light" | "dark" {
  if (mode === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return mode;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: "system",
  setMode: (mode) => {
    set({ mode });
    get().apply();
  },
  apply: () => {
    document.documentElement.setAttribute("data-theme", resolve(get().mode));
  },
}));
