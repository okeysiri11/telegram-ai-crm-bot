import type { CommandItem } from "../types";

/** Sprint 30.7 — Russian navigation command palette seeds. */
const commands: CommandItem[] = [
  { id: "cmd_ws", kind: "open_module", label: "Открыть рабочий стол", route: "/desktop", keywords: ["workspace", "рабочий", "стол", "home"] },
  { id: "cmd_id", kind: "open_module", label: "Центр идентичности", route: "/identity", keywords: ["identity", "users", "rbac"] },
  { id: "cmd_module", kind: "open_module", label: "Открыть модуль", route: "/search", keywords: ["модуль", "открыть"] },
  { id: "cmd_client", kind: "open_module", label: "Открыть клиента", route: "/crm?view=clients", keywords: ["клиент", "crm"] },
  { id: "cmd_project", kind: "open_module", label: "Открыть проект", route: "/projects", keywords: ["проект"] },
  { id: "cmd_ai", kind: "open_ai_agent", label: "Открыть AI-агента", route: "/ai-agents", keywords: ["ai", "агент", "copilot"] },
  { id: "cmd_dash", kind: "open_dashboard", label: "Открыть главную", route: "/dashboard", keywords: ["dashboard", "главная", "kpi"] },
  { id: "cmd_owner", kind: "open_dashboard", label: "Панель владельца", route: "/owner", keywords: ["владелец", "owner"] },
  { id: "cmd_admin", kind: "open_dashboard", label: "Панель администратора", route: "/admin", keywords: ["админ", "admin"] },
  { id: "cmd_city", kind: "open_module", label: "Открыть город", route: "/city", keywords: ["город", "карта", "city"] },
  { id: "cmd_calendar", kind: "open_module", label: "Открыть календарь", route: "/calendar", keywords: ["календарь"] },
  { id: "cmd_tasks", kind: "open_module", label: "Открыть задачи", route: "/tasks", keywords: ["задачи"] },
  { id: "cmd_notify", kind: "open_module", label: "Открыть уведомления", route: "/notifications", keywords: ["уведомления"] },
  { id: "cmd_report", kind: "open_report", label: "Недельный отчёт", route: "/workspace/reports/weekly", keywords: ["report", "weekly", "отчёт"] },
  { id: "cmd_create_task", kind: "create_entity", label: "Создать задачу", route: "/tasks", keywords: ["создать", "задача"] },
  { id: "cmd_run_wf", kind: "run_workflow", label: "Запустить процесс счёта", route: "/workspace?action=create_workflow", keywords: ["workflow", "invoice"] },
  { id: "cmd_theme", kind: "execute_command", label: "Переключить тему", keywords: ["theme", "тема", "dark", "light"], shortcut: "t" },
  { id: "cmd_search", kind: "search_everything", label: "Глобальный поиск", keywords: ["поиск", "search", "find"], shortcut: "k" },
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
