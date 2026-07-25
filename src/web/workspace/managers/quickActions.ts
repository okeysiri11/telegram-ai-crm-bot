import type { QuickActionId } from "../types";

export const quickActions = {
  actions: [
    { id: "create_task" as QuickActionId, label: "Create Task", shortcut: "t", path: "/workspace?action=create_task" },
    { id: "create_workflow" as QuickActionId, label: "Create Workflow", shortcut: "w", path: "/workspace?action=create_workflow" },
    { id: "open_ai_assistant" as QuickActionId, label: "Open AI Assistant", shortcut: "a", path: "/workspace?action=ai" },
    { id: "start_chat" as QuickActionId, label: "Start Chat", shortcut: "c", path: "/workspace?action=chat" },
    { id: "new_crm_record" as QuickActionId, label: "New CRM Record", shortcut: "r", path: "/workspace?action=crm" },
    { id: "upload_document" as QuickActionId, label: "Upload Document", shortcut: "u", path: "/workspace?action=upload" },
    { id: "launch_automation" as QuickActionId, label: "Launch Automation", shortcut: "l", path: "/workspace?action=automation" },
  ],
  byShortcut(key: string) {
    return this.actions.find((a) => a.shortcut === key.toLowerCase());
  },
};
