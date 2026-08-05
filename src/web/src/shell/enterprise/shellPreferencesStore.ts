/**
 * Shell preferences — Sprint 28.5.
 * Favorites · pins · recents · categories collapse · sidebar state.
 */

import { create } from "zustand";

export const SHELL_PREFS_KEY = "ews_shell_prefs_v1";

type ShellPrefsSnapshot = {
  version: 1;
  favorites: string[];
  pinned: string[];
  recentModuleIds: string[];
  collapsedCategories: string[];
  sidebarCollapsed: boolean;
  updatedAt: string;
};

type ShellPrefsState = ShellPrefsSnapshot & {
  hydrated: boolean;
  hydrate: () => void;
  persist: () => void;
  toggleFavorite: (moduleId: string) => void;
  togglePin: (moduleId: string) => void;
  rememberModule: (moduleId: string) => void;
  toggleCategory: (category: string) => void;
  setSidebarCollapsed: (v: boolean) => void;
};

function read(): ShellPrefsSnapshot | null {
  try {
    const raw = localStorage.getItem(SHELL_PREFS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ShellPrefsSnapshot;
    if (parsed.version !== 1) return null;
    return parsed;
  } catch {
    return null;
  }
}

export const useShellPreferences = create<ShellPrefsState>((set, get) => ({
  hydrated: false,
  version: 1,
  favorites: [],
  pinned: ["dashboard", "desktop", "ai_studio", "city"],
  recentModuleIds: [],
  collapsedCategories: [],
  sidebarCollapsed: false,
  updatedAt: new Date().toISOString(),

  hydrate: () => {
    if (get().hydrated) return;
    const snap = typeof window !== "undefined" ? read() : null;
    if (snap) {
      set({ ...snap, hydrated: true });
      return;
    }
    set({ hydrated: true });
    get().persist();
  },

  persist: () => {
    const s = get();
    const snap: ShellPrefsSnapshot = {
      version: 1,
      favorites: s.favorites,
      pinned: s.pinned,
      recentModuleIds: s.recentModuleIds,
      collapsedCategories: s.collapsedCategories,
      sidebarCollapsed: s.sidebarCollapsed,
      updatedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(SHELL_PREFS_KEY, JSON.stringify(snap));
    } catch {
      /* ignore */
    }
  },

  toggleFavorite: (moduleId) => {
    set((s) => ({
      favorites: s.favorites.includes(moduleId)
        ? s.favorites.filter((id) => id !== moduleId)
        : [moduleId, ...s.favorites].slice(0, 24),
    }));
    get().persist();
  },

  togglePin: (moduleId) => {
    set((s) => ({
      pinned: s.pinned.includes(moduleId)
        ? s.pinned.filter((id) => id !== moduleId)
        : [...s.pinned, moduleId].slice(0, 16),
    }));
    get().persist();
  },

  rememberModule: (moduleId) => {
    const cur = get().recentModuleIds;
    if (cur[0] === moduleId) return;
    set({
      recentModuleIds: [moduleId, ...cur.filter((id) => id !== moduleId)].slice(0, 16),
    });
    get().persist();
  },

  toggleCategory: (category) => {
    set((s) => ({
      collapsedCategories: s.collapsedCategories.includes(category)
        ? s.collapsedCategories.filter((c) => c !== category)
        : [...s.collapsedCategories, category],
    }));
    get().persist();
  },

  setSidebarCollapsed: (v) => {
    if (get().sidebarCollapsed === v) return;
    set({ sidebarCollapsed: v });
    get().persist();
  },
}));
