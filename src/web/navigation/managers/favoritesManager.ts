import type { FavoriteEntry } from "../types";

let favorites: FavoriteEntry[] = [
  { id: "fav_page_ws", kind: "page", label: "Workspace", path: "/workspace" },
  { id: "fav_dash", kind: "dashboard", label: "Executive Dashboard", path: "/workspace/dashboards/dash_exec" },
  { id: "fav_rep", kind: "report", label: "Weekly KPI", path: "/workspace/reports/weekly" },
  { id: "fav_cust", kind: "customer", label: "Acme Corp", path: "/workspace/crm?client=acme" },
  { id: "fav_prj", kind: "project", label: "Enterprise Web", path: "/workspace/list" },
  { id: "fav_cmd", kind: "command", label: "Open CRM", path: "/workspace/crm" },
  { id: "fav_ai", kind: "ai_agent", label: "Ops Copilot", path: "/workspace/ai" },
  { id: "fav_doc", kind: "document", label: "Documents", path: "/workspace/docs" },
];

export const favoritesManager = {
  list(): FavoriteEntry[] {
    return [...favorites];
  },
  pinnedPages() {
    return this.list().filter((f) => f.kind === "page");
  },
  pinnedDashboards() {
    return this.list().filter((f) => f.kind === "dashboard");
  },
  favoriteReports() {
    return this.list().filter((f) => f.kind === "report");
  },
  favoriteCustomers() {
    return this.list().filter((f) => f.kind === "customer");
  },
  favoriteProjects() {
    return this.list().filter((f) => f.kind === "project");
  },
  favoriteCommands() {
    return this.list().filter((f) => f.kind === "command");
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
