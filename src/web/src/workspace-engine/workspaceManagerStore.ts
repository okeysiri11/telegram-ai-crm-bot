import { create } from "zustand";
import { ENTERPRISE_SHELL_NAV } from "@/shell/enterprise/enterpriseNav";
import {
  MAX_CLOSED_TABS,
  WORKSPACE_SESSION_KEY,
  type WorkspaceSessionSnapshot,
  type WorkspaceTab,
} from "./types";
import { logActivity } from "./activityJournal";

function titleForPath(path: string): string {
  const clean = path.split("?")[0] || path;
  const hit = ENTERPRISE_SHELL_NAV.find(
    (n) => clean === n.route || (n.route !== "/dashboard" && clean.startsWith(n.route)),
  );
  if (hit) return hit.label;
  const seg = clean.split("/").filter(Boolean).pop() || "Workspace";
  return seg.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function moduleIdForPath(path: string): string | undefined {
  const clean = path.split("?")[0] || path;
  return ENTERPRISE_SHELL_NAV.find(
    (n) => clean === n.route || (n.route !== "/dashboard" && clean.startsWith(n.route)),
  )?.id;
}

function newTab(path: string, pinned = false): WorkspaceTab {
  return {
    id: `tab_${Math.random().toString(36).slice(2, 10)}`,
    title: titleForPath(path),
    path,
    moduleId: moduleIdForPath(path),
    pinned,
    openedAt: new Date().toISOString(),
  };
}

function readSnapshot(): WorkspaceSessionSnapshot | null {
  try {
    const raw = localStorage.getItem(WORKSPACE_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as WorkspaceSessionSnapshot;
    if ((parsed.version !== 1 && parsed.version !== 2) || !Array.isArray(parsed.tabs)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function persist(state: {
  activeWorkspaceId: string;
  activeTabId: string | null;
  tabs: WorkspaceTab[];
  closedTabs: WorkspaceTab[];
}) {
  const snap: WorkspaceSessionSnapshot = {
    version: 2,
    activeWorkspaceId: state.activeWorkspaceId,
    activeTabId: state.activeTabId,
    tabs: state.tabs,
    closedTabs: state.closedTabs.slice(0, MAX_CLOSED_TABS),
    updatedAt: new Date().toISOString(),
  };
  try {
    localStorage.setItem(WORKSPACE_SESSION_KEY, JSON.stringify(snap));
  } catch {
    /* ignore */
  }
}

type WorkspaceManagerState = {
  activeWorkspaceId: string;
  tabs: WorkspaceTab[];
  activeTabId: string | null;
  closedTabs: WorkspaceTab[];
  hydrated: boolean;
  hydrate: () => void;
  openTab: (path: string, opts?: { activate?: boolean; pinned?: boolean }) => WorkspaceTab;
  activateTab: (id: string) => WorkspaceTab | null;
  closeTab: (id: string) => string | null;
  togglePin: (id: string) => void;
  reorderTabs: (fromId: string, toId: string) => void;
  duplicateTab: (id: string) => WorkspaceTab | null;
  reopenClosedTab: () => WorkspaceTab | null;
  syncRoute: (path: string) => void;
  setActiveWorkspace: (id: string) => void;
};

function bootstrapTabs(): { tabs: WorkspaceTab[]; activeTabId: string } {
  const dash = newTab("/dashboard", true);
  return { tabs: [dash], activeTabId: dash.id };
}

export const useWorkspaceManager = create<WorkspaceManagerState>((set, get) => ({
  activeWorkspaceId: "ws_default",
  tabs: [],
  activeTabId: null,
  closedTabs: [],
  hydrated: false,

  hydrate: () => {
    if (get().hydrated) return;
    const snap = typeof window !== "undefined" ? readSnapshot() : null;
    if (snap && snap.tabs.length) {
      set({
        activeWorkspaceId: snap.activeWorkspaceId || "ws_default",
        tabs: snap.tabs,
        activeTabId: snap.activeTabId || snap.tabs[0]!.id,
        closedTabs: snap.closedTabs || [],
        hydrated: true,
      });
      logActivity({
        kind: "system",
        title: "Workspace session restored",
        detail: `${snap.tabs.length} tab(s)`,
      });
      return;
    }
    const boot = bootstrapTabs();
    set({ ...boot, closedTabs: [], hydrated: true });
    persist({ activeWorkspaceId: "ws_default", closedTabs: [], ...boot });
  },

  openTab: (path, opts) => {
    const activate = opts?.activate !== false;
    const existing = get().tabs.find((t) => t.path.split("?")[0] === path.split("?")[0]);
    if (existing) {
      if (activate && get().activeTabId !== existing.id) {
        set((s) => {
          const next = { ...s, activeTabId: existing.id };
          persist(next);
          return next;
        });
        logActivity({ kind: "navigate", title: `Activated ${existing.title}`, detail: existing.path });
      }
      return existing;
    }
    const tab = newTab(path, opts?.pinned);
    set((s) => {
      const tabs = [...s.tabs, tab];
      const next = {
        ...s,
        tabs,
        activeTabId: activate ? tab.id : s.activeTabId,
      };
      persist(next);
      return next;
    });
    logActivity({ kind: "navigate", title: `Opened ${tab.title}`, detail: tab.path });
    return tab;
  },

  activateTab: (id) => {
    const tab = get().tabs.find((t) => t.id === id) || null;
    if (!tab) return null;
    if (get().activeTabId === id) return tab;
    set((s) => {
      const next = { ...s, activeTabId: id };
      persist(next);
      return next;
    });
    logActivity({ kind: "navigate", title: `Switched to ${tab.title}`, detail: tab.path });
    return tab;
  },

  closeTab: (id) => {
    const { tabs, activeTabId, closedTabs } = get();
    const target = tabs.find((t) => t.id === id);
    if (!target || target.pinned) return activeTabId;
    const nextTabs = tabs.filter((t) => t.id !== id);
    const nextClosed = [target, ...closedTabs.filter((t) => t.path !== target.path)].slice(0, MAX_CLOSED_TABS);
    let nextActive = activeTabId;
    if (activeTabId === id) {
      nextActive = nextTabs[nextTabs.length - 1]?.id || null;
    }
    if (!nextTabs.length) {
      const boot = bootstrapTabs();
      set({ tabs: boot.tabs, activeTabId: boot.activeTabId, closedTabs: nextClosed });
      persist({
        activeWorkspaceId: get().activeWorkspaceId,
        closedTabs: nextClosed,
        ...boot,
      });
      logActivity({ kind: "navigate", title: `Closed ${target.title}`, detail: target.path });
      return boot.activeTabId;
    }
    set((s) => {
      const next = { ...s, tabs: nextTabs, activeTabId: nextActive, closedTabs: nextClosed };
      persist(next);
      return next;
    });
    logActivity({ kind: "navigate", title: `Closed ${target.title}`, detail: target.path });
    return nextActive;
  },

  togglePin: (id) => {
    set((s) => {
      const tabs = s.tabs.map((t) => (t.id === id ? { ...t, pinned: !t.pinned } : t));
      const next = { ...s, tabs };
      persist(next);
      return next;
    });
  },

  reorderTabs: (fromId, toId) => {
    if (fromId === toId) return;
    set((s) => {
      const from = s.tabs.findIndex((t) => t.id === fromId);
      const to = s.tabs.findIndex((t) => t.id === toId);
      if (from < 0 || to < 0) return s;
      const tabs = [...s.tabs];
      const [moved] = tabs.splice(from, 1);
      tabs.splice(to, 0, moved!);
      const next = { ...s, tabs };
      persist(next);
      return next;
    });
  },

  duplicateTab: (id) => {
    const source = get().tabs.find((t) => t.id === id);
    if (!source) return null;
    const tab = newTab(source.path, false);
    tab.title = `${source.title} · copy`;
    set((s) => {
      const idx = s.tabs.findIndex((t) => t.id === id);
      const tabs = [...s.tabs];
      tabs.splice(idx + 1, 0, tab);
      const next = { ...s, tabs, activeTabId: tab.id };
      persist(next);
      return next;
    });
    logActivity({ kind: "navigate", title: `Duplicated ${source.title}`, detail: tab.path });
    return tab;
  },

  reopenClosedTab: () => {
    const closed = get().closedTabs;
    if (!closed.length) return null;
    const [first, ...rest] = closed;
    const tab = newTab(first!.path, first!.pinned);
    set((s) => {
      const next = {
        ...s,
        tabs: [...s.tabs, tab],
        activeTabId: tab.id,
        closedTabs: rest,
      };
      persist(next);
      return next;
    });
    logActivity({ kind: "navigate", title: `Reopened ${tab.title}`, detail: tab.path });
    return tab;
  },

  syncRoute: (path) => {
    const clean = path.split("?")[0] || path;
    if (clean.startsWith("/login") || clean.startsWith("/auth")) return;
    const { tabs, activeTabId } = get();
    const active = tabs.find((t) => t.id === activeTabId);
    if (active && (active.path.split("?")[0] === clean || active.path === path)) {
      if (active.path !== path) {
        set((s) => {
          const nextTabs = s.tabs.map((t) =>
            t.id === active.id ? { ...t, path, title: titleForPath(path) } : t,
          );
          const next = { ...s, tabs: nextTabs };
          persist(next);
          return next;
        });
      }
      return;
    }
    const existing = tabs.find((t) => t.path.split("?")[0] === clean);
    if (existing) {
      if (activeTabId !== existing.id) {
        set((s) => {
          const next = { ...s, activeTabId: existing.id };
          persist(next);
          return next;
        });
      }
      return;
    }
    get().openTab(path, { activate: true });
  },

  setActiveWorkspace: (id) => {
    if (get().activeWorkspaceId === id) return;
    set((s) => {
      const next = { ...s, activeWorkspaceId: id };
      persist(next);
      return next;
    });
    logActivity({ kind: "system", title: "Workspace switched", detail: id });
  },
}));
