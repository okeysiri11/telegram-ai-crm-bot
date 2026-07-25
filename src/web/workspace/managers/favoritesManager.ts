import type { FavoriteItem } from "../types";

let favorites: FavoriteItem[] = [
  { id: "fav1", kind: "module", label: "AI Orchestrator", path: "/workspace/ai" },
  { id: "fav2", kind: "dashboard", label: "Executive Dashboard", path: "/workspace/dashboards/dash_exec" },
  { id: "fav3", kind: "report", label: "Weekly KPI", path: "/workspace/reports/weekly" },
  { id: "fav4", kind: "ai_agent", label: "Ops Copilot", path: "/workspace/ai/ops-copilot" },
  { id: "fav5", kind: "document", label: "Runbook", path: "/workspace/docs/runbook" },
];

export const favoritesManager = {
  list(): FavoriteItem[] {
    return [...favorites];
  },
  add(item: FavoriteItem) {
    if (!favorites.some((f) => f.id === item.id)) favorites = [item, ...favorites];
    return this.list();
  },
  remove(id: string) {
    favorites = favorites.filter((f) => f.id !== id);
    return this.list();
  },
};
