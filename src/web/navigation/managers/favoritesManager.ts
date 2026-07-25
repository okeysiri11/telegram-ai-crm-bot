import type { FavoriteEntry } from "../types";

let favorites: FavoriteEntry[] = [
  { id: "fav_page_ws", kind: "page", label: "Workspace", path: "/workspace" },
  { id: "fav_dash", kind: "dashboard", label: "Executive Dashboard", path: "/workspace/dashboards/dash_exec" },
  { id: "fav_rep", kind: "report", label: "Weekly KPI", path: "/workspace/reports/weekly" },
  { id: "fav_ai", kind: "ai_agent", label: "Ops Copilot", path: "/workspace/ai" },
  { id: "fav_doc", kind: "document", label: "Security Policy", path: "/workspace/docs/security" },
  { id: "fav_search", kind: "search", label: "crm", path: "/navigation?q=crm" },
];

export const favoritesManager = {
  list(): FavoriteEntry[] {
    return [...favorites];
  },
  add(entry: FavoriteEntry) {
    favorites = [entry, ...favorites.filter((f) => f.id !== entry.id)];
    return this.list();
  },
  remove(id: string) {
    favorites = favorites.filter((f) => f.id !== id);
    return this.list();
  },
};
