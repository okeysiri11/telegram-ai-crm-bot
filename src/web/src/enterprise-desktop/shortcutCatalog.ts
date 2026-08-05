/**
 * Desktop keyboard shortcut catalog — Sprint 28.4.
 */

export type DesktopShortcut = {
  id: string;
  keys: string;
  label: string;
  group: "window" | "tabs" | "workspace" | "system";
};

export const DESKTOP_SHORTCUTS: DesktopShortcut[] = [
  { id: "cycle_fwd", keys: "Ctrl+Tab / Alt+Tab", label: "Next window", group: "window" },
  { id: "cycle_back", keys: "Ctrl+Shift+Tab / Alt+Shift+Tab", label: "Previous window", group: "window" },
  { id: "close", keys: "Ctrl+W", label: "Close window / tab", group: "window" },
  { id: "new", keys: "Ctrl+N", label: "New window (duplicate focus)", group: "window" },
  { id: "duplicate", keys: "Ctrl+D", label: "Duplicate tab", group: "tabs" },
  { id: "launcher", keys: "Ctrl+Space", label: "Launcher", group: "system" },
  { id: "palette", keys: "Ctrl+Shift+P / Ctrl+K", label: "Command palette", group: "system" },
  { id: "escape", keys: "Esc", label: "Close launcher / cancel snap preview", group: "system" },
  { id: "reopen", keys: "Ctrl+Shift+T", label: "Reopen closed window", group: "window" },
  { id: "maximize", keys: "Ctrl+Shift+M", label: "Toggle maximize", group: "window" },
  { id: "minimize", keys: "Ctrl+M", label: "Minimize", group: "window" },
  { id: "snap_left", keys: "Ctrl+Shift+←", label: "Snap left", group: "window" },
  { id: "snap_right", keys: "Ctrl+Shift+→", label: "Snap right", group: "window" },
  { id: "inspector", keys: "Ctrl+Shift+I", label: "Window Inspector", group: "system" },
];
