import {
  commandPalette,
  favoritesManager,
  navigationHistory,
  navigationManager,
  recentManager,
  searchProvider,
  shortcutManager,
} from "../managers";

export function buildNavigationDashboard() {
  return {
    activeNavigation: navigationManager.get("sidebar").slice(0, 8),
    searchAnalytics: {
      recent: searchProvider.recent(),
      categories: searchProvider.filters().length,
    },
    mostUsedPages: recentManager.pages(),
    favoriteModules: favoritesManager.list().filter((f) => f.kind === "page" || f.kind === "dashboard"),
    recentActivity: navigationHistory.list().slice(0, 8),
    shortcutUsage: shortcutManager.list(),
    commandUsage: commandPalette.list().slice(0, 8),
  };
}
