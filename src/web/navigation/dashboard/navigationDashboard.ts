import {
  applicationRegistry,
  commandPalette,
  favoritesManager,
  navigationAnalytics,
  navigationHistory,
  navigationManager,
  recentManager,
  searchProvider,
  shortcutManager,
  workspaceFederation,
} from "../managers";

export function buildNavigationDashboard() {
  return {
    activeNavigation: navigationManager.get("sidebar").slice(0, 8),
    searchAnalytics: {
      recent: searchProvider.recent(),
      categories: searchProvider.filters().length,
      ...navigationAnalytics.snapshot().search_statistics,
    },
    mostUsedPages: recentManager.pages(),
    favoriteModules: favoritesManager.list().filter((f) => f.kind === "page" || f.kind === "dashboard"),
    smartFavorites: {
      pages: favoritesManager.pinnedPages(),
      dashboards: favoritesManager.pinnedDashboards(),
      reports: favoritesManager.favoriteReports(),
      customers: favoritesManager.favoriteCustomers(),
      projects: favoritesManager.favoriteProjects(),
      commands: favoritesManager.favoriteCommands(),
    },
    recentActivity: navigationHistory.list().slice(0, 8),
    recentHistory: {
      pages: navigationHistory.recentPages(),
      searches: navigationHistory.recentSearches(),
      documents: navigationHistory.recentDocuments(),
      reports: navigationHistory.recentReports(),
      aiChats: navigationHistory.recentAiChats(),
      commands: navigationHistory.recentCommands(),
    },
    shortcutUsage: shortcutManager.list(),
    commandUsage: commandPalette.list().slice(0, 8),
    workspaces: workspaceFederation.list(),
    currentWorkspace: workspaceFederation.current(),
    applications: applicationRegistry.list(),
    analytics: navigationAnalytics.snapshot(),
  };
}
