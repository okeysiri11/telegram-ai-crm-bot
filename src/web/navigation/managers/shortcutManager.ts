import type { ShortcutBinding } from "../types";

let bindings: ShortcutBinding[] = [
  { id: "sc_palette", scope: "global", keys: "Meta+K", action: "open_command_palette", customizable: false },
  { id: "sc_palette_ctrl", scope: "global", keys: "Ctrl+K", action: "open_command_palette", customizable: false },
  { id: "sc_search", scope: "global", keys: "Meta+/", action: "focus_global_search", customizable: true },
  { id: "sc_ws_home", scope: "workspace", keys: "Meta+H", action: "go_workspace_home", customizable: true },
  { id: "sc_user_fav", scope: "user", keys: "Meta+B", action: "toggle_favorite", customizable: true },
  { id: "sc_ai", scope: "ai", keys: "Meta+J", action: "open_ai_assistant", customizable: true },
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
