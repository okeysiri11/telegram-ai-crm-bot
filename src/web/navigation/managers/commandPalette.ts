import type { CommandItem } from "../types";

const commands: CommandItem[] = [
  { id: "cmd_ws", kind: "open_module", label: "Open Workspace", route: "/workspace", keywords: ["workspace", "home"] },
  { id: "cmd_id", kind: "open_module", label: "Open Identity Center", route: "/identity", keywords: ["identity", "users", "rbac"] },
  { id: "cmd_dash", kind: "open_dashboard", label: "Open Personal Dashboard", route: "/workspace/dashboards", keywords: ["dashboard", "kpi"] },
  { id: "cmd_ai", kind: "open_ai_agent", label: "Open AI Agent", route: "/workspace/dashboards/dash_ai", keywords: ["ai", "agent", "copilot"] },
  { id: "cmd_report", kind: "open_report", label: "Open Weekly Report", route: "/workspace/reports/weekly", keywords: ["report", "weekly"] },
  { id: "cmd_create_task", kind: "create_entity", label: "Create Task", route: "/workspace?action=create_task", keywords: ["create", "task"] },
  { id: "cmd_run_wf", kind: "run_workflow", label: "Run Invoice Workflow", route: "/workspace?action=create_workflow", keywords: ["workflow", "invoice"] },
  { id: "cmd_theme", kind: "execute_command", label: "Toggle Theme", keywords: ["theme", "dark", "light"], shortcut: "t" },
  { id: "cmd_search", kind: "search_everything", label: "Search Everything", keywords: ["search", "find"], shortcut: "k" },
];

export const commandPalette = {
  hotkeys: ["Ctrl+K", "Meta+K"] as const,
  list(): CommandItem[] {
    return [...commands];
  },
  search(query: string): CommandItem[] {
    const q = query.trim().toLowerCase();
    if (!q) return this.list();
    return commands.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        c.kind.includes(q) ||
        c.keywords.some((k) => k.includes(q)),
    );
  },
};
