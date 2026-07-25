import type { HistoryEntry, HistoryKind } from "../types";

let history: HistoryEntry[] = [
  { id: "h1", kind: "page", label: "Workspace", path: "/workspace", at: new Date().toISOString() },
  { id: "h2", kind: "command", label: "Open AI Agent", path: "/workspace/dashboards/dash_ai", at: new Date(Date.now() - 60000).toISOString() },
  { id: "h3", kind: "search", label: "invoice", at: new Date(Date.now() - 120000).toISOString() },
  { id: "h4", kind: "document", label: "Security Policy", path: "/workspace/docs/security", at: new Date(Date.now() - 180000).toISOString() },
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
};
