export const workspaceSettings = {
  sections: [
    "appearance",
    "dashboard",
    "navigation",
    "ai_preferences",
    "accessibility",
    "integrations",
    "shortcuts",
  ] as const,
  defaults: {
    appearance: { density: "comfortable", sidebarCollapsed: false },
    dashboard: { autoRefresh: true, refreshSec: 30 },
    navigation: { showFavorites: true, showRecent: true },
    aiPreferences: { suggestActions: true, defaultAgent: "ops-copilot" },
    accessibility: { highContrast: false, reduceMotion: false },
    integrations: { hub: true, websocket: true, eventBus: true },
    shortcuts: { enabled: true },
  },
};
