import type { ShortcutBinding } from "../types";

let bindings: ShortcutBinding[] = [
  { id: "sc_palette", scope: "global", keys: "Meta+K", action: "open_command_palette", customizable: false },
  { id: "sc_palette_ctrl", scope: "global", keys: "Ctrl+K", action: "open_command_palette", customizable: false },
  { id: "sc_omnibox", scope: "global", keys: "Ctrl+P", action: "open_omnibox", customizable: false },
  { id: "sc_ai", scope: "ai", keys: "Ctrl+Shift+P", action: "open_ai_assistant", customizable: false },
  { id: "sc_commands", scope: "global", keys: "Ctrl+/", action: "open_omnibox_commands", customizable: false },
  { id: "sc_search", scope: "global", keys: "Meta+F", action: "focus_global_search", customizable: true },
  { id: "sc_search_ctrl", scope: "global", keys: "Ctrl+F", action: "focus_global_search", customizable: true },
  { id: "sc_esc", scope: "global", keys: "Escape", action: "close_panels", customizable: false },
  { id: "sc_quick", scope: "global", keys: "Ctrl+Tab", action: "open_quick_switcher", customizable: false },
  { id: "sc_close_tab", scope: "workspace", keys: "Ctrl+W", action: "close_workspace_tab", customizable: false },
  { id: "sc_reopen_tab", scope: "workspace", keys: "Ctrl+Shift+T", action: "reopen_closed_tab", customizable: false },
  { id: "sc_next_tab", scope: "workspace", keys: "Alt+]", action: "next_workspace_tab", customizable: true },
  { id: "sc_prev_tab", scope: "workspace", keys: "Alt+[", action: "prev_workspace_tab", customizable: true },
  { id: "sc_next_panel", scope: "workspace", keys: "Ctrl+Alt+]", action: "next_dock_panel", customizable: true },
  { id: "sc_prev_panel", scope: "workspace", keys: "Ctrl+Alt+[", action: "prev_dock_panel", customizable: true },
  { id: "sc_ws_home", scope: "workspace", keys: "Meta+H", action: "go_workspace_home", customizable: true },
  { id: "sc_user_fav", scope: "user", keys: "Meta+B", action: "toggle_favorite", customizable: true },
  { id: "sc_ai_j", scope: "ai", keys: "Meta+J", action: "open_ai_assistant", customizable: true },
];

export const shortcutManager = {
  list(): ShortcutBinding[] {
    return [...bindings];
  },
  byScope(scope: ShortcutBinding["scope"]) {
    return bindings.filter((b) => b.scope === scope);
  },
  update(id: string, keys: string) {
    bindings = bindings.map((b) => (b.id === id && b.customizable ? { ...b, keys } : b));
    return this.list();
  },
};
