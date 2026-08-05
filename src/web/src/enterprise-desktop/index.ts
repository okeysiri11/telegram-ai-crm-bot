export type {
  DesktopWindowState,
  DesktopIcon,
  DesktopAppDef,
  WallpaperId,
  DesktopLayoutId,
  DesktopSessionSnapshot,
  WindowMode,
  SnapRegion,
  WorkspaceProfile,
  OpenAppOptions,
} from "./types";
export { DESKTOP_SESSION_KEY, DESKTOP_WM_VERSION } from "./types";
export { DESKTOP_APPS, WALLPAPERS, DESKTOP_LAYOUTS, appById, appByPath } from "./desktopCatalog";
export { useDesktopStore } from "./desktopStore";
export { DesktopShell } from "./DesktopShell";
export { WindowFrame } from "./WindowFrame";
export { EnterpriseDock } from "./EnterpriseDock";
export { DesktopLauncher } from "./DesktopLauncher";
export { WindowInspector } from "./WindowInspector";
export { useDesktopKeyboard } from "./useDesktopKeyboard";
export { DESKTOP_SHORTCUTS } from "./shortcutCatalog";
export { WORKSPACE_TEMPLATES, seedWorkspaceProfiles } from "./workspaceProfiles";
