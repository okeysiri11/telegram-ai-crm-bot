import { create } from "zustand";
import type { Locale } from "@/i18n";
import type { ThemeMode } from "@/theme/themeStore";

export type Preferences = {
  theme: ThemeMode;
  language: Locale;
  timeZone: string;
  dateFormat: string;
  dashboardLayout: "grid" | "list";
  notificationsEnabled: boolean;
  accessibility: { reduceMotion: boolean; highContrast: boolean };
};

type PrefState = Preferences & {
  update: (patch: Partial<Preferences>) => void;
};

export const usePreferencesStore = create<PrefState>((set) => ({
  theme: "system",
  language: "en",
  timeZone: "UTC",
  dateFormat: "YYYY-MM-DD",
  dashboardLayout: "grid",
  notificationsEnabled: true,
  accessibility: { reduceMotion: false, highContrast: false },
  update: (patch) => set(patch),
}));
