/**
 * Sprint 41.2 — persisted UI preferences (font scale, density, menu width).
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import type { Locale } from "@/i18n";
import type { ThemeMode } from "@/theme/themeStore";

export const PREFERENCES_KEY = wsKey("ewp_ui_preferences_v1");

export type FontScale = 80 | 90 | 100 | 110 | 120;
export type DensityMode = "compact" | "standard" | "comfortable";
export type MenuWidth = "compact" | "standard" | "wide";

export type Preferences = {
  theme: ThemeMode;
  language: Locale;
  timeZone: string;
  dateFormat: string;
  dashboardLayout: "grid" | "list";
  notificationsEnabled: boolean;
  accessibility: { reduceMotion: boolean; highContrast: boolean };
  /** Sprint 41.2 */
  fontScale: FontScale;
  density: DensityMode;
  menuWidth: MenuWidth;
};

type PrefState = Preferences & {
  update: (patch: Partial<Preferences>) => void;
  applyToDocument: () => void;
};

const DEFAULTS: Preferences = {
  theme: "system",
  language: "ru",
  timeZone: "UTC",
  dateFormat: "YYYY-MM-DD",
  dashboardLayout: "grid",
  notificationsEnabled: true,
  accessibility: { reduceMotion: false, highContrast: false },
  fontScale: 100,
  density: "standard",
  menuWidth: "standard",
};

function readPrefs(): Preferences {
  try {
    const raw = localStorage.getItem(PREFERENCES_KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw) as Partial<Preferences>;
    return {
      ...DEFAULTS,
      ...parsed,
      accessibility: { ...DEFAULTS.accessibility, ...parsed.accessibility },
    };
  } catch {
    return { ...DEFAULTS };
  }
}

function persist(prefs: Preferences) {
  try {
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(prefs));
  } catch {
    /* ignore */
  }
}

export function applyInterfacePreferences(prefs: Pick<Preferences, "fontScale" | "density" | "menuWidth" | "accessibility">) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.style.setProperty("--ew-font-scale", `${prefs.fontScale / 100}`);
  root.style.fontSize = `${(16 * prefs.fontScale) / 100}px`;
  root.dataset.density = prefs.density;
  root.dataset.menuWidth = prefs.menuWidth;
  root.classList.toggle("ew-reduce-motion", prefs.accessibility.reduceMotion);
  root.classList.toggle("ew-high-contrast", prefs.accessibility.highContrast);
  const menuPx = prefs.menuWidth === "compact" ? 200 : prefs.menuWidth === "wide" ? 300 : 248;
  root.style.setProperty("--ews-sidebar-width", `${menuPx}px`);
  const pad = prefs.density === "compact" ? "0.5rem" : prefs.density === "comfortable" ? "1.25rem" : "0.85rem";
  root.style.setProperty("--ew-density-pad", pad);
}

export const usePreferencesStore = create<PrefState>((set, get) => {
  const initial = typeof localStorage !== "undefined" ? readPrefs() : { ...DEFAULTS };
  return {
    ...initial,
    update: (patch) => {
      set((state) => {
        const next = {
          ...state,
          ...patch,
          accessibility: patch.accessibility
            ? { ...state.accessibility, ...patch.accessibility }
            : state.accessibility,
        };
        const { update: _u, applyToDocument: _a, ...prefs } = next;
        persist(prefs);
        return next;
      });
      get().applyToDocument();
    },
    applyToDocument: () => {
      const s = get();
      applyInterfacePreferences(s);
    },
  };
});
