import type { SearchCategory, SearchHit } from "../types";

const index: SearchHit[] = [
  { id: "s1", category: "modules", label: "CRM Platform", path: "/workspace/crm" },
  { id: "s2", category: "users", label: "Alex Owner", path: "/identity/users" },
  { id: "s3", category: "organizations", label: "Demo Corp", path: "/identity/organizations" },
  { id: "s4", category: "documents", label: "Workspace documents", path: "/workspace/docs" },
  { id: "s5", category: "workflows", label: "Invoice approval", path: "/workspace/workflows/invoice" },
  { id: "s6", category: "ai_agents", label: "Ops Copilot", path: "/workspace/ai/ops-copilot" },
  { id: "s7", category: "reports", label: "Weekly KPI", path: "/workspace/reports/weekly" },
  { id: "s8", category: "tasks", label: "Review migration", path: "/workspace?task=migration" },
];

const commands = [
  { id: "cmd_goto_ai", label: ">ai", description: "Open AI Dashboard", path: "/workspace/dashboards/dash_ai" },
  { id: "cmd_goto_settings", label: ">settings", description: "Workspace settings", path: "/workspace/settings" },
  { id: "cmd_search_users", label: ">users", description: "Search users", path: "/identity/users" },
];

export const searchCenter = {
  categories(): SearchCategory[] {
    return ["modules", "users", "organizations", "documents", "workflows", "ai_agents", "reports", "tasks"];
  },
  search(query: string): SearchHit[] {
    const q = query.trim().toLowerCase();
    if (!q) return [...index];
    if (q.startsWith(">")) {
      return commands
        .filter((c) => c.label.includes(q) || c.description.toLowerCase().includes(q.slice(1)))
        .map((c) => ({ id: c.id, category: "modules" as const, label: `${c.label} — ${c.description}`, path: c.path }));
    }
    return index.filter((h) => h.label.toLowerCase().includes(q) || h.category.includes(q));
  },
  commands() {
    return [...commands];
  },
};
