/**
 * Sprint 27.7 / 28.4 — Enterprise Desktop types + Window Manager.
 */

export const DESKTOP_SESSION_KEY = "ews_desktop_session_v1";
export const DESKTOP_WM_VERSION = "28.4";

export type WallpaperId = "aurora" | "slate" | "studio" | "midnight" | "plain";

export type DesktopIconKind = "app" | "folder" | "shortcut";

export type DesktopIcon = {
  id: string;
  label: string;
  kind: DesktopIconKind;
  /** App route or nested folder id */
  target: string;
  x: number;
  y: number;
  badge?: number;
};

/** Explicit window modes — Sprint 28.4. */
export type WindowMode = "floating" | "snapped" | "maximized" | "fullscreen" | "minimized" | "docked";

export type SnapRegion =
  | "left"
  | "right"
  | "top"
  | "bottom"
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right"
  | "center"
  | "fullscreen";

export type WindowBounds = { x: number; y: number; width: number; height: number };

export type WindowTab = {
  id: string;
  title: string;
  path: string;
  pinned: boolean;
};

export type SplitOrientation = "horizontal" | "vertical" | null;

export type DesktopWindowState = {
  id: string;
  appId: string;
  title: string;
  path: string;
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
  minimized: boolean;
  maximized: boolean;
  /** Before maximize/snap/fullscreen */
  restore?: WindowBounds;
  /** Sprint 28.4 */
  mode?: WindowMode;
  snapRegion?: SnapRegion | null;
  alwaysOnTop?: boolean;
  floating?: boolean;
  fullscreen?: boolean;
  workspaceId?: string;
  tabs?: WindowTab[];
  activeTabId?: string | null;
  split?: SplitOrientation;
  splitSecondaryTabId?: string | null;
  closedTabStack?: WindowTab[];
};

export type DockItem = {
  appId: string;
  pinned: boolean;
};

export type DesktopLayoutId = "default" | "ops" | "sales" | "dev";

export type WorkspaceProfile = {
  id: string;
  name: string;
  templateId?: string;
  windows: DesktopWindowState[];
  focusedId: string | null;
  dock: DockItem[];
  wallpaperId: WallpaperId;
  layoutId: DesktopLayoutId;
  updatedAt: string;
};

export type WorkspaceTemplateId = "blank" | "ops" | "creative" | "dev" | "executive";

export type DesktopSessionSnapshot = {
  version: 1 | 2;
  wallpaperId: WallpaperId;
  layoutId: DesktopLayoutId;
  icons: DesktopIcon[];
  windows: DesktopWindowState[];
  focusedId: string | null;
  dock: DockItem[];
  recentAppIds: string[];
  launcherOpen: boolean;
  profileId: string;
  activeWorkspaceId: string;
  workspaceProfiles?: WorkspaceProfile[];
  activeWorkspaceProfileId?: string | null;
  inspectorOpen?: boolean;
  updatedAt: string;
};

export type DesktopAppDef = {
  id: string;
  label: string;
  path: string;
  icon: string;
  group: "core" | "ai" | "ops" | "tools";
  badgeKey?: "notifications" | "jobs" | "ai";
};

export type OpenAppOptions = {
  forceNew?: boolean;
  /** Prefer matching this exact path (incl. query) for multi-studio. */
  exactPath?: boolean;
  asTab?: boolean;
  targetWindowId?: string;
};

export type SnapPreview = {
  region: SnapRegion;
  bounds: WindowBounds;
} | null;
