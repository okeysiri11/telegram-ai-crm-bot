/**
 * Sprint 42.1 — per-role UI session vault (sidebar/dock/theme/tabs isolation).
 * Used by Dev Role Switcher without logout.
 */

import { wsKey } from "./workspaceSlot";

export const ROLE_VAULT_KEY = "ewp_role_session_vault_v1";

export type RoleSessionSnapshot = {
  viewMode?: string;
  roleId?: string;
  toolbarCollapsed?: string | null;
  dockLayout?: string | null;
  workspaceDock?: string | null;
  workspaceTabs?: string | null;
  preferences?: string | null;
  theme?: string | null;
  locale?: string | null;
  activityOpen?: string | null;
  savedAt: string;
};

type Vault = Record<string, RoleSessionSnapshot>;

const TRACKED_BASES = [
  "ewp_view_mode_v1",
  "ewp_role_switcher_v1",
  "ewp_toolbar_collapsed_v1",
  "ews_dock_layout_v1",
  "ews_activity_panel_open_v1",
  "ewp_workspace_dock_v1",
  "ews_workspace_session_v1",
  "ewp_ui_preferences_v1",
  "ews_theme_mode_v1",
] as const;

function readVault(): Vault {
  try {
    return JSON.parse(localStorage.getItem(wsKey(ROLE_VAULT_KEY)) || "{}") as Vault;
  } catch {
    return {};
  }
}

function writeVault(v: Vault) {
  localStorage.setItem(wsKey(ROLE_VAULT_KEY), JSON.stringify(v));
}

export function snapshotRoleSession(roleId: string): RoleSessionSnapshot {
  const snap: RoleSessionSnapshot = {
    viewMode: localStorage.getItem(wsKey("ewp_view_mode_v1")) || undefined,
    roleId: localStorage.getItem(wsKey("ewp_role_switcher_v1")) || roleId,
    toolbarCollapsed: localStorage.getItem(wsKey("ewp_toolbar_collapsed_v1")),
    dockLayout: localStorage.getItem(wsKey("ews_dock_layout_v1")),
    workspaceDock: localStorage.getItem(wsKey("ewp_workspace_dock_v1")),
    workspaceTabs: localStorage.getItem(wsKey("ews_workspace_session_v1")),
    preferences: localStorage.getItem(wsKey("ewp_ui_preferences_v1")),
    theme: localStorage.getItem(wsKey("ews_theme_mode_v1")),
    locale: localStorage.getItem(wsKey("ewp_ui_preferences_v1")),
    activityOpen: localStorage.getItem(wsKey("ews_activity_panel_open_v1")),
    savedAt: new Date().toISOString(),
  };
  const vault = readVault();
  vault[roleId] = snap;
  writeVault(vault);
  return snap;
}

export function restoreRoleSession(roleId: string): boolean {
  const vault = readVault();
  const snap = vault[roleId];
  if (!snap) return false;
  const map: Array<[string, string | null | undefined]> = [
    ["ewp_view_mode_v1", snap.viewMode],
    ["ewp_role_switcher_v1", snap.roleId],
    ["ewp_toolbar_collapsed_v1", snap.toolbarCollapsed],
    ["ews_dock_layout_v1", snap.dockLayout],
    ["ewp_workspace_dock_v1", snap.workspaceDock],
    ["ews_workspace_session_v1", snap.workspaceTabs],
    ["ewp_ui_preferences_v1", snap.preferences],
    ["ews_theme_mode_v1", snap.theme],
    ["ews_activity_panel_open_v1", snap.activityOpen],
  ];
  for (const [base, val] of map) {
    if (val == null) localStorage.removeItem(wsKey(base));
    else localStorage.setItem(wsKey(base), val);
  }
  void TRACKED_BASES;
  return true;
}

/** Switch role: snapshot current, restore target (or defaults), update role key. */
export function switchRoleSession(fromRole: string, toRole: string): void {
  snapshotRoleSession(fromRole);
  const restored = restoreRoleSession(toRole);
  if (!restored) {
    localStorage.setItem(wsKey("ewp_role_switcher_v1"), toRole);
  }
}
