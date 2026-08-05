import { beforeEach, describe, expect, it } from "vitest";
import { useDesktopStore } from "./desktopStore";
import { DESKTOP_APPS, DESKTOP_LAYOUTS, WALLPAPERS } from "./desktopCatalog";
import { DESKTOP_SESSION_KEY, DESKTOP_WM_VERSION } from "./types";
import { WORKSPACE_TEMPLATES } from "./workspaceProfiles";
import { DESKTOP_SHORTCUTS } from "./shortcutCatalog";

describe("Sprint 27.7 / 28.4 enterprise desktop window manager", () => {
  beforeEach(() => {
    localStorage.removeItem(DESKTOP_SESSION_KEY);
    useDesktopStore.setState({
      hydrated: false,
      wallpaperId: "aurora",
      layoutId: "default",
      icons: [],
      windows: [],
      focusedId: null,
      dock: [],
      recentAppIds: [],
      launcherOpen: false,
      profileId: "ceo",
      activeWorkspaceId: "ws_default",
      zCounter: 20,
      closedStack: [],
      workspaceProfiles: [],
      activeWorkspaceProfileId: null,
      inspectorOpen: false,
      snapPreview: null,
    });
  });

  it("exposes launcher apps and wallpapers", () => {
    expect(DESKTOP_WM_VERSION).toBe("28.4");
    expect(DESKTOP_APPS.length).toBeGreaterThanOrEqual(12);
    expect(DESKTOP_APPS.map((a) => a.id)).toEqual(
      expect.arrayContaining([
        "crm",
        "ai_studio",
        "production",
        "prod_image",
        "workflow_studio",
        "agent_studio",
        "city",
      ]),
    );
    expect(Object.keys(WALLPAPERS)).toEqual(
      expect.arrayContaining(["aurora", "slate", "studio", "midnight", "plain"]),
    );
    expect(Object.keys(DESKTOP_LAYOUTS)).toEqual(
      expect.arrayContaining(["default", "ops", "sales", "dev"]),
    );
    expect(DESKTOP_SHORTCUTS.length).toBeGreaterThan(8);
    expect(WORKSPACE_TEMPLATES.map((t) => t.id)).toEqual(
      expect.arrayContaining(["blank", "ops", "creative", "dev", "executive"]),
    );
  });

  it("opens focuses minimizes snaps and restores windows", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    const id = store.openApp("crm");
    expect(useDesktopStore.getState().windows).toHaveLength(1);
    expect(useDesktopStore.getState().focusedId).toBe(id);
    expect(useDesktopStore.getState().windows[0]!.tabs?.length).toBe(1);

    store.minimizeWindow(id);
    expect(useDesktopStore.getState().windows[0]!.mode).toBe("minimized");

    store.restoreWindow(id);
    expect(useDesktopStore.getState().windows[0]!.minimized).toBe(false);

    store.snapWindow(id, "left");
    const left = useDesktopStore.getState().windows[0]!;
    expect(left.x).toBe(0);
    expect(left.mode).toBe("snapped");

    store.snapWindow(id, "top-right");
    expect(useDesktopStore.getState().windows[0]!.snapRegion).toBe("top-right");

    store.centerRestore(id);
    expect(useDesktopStore.getState().windows[0]!.mode).toBe("floating");

    store.maximizeWindow(id);
    expect(useDesktopStore.getState().windows[0]!.maximized).toBe(true);
  });

  it("supports multi-studio simultaneous windows by exact path", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    const a = store.openApp("prod_image", { forceNew: true, exactPath: true });
    const b = store.openApp("prod_video", { forceNew: true, exactPath: true });
    const c = store.openApp("ai_studio", { forceNew: true, exactPath: true });
    expect(new Set([a, b, c]).size).toBe(3);
    expect(useDesktopStore.getState().windows).toHaveLength(3);
  });

  it("manages window tabs detach and merge", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    const win = store.openApp("ai_studio", { forceNew: true });
    store.addTab(win, "/ai-studio?studio=image", "Image");
    expect(useDesktopStore.getState().windows[0]!.tabs).toHaveLength(2);
    store.activateTab(win, useDesktopStore.getState().windows[0]!.tabs![1]!.id);
    store.duplicateTab(win, useDesktopStore.getState().windows[0]!.activeTabId!);
    expect(useDesktopStore.getState().windows[0]!.tabs!.length).toBeGreaterThanOrEqual(3);
    const tabId = useDesktopStore.getState().windows[0]!.tabs![1]!.id;
    const detached = store.detachTab(win, tabId);
    expect(detached).toBeTruthy();
    expect(useDesktopStore.getState().windows.length).toBeGreaterThanOrEqual(2);
    const ids = useDesktopStore.getState().windows.map((w) => w.id);
    store.mergeWindows(ids[1]!, ids[0]!);
    expect(useDesktopStore.getState().windows).toHaveLength(1);
  });

  it("saves and restores workspace profiles", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    store.openApp("dashboard", { forceNew: true });
    store.openApp("crm", { forceNew: true });
    const pid = store.saveWorkspaceProfile("Ops desk");
    store.closeWindow(useDesktopStore.getState().windows[0]!.id);
    expect(useDesktopStore.getState().windows.length).toBeLessThan(2);
    store.restoreWorkspaceProfile(pid);
    expect(useDesktopStore.getState().windows.length).toBeGreaterThanOrEqual(2);
  });

  it("persists session v2 and migrates windows", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    store.openApp("dashboard");
    store.setWallpaper("midnight");
    store.persist();
    const raw = JSON.parse(localStorage.getItem(DESKTOP_SESSION_KEY)!);
    expect(raw.version).toBe(2);
    useDesktopStore.setState({ hydrated: false, windows: [] });
    useDesktopStore.getState().hydrate();
    expect(useDesktopStore.getState().wallpaperId).toBe("midnight");
    expect(useDesktopStore.getState().windows[0]!.tabs?.length).toBe(1);
  });

  it("detects snap preview regions", () => {
    const store = useDesktopStore.getState();
    store.hydrate();
    expect(store.detectSnapFromPoint(5, 100)?.region).toBe("left");
    expect(store.detectSnapFromPoint(window.innerWidth - 5, 100)?.region).toBe("right");
    expect(store.detectSnapFromPoint(5, 5)?.region).toBe("top-left");
  });
});
