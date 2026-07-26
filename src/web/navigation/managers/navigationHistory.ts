import type { HistoryEntry, HistoryKind } from "../types";

let history: HistoryEntry[] = [
  { id: "h1", kind: "page", label: "Workspace", path: "/workspace", at: new Date().toISOString() },
  { id: "h2", kind: "command", label: "Open AI Agent", path: "/workspace/dashboards/dash_ai", at: new Date(Date.now() - 60000).toISOString() },
  { id: "h3", kind: "search", label: "invoice", at: new Date(Date.now() - 120000).toISOString() },
  { id: "h4", kind: "document", label: "Documents", path: "/workspace/docs", at: new Date(Date.now() - 180000).toISOString() },
  { id: "h5", kind: "report", label: "Weekly KPI", path: "/workspace/reports/weekly", at: new Date(Date.now() - 240000).toISOString() },
  { id: "h6", kind: "ai_chat", label: "Ops Copilot", path: "/workspace/ai", at: new Date(Date.now() - 300000).toISOString() },
];

export const navigationHistory = {
  list(kind?: HistoryKind): HistoryEntry[] {
    return kind ? history.filter((h) => h.kind === kind) : [...history];
  },
  push(entry: Omit<HistoryEntry, "id" | "at">) {
    const item: HistoryEntry = {
      ...entry,
      id: `h_${Math.random().toString(36).slice(2, 8)}`,
      at: new Date().toISOString(),
    };
    history = [item, ...history].slice(0, 50);
    return item;
  },
  recentPages() {
    return this.list("page").slice(0, 8);
  },
  recentCommands() {
    return this.list("command").slice(0, 8);
  },
  recentSearches() {
    return this.list("search").slice(0, 8);
  },
  recentDocuments() {
    return this.list("document").slice(0, 8);
  },
  recentReports() {
    return this.list("report").slice(0, 8);
  },
  recentAiChats() {
    return this.list("ai_chat").slice(0, 8);
  },
};
