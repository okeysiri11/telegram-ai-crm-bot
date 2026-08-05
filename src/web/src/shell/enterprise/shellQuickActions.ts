/**
 * Shell quick actions — Sprint 28.5 / 28.6.
 */

import { searchIndex } from "../../../navigation/managers/searchIndex";

export type ShellQuickAction = {
  id: string;
  label: string;
  path: string;
  keywords: string[];
  group: "create" | "open" | "command";
};

export const SHELL_QUICK_ACTIONS: ShellQuickAction[] = [
  { id: "qa_client", label: "Создать клиента", path: "/crm?action=create_client", keywords: ["создать", "клиент", "crm"], group: "create" },
  { id: "qa_project", label: "Создать проект", path: "/projects?action=create_project", keywords: ["создать", "проект"], group: "create" },
  { id: "qa_doc", label: "Создать документ", path: "/documents?action=create_document", keywords: ["создать", "документ"], group: "create" },
  { id: "qa_ai", label: "Запустить AI", path: "/ai-agents?action=create", keywords: ["ai", "агент", "запустить"], group: "create" },
  { id: "qa_map", label: "Открыть карту", path: "/enterprise-city", keywords: ["карта", "город"], group: "open" },
  { id: "qa_task", label: "Создать задачу", path: "/projects?action=create_task", keywords: ["создать", "задача"], group: "create" },
  { id: "qa_agent", label: "Создать агента", path: "/platform-builder/builder-studio", keywords: ["создать", "агент"], group: "create" },
  { id: "qa_workflow", label: "Создать процесс", path: "/platform-builder/workflow-center", keywords: ["создать", "процесс"], group: "create" },
  { id: "qa_studio", label: "Открыть студию", path: "/ai-studio", keywords: ["открыть", "ai", "студия"], group: "open" },
  { id: "qa_city", label: "Открыть город", path: "/enterprise-city", keywords: ["открыть", "город"], group: "open" },
  { id: "qa_crm", label: "Открыть CRM", path: "/crm", keywords: ["открыть", "crm"], group: "open" },
  { id: "qa_dashboard", label: "Открыть главную", path: "/dashboard", keywords: ["открыть", "главная"], group: "open" },
  { id: "qa_production", label: "Открыть продакшн", path: "/production-studio", keywords: ["открыть", "продакшн"], group: "open" },
  { id: "qa_desktop", label: "Открыть рабочий стол", path: "/desktop", keywords: ["открыть", "рабочий", "стол"], group: "open" },
  { id: "qa_command", label: "Палитра команд", path: "/command-center", keywords: ["команды", "палитра"], group: "command" },
  { id: "qa_owner", label: "Панель владельца", path: "/owner", keywords: ["владелец", "owner"], group: "open" },
  { id: "qa_automation", label: "Центр автоматизации", path: "/automation", keywords: ["автоматизация"], group: "open" },
  { id: "qa_ebn", label: "Бизнес-сеть", path: "/business-network", keywords: ["бизнес", "сеть"], group: "open" },
  { id: "qa_kernel", label: "Ядро предприятия", path: "/kernel", keywords: ["ядро", "архитектура"], group: "open" },
];

let registered = false;

export function registerQuickActionsInSearch() {
  if (registered) return;
  registered = true;
  for (const a of SHELL_QUICK_ACTIONS) {
    searchIndex.upsert({
      id: `shell_qa_${a.id}`,
      category: "commands",
      title: a.label,
      path: a.path,
      tokens: [...a.keywords, "quick", "action", a.group],
      rankBoost: 16,
    });
  }
}

/** Sprint 28.6 — execute via Command Runtime (lazy import avoids cycle). */
export async function executeShellQuickAction(id: string) {
  const { commandRuntime } = await import("@/runtime/commandRuntime");
  commandRuntime.setSurface("shell");
  return commandRuntime.execute(id);
}
