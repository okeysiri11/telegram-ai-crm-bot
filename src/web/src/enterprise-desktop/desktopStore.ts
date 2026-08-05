/**
 * Enterprise Desktop store + Window Manager — Sprint 27.7 / 28.4.
 * Single authority for windows, focus, snap, tabs, workspace profiles.
 */

import { create } from "zustand";
import {
  DESKTOP_SESSION_KEY,
  type DesktopIcon,
  type DesktopLayoutId,
  type DesktopSessionSnapshot,
  type DesktopWindowState,
  type DockItem,
  type OpenAppOptions,
  type SnapPreview,
  type SnapRegion,
  type WallpaperId,
  type WindowBounds,
  type WindowMode,
  type WindowTab,
  type WorkspaceProfile,
} from "./types";
import { appById, appByPath, defaultDock, defaultIcons } from "./desktopCatalog";
import { enterpriseEventBus } from "@/integration-hub";
import {
  WORKSPACE_TEMPLATES,
  profileFromState,
  seedWorkspaceProfiles,
} from "./workspaceProfiles";
import type { WorkspaceTemplateId } from "./types";

const MIN_W = 420;
const MIN_H = 280;
const CASCADE = 28;
const Z_BASE = 20;
const Z_AOT = 80;
const Z_MODAL = 90;

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

function viewport(): WindowBounds {
  const vw = typeof window !== "undefined" ? window.innerWidth : 1200;
  const vh = typeof window !== "undefined" ? window.innerHeight - 64 : 800;
  return { x: 0, y: 0, width: vw, height: vh };
}

function snapBounds(region: SnapRegion): WindowBounds {
  const { width: vw, height: vh } = viewport();
  const hw = Math.floor(vw / 2);
  const hh = Math.floor(vh / 2);
  switch (region) {
    case "left":
      return { x: 0, y: 0, width: hw, height: vh };
    case "right":
      return { x: hw, y: 0, width: vw - hw, height: vh };
    case "top":
      return { x: 0, y: 0, width: vw, height: hh };
    case "bottom":
      return { x: 0, y: hh, width: vw, height: vh - hh };
    case "top-left":
      return { x: 0, y: 0, width: hw, height: hh };
    case "top-right":
      return { x: hw, y: 0, width: vw - hw, height: hh };
    case "bottom-left":
      return { x: 0, y: hh, width: hw, height: vh - hh };
    case "bottom-right":
      return { x: hw, y: hh, width: vw - hw, height: vh - hh };
    case "center":
      return {
        x: Math.floor(vw * 0.15),
        y: Math.floor(vh * 0.1),
        width: Math.floor(vw * 0.7),
        height: Math.floor(vh * 0.8),
      };
    case "fullscreen":
      return { x: 0, y: 0, width: vw, height: vh };
  }
}

function migrateWindow(w: DesktopWindowState): DesktopWindowState {
  const tab: WindowTab = {
    id: w.activeTabId || `tab_${w.id}`,
    title: w.title,
    path: w.path,
    pinned: false,
  };
  const mode: WindowMode = w.minimized
    ? "minimized"
    : w.fullscreen
      ? "fullscreen"
      : w.maximized
        ? "maximized"
        : w.snapRegion
          ? "snapped"
          : w.mode || "floating";
  return {
    ...w,
    mode,
    floating: mode === "floating",
    snapRegion: w.snapRegion ?? null,
    alwaysOnTop: w.alwaysOnTop ?? false,
    fullscreen: w.fullscreen ?? false,
    tabs: w.tabs?.length ? w.tabs : [tab],
    activeTabId: w.activeTabId || tab.id,
    split: w.split ?? null,
    splitSecondaryTabId: w.splitSecondaryTabId ?? null,
    closedTabStack: w.closedTabStack || [],
    workspaceId: w.workspaceId,
  };
}

function readSnap(): DesktopSessionSnapshot | null {
  try {
    const raw = localStorage.getItem(DESKTOP_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DesktopSessionSnapshot;
    if (parsed.version !== 1 && parsed.version !== 2) return null;
    return parsed;
  } catch {
    return null;
  }
}

function nextGeometry(windows: DesktopWindowState[], z: number) {
  const n = windows.filter((w) => !w.minimized).length;
  return {
    x: 80 + (n % 6) * CASCADE,
    y: 60 + (n % 5) * CASCADE,
    width: 880,
    height: 560,
    zIndex: z,
  };
}

function clampWin(w: DesktopWindowState): DesktopWindowState {
  const { width: vw, height: vh } = viewport();
  return {
    ...w,
    width: Math.max(MIN_W, Math.min(w.width, vw)),
    height: Math.max(MIN_H, Math.min(w.height, vh)),
    x: Math.max(0, Math.min(w.x, Math.max(0, vw - 80))),
    y: Math.max(0, Math.min(w.y, Math.max(0, vh - 40))),
  };
}

function pathKey(path: string) {
  return path;
}

function highestVisible(windows: DesktopWindowState[]): string | null {
  const open = windows.filter((w) => !w.minimized).sort((a, b) => b.zIndex - a.zIndex);
  return open[0]?.id || null;
}

function activePath(w: DesktopWindowState): string {
  const tab = w.tabs?.find((t) => t.id === w.activeTabId);
  return tab?.path || w.path;
}

type DesktopState = {
  hydrated: boolean;
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
  zCounter: number;
  closedStack: DesktopWindowState[];
  workspaceProfiles: WorkspaceProfile[];
  activeWorkspaceProfileId: string | null;
  inspectorOpen: boolean;
  snapPreview: SnapPreview;
  hydrate: () => void;
  persist: () => void;
  setWallpaper: (id: WallpaperId) => void;
  setLayout: (id: DesktopLayoutId) => void;
  setLauncherOpen: (open: boolean) => void;
  setProfile: (id: string) => void;
  setActiveWorkspaceId: (id: string) => void;
  setInspectorOpen: (open: boolean) => void;
  moveIcon: (id: string, x: number, y: number) => void;
  openApp: (appIdOrPath: string, opts?: OpenAppOptions) => string;
  focusWindow: (id: string) => void;
  closeWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  restoreWindow: (id: string) => void;
  maximizeWindow: (id: string) => void;
  toggleMaximize: (id: string) => void;
  setFullscreen: (id: string, on?: boolean) => void;
  snapWindow: (id: string, side: SnapRegion | "left" | "right" | "fullscreen") => void;
  centerRestore: (id: string) => void;
  setSnapPreview: (preview: SnapPreview) => void;
  detectSnapFromPoint: (clientX: number, clientY: number) => SnapPreview;
  moveWindow: (id: string, x: number, y: number) => void;
  resizeWindow: (id: string, width: number, height: number, x?: number, y?: number) => void;
  cycleWindows: (dir: 1 | -1) => void;
  pinDockApp: (appId: string) => void;
  unpinDockApp: (appId: string) => void;
  reopenClosed: () => string | null;
  addTab: (windowId: string, path: string, title: string) => string;
  activateTab: (windowId: string, tabId: string) => void;
  closeTab: (windowId: string, tabId: string) => void;
  reorderTabs: (windowId: string, from: number, to: number) => void;
  pinTab: (windowId: string, tabId: string) => void;
  duplicateTab: (windowId: string, tabId: string) => void;
  reopenClosedTab: (windowId: string) => void;
  detachTab: (windowId: string, tabId: string) => string | null;
  mergeWindows: (sourceId: string, targetId: string) => void;
  setSplit: (windowId: string, orientation: "horizontal" | "vertical" | null, secondaryTabId?: string) => void;
  saveWorkspaceProfile: (name: string) => string;
  restoreWorkspaceProfile: (id: string) => void;
  applyWorkspaceTemplate: (templateId: WorkspaceTemplateId) => void;
  listWorkspaceProfiles: () => WorkspaceProfile[];
};

export const useDesktopStore = create<DesktopState>((set, get) => ({
  hydrated: false,
  wallpaperId: "aurora",
  layoutId: "default",
  icons: defaultIcons("default"),
  windows: [],
  focusedId: null,
  dock: defaultDock(),
  recentAppIds: [],
  launcherOpen: false,
  profileId: "ceo",
  activeWorkspaceId: "ws_default",
  zCounter: Z_BASE,
  closedStack: [],
  workspaceProfiles: seedWorkspaceProfiles(),
  activeWorkspaceProfileId: "wp_default",
  inspectorOpen: false,
  snapPreview: null,

  hydrate: () => {
    if (get().hydrated) return;
    const snap = typeof window !== "undefined" ? readSnap() : null;
    if (snap) {
      const windows = (snap.windows || []).map(migrateWindow);
      set({
        wallpaperId: snap.wallpaperId || "aurora",
        layoutId: snap.layoutId || "default",
        icons: snap.icons?.length ? snap.icons : defaultIcons(snap.layoutId || "default"),
        windows,
        focusedId: snap.focusedId,
        dock: snap.dock?.length ? snap.dock : defaultDock(),
        recentAppIds: snap.recentAppIds || [],
        launcherOpen: false,
        profileId: snap.profileId || "ceo",
        activeWorkspaceId: snap.activeWorkspaceId || "ws_default",
        zCounter: Math.max(Z_BASE, ...windows.map((w) => w.zIndex), Z_BASE) + 1,
        hydrated: true,
        closedStack: [],
        workspaceProfiles: snap.workspaceProfiles?.length
          ? snap.workspaceProfiles
          : seedWorkspaceProfiles(),
        activeWorkspaceProfileId: snap.activeWorkspaceProfileId || "wp_default",
        inspectorOpen: false,
        snapPreview: null,
      });
      return;
    }
    set({ hydrated: true });
    get().persist();
  },

  persist: () => {
    const s = get();
    const snap: DesktopSessionSnapshot = {
      version: 2,
      wallpaperId: s.wallpaperId,
      layoutId: s.layoutId,
      icons: s.icons,
      windows: s.windows,
      focusedId: s.focusedId,
      dock: s.dock,
      recentAppIds: s.recentAppIds,
      launcherOpen: false,
      profileId: s.profileId,
      activeWorkspaceId: s.activeWorkspaceId,
      workspaceProfiles: s.workspaceProfiles,
      activeWorkspaceProfileId: s.activeWorkspaceProfileId,
      inspectorOpen: false,
      updatedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(DESKTOP_SESSION_KEY, JSON.stringify(snap));
    } catch {
      /* ignore */
    }
  },

  setWallpaper: (id) => {
    set({ wallpaperId: id });
    get().persist();
  },

  setLayout: (id) => {
    set({ layoutId: id, icons: defaultIcons(id) });
    get().persist();
  },

  setLauncherOpen: (open) => set({ launcherOpen: open }),

  setProfile: (id) => {
    set({ profileId: id });
    get().persist();
  },

  setActiveWorkspaceId: (id) => {
    set({ activeWorkspaceId: id });
    get().persist();
  },

  setInspectorOpen: (open) => set({ inspectorOpen: open }),

  moveIcon: (id, x, y) => {
    set((s) => ({
      icons: s.icons.map((i) => (i.id === id ? { ...i, x: Math.max(0, x), y: Math.max(0, y) } : i)),
    }));
    get().persist();
  },

  openApp: (appIdOrPath, opts) => {
    const app = appById(appIdOrPath) || appByPath(appIdOrPath);
    const path = app?.path || (appIdOrPath.startsWith("/") ? appIdOrPath : "/dashboard");
    const title = app?.label || path;
    const appId = app?.id || path;

    if (opts?.asTab && opts.targetWindowId) {
      return get().addTab(opts.targetWindowId, path, title);
    }
    if (opts?.asTab && get().focusedId) {
      return get().addTab(get().focusedId!, path, title);
    }

    const matchExact = opts?.exactPath !== false;
    const existing = !opts?.forceNew
      ? get().windows.find((w) => {
          if (w.minimized) return false;
          if (matchExact) {
            return pathKey(activePath(w)) === pathKey(path) || pathKey(w.path) === pathKey(path);
          }
          return w.appId === appId;
        })
      : undefined;
    if (existing) {
      get().focusWindow(existing.id);
      try {
        enterpriseEventBus.openModule(path, "desktop", { appId, windowId: existing.id, focused: true });
      } catch {
        /* ignore */
      }
      return existing.id;
    }

    const minimized = !opts?.forceNew
      ? get().windows.find((w) => pathKey(w.path) === pathKey(path) && w.minimized)
      : undefined;
    if (minimized) {
      get().restoreWindow(minimized.id);
      return minimized.id;
    }

    const z = get().zCounter + 1;
    const geo = nextGeometry(get().windows, z);
    const tabId = uid("tab");
    const win: DesktopWindowState = clampWin({
      id: uid("win"),
      appId,
      title,
      path,
      ...geo,
      minimized: false,
      maximized: false,
      mode: "floating",
      floating: true,
      snapRegion: null,
      alwaysOnTop: false,
      fullscreen: false,
      workspaceId: get().activeWorkspaceId,
      tabs: [{ id: tabId, title, path, pinned: false }],
      activeTabId: tabId,
      split: null,
      closedTabStack: [],
    });
    set((s) => ({
      windows: [...s.windows, win],
      focusedId: win.id,
      zCounter: z,
      launcherOpen: false,
      recentAppIds: [appId, ...s.recentAppIds.filter((id) => id !== appId)].slice(0, 12),
      dock: s.dock.some((d) => d.appId === appId) ? s.dock : [...s.dock, { appId, pinned: false }],
    }));
    get().persist();
    try {
      enterpriseEventBus.openModule(path, "desktop", { appId, windowId: win.id, multiStudio: true });
    } catch {
      /* hub optional during tests */
    }
    return win.id;
  },

  focusWindow: (id) => {
    const target = get().windows.find((w) => w.id === id);
    const z = Math.min((target?.alwaysOnTop ? Z_AOT : Z_BASE) + (get().zCounter % 40) + 1, Z_MODAL - 1);
    set((s) => ({
      focusedId: id,
      zCounter: Math.max(s.zCounter, z),
      windows: s.windows.map((w) =>
        w.id === id
          ? { ...w, zIndex: z, minimized: false, mode: w.mode === "minimized" ? "floating" : w.mode }
          : w,
      ),
    }));
    get().persist();
  },

  closeWindow: (id) => {
    const target = get().windows.find((w) => w.id === id);
    set((s) => {
      const next = s.windows.filter((w) => w.id !== id);
      return {
        windows: next,
        focusedId: s.focusedId === id ? highestVisible(next) : s.focusedId,
        closedStack: target ? [target, ...s.closedStack].slice(0, 20) : s.closedStack,
        dock: s.dock.filter((d) => d.pinned || next.some((w) => w.appId === d.appId)),
      };
    });
    get().persist();
  },

  minimizeWindow: (id) => {
    set((s) => {
      const windows = s.windows.map((w) =>
        w.id === id ? { ...w, minimized: true, mode: "minimized" as const } : w,
      );
      return { windows, focusedId: s.focusedId === id ? highestVisible(windows) : s.focusedId };
    });
    get().persist();
  },

  restoreWindow: (id) => {
    const z = get().zCounter + 1;
    set((s) => ({
      zCounter: z,
      focusedId: id,
      windows: s.windows.map((w) => {
        if (w.id !== id) return w;
        const r = w.restore;
        const restored = r
          ? { x: r.x, y: r.y, width: r.width, height: r.height }
          : { x: w.x, y: w.y, width: w.width, height: w.height };
        return clampWin({
          ...w,
          ...restored,
          minimized: false,
          maximized: false,
          fullscreen: false,
          mode: "floating",
          floating: true,
          snapRegion: null,
          zIndex: z,
          restore: undefined,
        });
      }),
    }));
    get().persist();
  },

  maximizeWindow: (id) => {
    const z = get().zCounter + 1;
    const vp = viewport();
    set((s) => ({
      zCounter: z,
      focusedId: id,
      windows: s.windows.map((w) => {
        if (w.id !== id) return w;
        if (w.maximized || w.mode === "maximized") {
          const r = w.restore;
          return clampWin({
            ...w,
            maximized: false,
            fullscreen: false,
            mode: "floating",
            floating: true,
            snapRegion: null,
            zIndex: z,
            minimized: false,
            x: r?.x ?? w.x,
            y: r?.y ?? w.y,
            width: r?.width ?? w.width,
            height: r?.height ?? w.height,
            restore: undefined,
          });
        }
        return {
          ...w,
          maximized: true,
          minimized: false,
          fullscreen: false,
          mode: "maximized",
          floating: false,
          snapRegion: null,
          zIndex: z,
          restore: w.restore || { x: w.x, y: w.y, width: w.width, height: w.height },
          x: 0,
          y: 0,
          width: vp.width,
          height: vp.height,
        };
      }),
    }));
    get().persist();
  },

  toggleMaximize: (id) => get().maximizeWindow(id),

  setFullscreen: (id, on) => {
    const z = get().zCounter + 1;
    const vp = viewport();
    set((s) => ({
      zCounter: z,
      focusedId: id,
      windows: s.windows.map((w) => {
        if (w.id !== id) return w;
        const enable = on ?? !w.fullscreen;
        if (!enable) {
          const r = w.restore;
          return clampWin({
            ...w,
            fullscreen: false,
            maximized: false,
            mode: "floating",
            floating: true,
            zIndex: z,
            x: r?.x ?? w.x,
            y: r?.y ?? w.y,
            width: r?.width ?? w.width,
            height: r?.height ?? w.height,
            restore: undefined,
          });
        }
        return {
          ...w,
          fullscreen: true,
          maximized: true,
          minimized: false,
          mode: "fullscreen",
          floating: false,
          zIndex: z,
          restore: w.restore || { x: w.x, y: w.y, width: w.width, height: w.height },
          ...vp,
        };
      }),
    }));
    get().persist();
  },

  snapWindow: (id, side) => {
    const region = side as SnapRegion;
    const bounds = snapBounds(region);
    const z = get().zCounter + 1;
    set((s) => ({
      zCounter: z,
      focusedId: id,
      snapPreview: null,
      windows: s.windows.map((w) => {
        if (w.id !== id) return w;
        const restore = w.restore || { x: w.x, y: w.y, width: w.width, height: w.height };
        if (region === "fullscreen") {
          return {
            ...w,
            ...bounds,
            maximized: true,
            fullscreen: true,
            minimized: false,
            mode: "fullscreen",
            floating: false,
            snapRegion: "fullscreen",
            zIndex: z,
            restore,
          };
        }
        if (region === "center") {
          return clampWin({
            ...w,
            ...bounds,
            maximized: false,
            fullscreen: false,
            minimized: false,
            mode: "floating",
            floating: true,
            snapRegion: null,
            zIndex: z,
            restore: undefined,
          });
        }
        return clampWin({
          ...w,
          ...bounds,
          maximized: false,
          fullscreen: false,
          minimized: false,
          mode: "snapped",
          floating: false,
          snapRegion: region,
          zIndex: z,
          restore,
        });
      }),
    }));
    get().persist();
  },

  centerRestore: (id) => get().snapWindow(id, "center"),

  setSnapPreview: (preview) => set({ snapPreview: preview }),

  detectSnapFromPoint: (clientX, clientY) => {
    const { width: vw, height: vh } = viewport();
    const edge = 28;
    let region: SnapRegion | null = null;
    if (clientX <= edge && clientY <= edge) region = "top-left";
    else if (clientX >= vw - edge && clientY <= edge) region = "top-right";
    else if (clientX <= edge && clientY >= vh - edge) region = "bottom-left";
    else if (clientX >= vw - edge && clientY >= vh - edge) region = "bottom-right";
    else if (clientX <= edge) region = "left";
    else if (clientX >= vw - edge) region = "right";
    else if (clientY <= edge) region = "top";
    else if (clientY >= vh - edge) region = "bottom";
    if (!region) return null;
    return { region, bounds: snapBounds(region) };
  },

  moveWindow: (id, x, y) => {
    set((s) => ({
      windows: s.windows.map((w) =>
        w.id === id && !w.maximized && !w.fullscreen
          ? { ...w, x: Math.max(0, x), y: Math.max(0, y), mode: "floating", floating: true, snapRegion: null }
          : w,
      ),
    }));
  },

  resizeWindow: (id, width, height, x, y) => {
    set((s) => ({
      windows: s.windows.map((w) =>
        w.id === id && !w.maximized && !w.fullscreen
          ? clampWin({
              ...w,
              width,
              height,
              x: x ?? w.x,
              y: y ?? w.y,
              mode: "floating",
              floating: true,
              snapRegion: null,
            })
          : w,
      ),
    }));
  },

  cycleWindows: (dir) => {
    const open = get().windows.filter((w) => !w.minimized).sort((a, b) => a.zIndex - b.zIndex);
    if (!open.length) return;
    const idx = open.findIndex((w) => w.id === get().focusedId);
    const next = open[(idx + dir + open.length) % open.length];
    if (next) get().focusWindow(next.id);
  },

  pinDockApp: (appId) => {
    set((s) => {
      const exists = s.dock.find((d) => d.appId === appId);
      const dock = exists
        ? s.dock.map((d) => (d.appId === appId ? { ...d, pinned: true } : d))
        : [...s.dock, { appId, pinned: true }];
      return { dock };
    });
    get().persist();
  },

  unpinDockApp: (appId) => {
    set((s) => ({
      dock: s.dock
        .map((d) => (d.appId === appId ? { ...d, pinned: false } : d))
        .filter((d) => d.pinned || s.windows.some((w) => w.appId === d.appId)),
    }));
    get().persist();
  },

  reopenClosed: () => {
    const [first, ...rest] = get().closedStack;
    if (!first) return null;
    set({ closedStack: rest });
    return get().openApp(first.path || first.appId, { forceNew: true, exactPath: true });
  },

  addTab: (windowId, path, title) => {
    const tabId = uid("tab");
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== windowId) return w;
        const tabs = [...(w.tabs || []), { id: tabId, title, path, pinned: false }];
        return { ...w, tabs, activeTabId: tabId, path, title };
      }),
      focusedId: windowId,
    }));
    get().persist();
    return tabId;
  },

  activateTab: (windowId, tabId) => {
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== windowId) return w;
        const tab = w.tabs?.find((t) => t.id === tabId);
        if (!tab) return w;
        return { ...w, activeTabId: tabId, path: tab.path, title: tab.title };
      }),
      focusedId: windowId,
    }));
    get().persist();
  },

  closeTab: (windowId, tabId) => {
    set((s) => {
      const windows = s.windows.flatMap((w) => {
        if (w.id !== windowId) return [w];
        const tabs = w.tabs || [];
        const closing = tabs.find((t) => t.id === tabId);
        const nextTabs = tabs.filter((t) => t.id !== tabId);
        if (!nextTabs.length) return [];
        const active = nextTabs.find((t) => t.id === w.activeTabId) || nextTabs[0]!;
        return [
          {
            ...w,
            tabs: nextTabs,
            activeTabId: active.id,
            path: active.path,
            title: active.title,
            closedTabStack: closing
              ? [closing, ...(w.closedTabStack || [])].slice(0, 20)
              : w.closedTabStack,
          },
        ];
      });
      return {
        windows,
        focusedId: windows.some((w) => w.id === windowId) ? windowId : highestVisible(windows),
      };
    });
    get().persist();
  },

  reorderTabs: (windowId, from, to) => {
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== windowId || !w.tabs) return w;
        const tabs = [...w.tabs];
        const [item] = tabs.splice(from, 1);
        if (!item) return w;
        tabs.splice(to, 0, item);
        return { ...w, tabs };
      }),
    }));
    get().persist();
  },

  pinTab: (windowId, tabId) => {
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== windowId) return w;
        return { ...w, tabs: w.tabs?.map((t) => (t.id === tabId ? { ...t, pinned: !t.pinned } : t)) };
      }),
    }));
    get().persist();
  },

  duplicateTab: (windowId, tabId) => {
    const w = get().windows.find((x) => x.id === windowId);
    const tab = w?.tabs?.find((t) => t.id === tabId);
    if (!tab) return;
    get().addTab(windowId, tab.path, `${tab.title} copy`);
  },

  reopenClosedTab: (windowId) => {
    const w = get().windows.find((x) => x.id === windowId);
    const [first, ...rest] = w?.closedTabStack || [];
    if (!first) return;
    const newId = uid("tab");
    set((s) => ({
      windows: s.windows.map((win) => {
        if (win.id !== windowId) return win;
        return {
          ...win,
          closedTabStack: rest,
          tabs: [...(win.tabs || []), { ...first, id: newId }],
          activeTabId: newId,
          path: first.path,
          title: first.title,
        };
      }),
    }));
    get().persist();
  },

  detachTab: (windowId, tabId) => {
    const w = get().windows.find((x) => x.id === windowId);
    const tab = w?.tabs?.find((t) => t.id === tabId);
    if (!w || !tab || (w.tabs?.length || 0) <= 1) return null;
    get().closeTab(windowId, tabId);
    return get().openApp(tab.path, { forceNew: true, exactPath: true });
  },

  mergeWindows: (sourceId, targetId) => {
    if (sourceId === targetId) return;
    const source = get().windows.find((w) => w.id === sourceId);
    const target = get().windows.find((w) => w.id === targetId);
    if (!source || !target) return;
    const tabs = [...(target.tabs || []), ...(source.tabs || [])];
    set((s) => ({
      windows: s.windows
        .filter((w) => w.id !== sourceId)
        .map((w) =>
          w.id === targetId
            ? {
                ...w,
                tabs,
                activeTabId: source.activeTabId || w.activeTabId,
                path: source.path,
                title: source.title,
              }
            : w,
        ),
      focusedId: targetId,
      closedStack: [source, ...s.closedStack].slice(0, 20),
    }));
    get().persist();
  },

  setSplit: (windowId, orientation, secondaryTabId) => {
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== windowId) return w;
        const secondary = secondaryTabId || w.tabs?.find((t) => t.id !== w.activeTabId)?.id || null;
        return { ...w, split: orientation, splitSecondaryTabId: orientation ? secondary : null };
      }),
    }));
    get().persist();
  },

  saveWorkspaceProfile: (name) => {
    const s = get();
    const id = uid("wp");
    const profile = profileFromState({
      id,
      name,
      windows: s.windows,
      focusedId: s.focusedId,
      dock: s.dock,
      wallpaperId: s.wallpaperId,
      layoutId: s.layoutId,
    });
    set((st) => ({
      workspaceProfiles: [profile, ...st.workspaceProfiles].slice(0, 12),
      activeWorkspaceProfileId: id,
    }));
    get().persist();
    return id;
  },

  restoreWorkspaceProfile: (id) => {
    const profile = get().workspaceProfiles.find((p) => p.id === id);
    if (!profile) return;
    const windows = profile.windows.map(migrateWindow);
    set({
      windows,
      focusedId: profile.focusedId,
      dock: profile.dock.length ? profile.dock : defaultDock(),
      wallpaperId: profile.wallpaperId,
      layoutId: profile.layoutId,
      icons: defaultIcons(profile.layoutId),
      activeWorkspaceProfileId: id,
      zCounter: Math.max(Z_BASE, ...windows.map((w) => w.zIndex), Z_BASE) + 1,
    });
    get().persist();
  },

  applyWorkspaceTemplate: (templateId) => {
    const tpl = WORKSPACE_TEMPLATES.find((t) => t.id === templateId);
    if (!tpl) return;
    set({
      windows: [],
      focusedId: null,
      wallpaperId: tpl.wallpaperId,
      layoutId: tpl.layoutId,
      icons: defaultIcons(tpl.layoutId),
    });
    for (const appId of tpl.appIds) {
      get().openApp(appId, { forceNew: true, exactPath: true });
    }
    get().saveWorkspaceProfile(tpl.name);
  },

  listWorkspaceProfiles: () => get().workspaceProfiles.slice(),
}));
