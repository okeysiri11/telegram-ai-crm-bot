import type { Personalization } from "../types";

let prefs: Personalization = {
  dashboardLayout: "layout_personal",
  widgets: ["w_kpi", "w_ai", "w_tasks", "w_calendar", "w_notif", "w_health"],
  theme: "system",
  language: "en",
  timeZone: "UTC",
  homePage: "/workspace",
  defaultWorkspace: "ws_personal",
  notificationPreferences: { email: true, push: false, inApp: true },
};

export const personalizationEngine = {
  get(): Personalization {
    return {
      ...prefs,
      widgets: [...prefs.widgets],
      notificationPreferences: { ...prefs.notificationPreferences },
    };
  },
  update(patch: Partial<Personalization>) {
    prefs = {
      ...prefs,
      ...patch,
      widgets: patch.widgets ? [...patch.widgets] : prefs.widgets,
      notificationPreferences: {
        ...prefs.notificationPreferences,
        ...(patch.notificationPreferences || {}),
      },
    };
    return this.get();
  },
};
