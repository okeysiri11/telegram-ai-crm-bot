import type { CommandItem } from "../../command-center/types";

/** Sprint 27.5 — developer / diagnostic commands for the Command Palette. */
export const DEVELOPER_COMMANDS: CommandItem[] = [
  {
    id: "dev_toggle_ops",
    kind: "open",
    action: "dev_toggle_ops_strips",
    label: "Developer: Toggle platform strips",
    route: "/dashboard",
    keywords: ["dev", "ops", "strips", "debug"],
  },
  {
    id: "dev_open_cc",
    kind: "navigate",
    action: "dev_open_command_center",
    label: "Developer: Open Command Center page",
    route: "/command-center",
    keywords: ["dev", "command", "center"],
  },
  {
    id: "dev_open_runtime",
    kind: "open",
    action: "dev_open_runtime",
    label: "Developer: Open AI Runtime",
    route: "/platform-builder/runtime",
    keywords: ["dev", "runtime", "queue"],
  },
  {
    id: "dev_open_search",
    kind: "search",
    action: "dev_open_search",
    label: "Developer: Search Workspace",
    route: "/search",
    keywords: ["dev", "search"],
  },
  {
    id: "dev_open_settings",
    kind: "open_settings",
    action: "dev_open_settings",
    label: "Developer: Open Settings",
    route: "/settings",
    keywords: ["dev", "settings"],
  },
  {
    id: "dev_reload_health",
    kind: "open",
    action: "dev_reload_health",
    label: "Developer: Focus Runtime Health dock",
    route: "/dashboard",
    keywords: ["dev", "health", "status"],
  },
];

export function isDeveloperCommand(id: string): boolean {
  return id.startsWith("dev_") || DEVELOPER_COMMANDS.some((c) => c.id === id);
}
