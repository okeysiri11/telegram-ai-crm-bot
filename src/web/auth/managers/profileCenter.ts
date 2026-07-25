export type ProfileSettings = {
  avatar: string;
  name: string;
  theme: "light" | "dark" | "corporate" | "system";
  language: "en" | "ru" | "uk";
  notifications: boolean;
  timeZone: string;
  accessibility: { highContrast: boolean; reduceMotion: boolean };
  dashboardPreferences: { dense: boolean; showKpis: boolean };
};

let settings: ProfileSettings = {
  avatar: "",
  name: "Alex Owner",
  theme: "system",
  language: "en",
  notifications: true,
  timeZone: "UTC",
  accessibility: { highContrast: false, reduceMotion: false },
  dashboardPreferences: { dense: false, showKpis: true },
};

export const profileCenter = {
  get(): ProfileSettings {
    return { ...settings, accessibility: { ...settings.accessibility }, dashboardPreferences: { ...settings.dashboardPreferences } };
  },
  update(patch: Partial<ProfileSettings>) {
    settings = {
      ...settings,
      ...patch,
      accessibility: { ...settings.accessibility, ...(patch.accessibility || {}) },
      dashboardPreferences: { ...settings.dashboardPreferences, ...(patch.dashboardPreferences || {}) },
    };
    return this.get();
  },
};
