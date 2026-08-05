/**
 * Launcher registry — Sprint 28.7.
 * Desktop launcher · Quick Actions · Palette · Shortcuts → Registry IDs only.
 */

import { SHELL_QUICK_ACTIONS } from "@/shell/enterprise/shellQuickActions";
import { DESKTOP_APPS } from "@/enterprise-desktop/desktopCatalog";

/** appId → command registry id (no duplicated action definitions). */
export const LAUNCHER_COMMAND_MAP: Record<string, string> = {
  dashboard: "mod_dashboard",
  crm: "act_open_crm",
  erp: "act_open_erp",
  finance: "act_open_analytics",
  knowledge: "act_open_knowledge",
  ai_studio: "act_open_ai_studio",
  ai_agents: "mod_ai_agents",
  marketplace: "act_open_marketplace",
  analytics: "act_open_analytics",
  settings: "act_open_settings",
  city: "act_open_enterprise_city",
  production: "mod_production_studio",
  prod_image: "mod_production_studio",
  prod_video: "mod_production_studio",
  prod_audio: "mod_production_studio",
  prod_voice: "mod_production_studio",
  prod_avatar: "act_open_ai_studio",
  prod_reels: "mod_production_studio",
  prod_ads: "mod_production_studio",
  prod_creative: "mod_production_studio",
  prod_prompt: "mod_production_studio",
  prod_publish: "mod_production_studio",
  prod_runtime: "mod_production_studio",
  prod_analytics: "mod_production_studio",
  workflow_studio: "act_open_workflow_center",
  agent_studio: "act_open_builder_studio",
  devtools: "cmd_cc",
  cmd_runtime: "dev_open_cmd_inspector",
  workflow_runtime: "wf_open_inspector",
  automation_center: "auto_open_center",
  business_network: "ebn_open",
  digital_citizens: "edc_open",
  life_engine: "life_open",
  assets: "asset_open",
  documents: "act_open_documents",
  automation: "auto_open_center",
};

export type LauncherRegistryItem = {
  appId: string;
  commandId: string;
  label: string;
  path: string;
  group: string;
  source: "desktop" | "shell_qa" | "shortcut";
};

export const launcherRegistry = {
  resolveCommandId(appIdOrCommandId: string): string {
    return LAUNCHER_COMMAND_MAP[appIdOrCommandId] || appIdOrCommandId;
  },

  listDesktop(): LauncherRegistryItem[] {
    return DESKTOP_APPS.map((a) => ({
      appId: a.id,
      commandId: this.resolveCommandId(a.id),
      label: a.label,
      path: a.path,
      group: a.group,
      source: "desktop" as const,
    }));
  },

  listQuickActions(): LauncherRegistryItem[] {
    return SHELL_QUICK_ACTIONS.map((a) => ({
      appId: a.id,
      commandId: a.id,
      label: a.label,
      path: a.path,
      group: a.group,
      source: "shell_qa" as const,
    }));
  },

  /** Keyboard / menubar shortcuts → registry ids */
  shortcuts(): { id: string; commandId: string; keys: string }[] {
    return [
      { id: "close_window", commandId: "desk_close_focused", keys: "Ctrl+W" },
      { id: "minimize", commandId: "desk_minimize_focused", keys: "Ctrl+M" },
      { id: "maximize", commandId: "desk_maximize_focused", keys: "Ctrl+Shift+M" },
      { id: "open_city", commandId: "desk_open_city", keys: "menubar" },
      { id: "open_production", commandId: "desk_open_production", keys: "menubar" },
      { id: "open_crm", commandId: "desk_open_crm", keys: "menubar" },
      { id: "undo", commandId: "sys_undo", keys: "Ctrl+Z" },
      { id: "redo", commandId: "sys_redo", keys: "Ctrl+Shift+Z" },
    ];
  },

  all(): LauncherRegistryItem[] {
    return [...this.listDesktop(), ...this.listQuickActions()];
  },
};
