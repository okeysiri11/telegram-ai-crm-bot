/**
 * Sprint 42.2 — Adaptive Enterprise Shell layout.
 * Per-role persistence: Owner / Admin / Manager / Client / Demo.
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";

export type PanelMode = "expanded" | "compact" | "hidden";

export type AdaptiveLayoutSnapshot = {
  sidebarCollapsed: boolean;
  headerCollapsed: boolean;
  activityMode: PanelMode;
  runtimeMode: PanelMode;
  focusMode: boolean;
  /** Pre-focus restore */
  preFocus?: Omit<AdaptiveLayoutSnapshot, "focusMode" | "preFocus"> | null;
};

export type LayoutRoleKey = "owner" | "administrator" | "manager" | "client" | "demo" | "default";

const STORAGE_BASE = "ewp_adaptive_shell_v1";

const DEFAULTS: AdaptiveLayoutSnapshot = {
  sidebarCollapsed: false,
  headerCollapsed: false,
  activityMode: "hidden",
  runtimeMode: "compact",
  focusMode: false,
  preFocus: null,
};

type Vault = Record<string, AdaptiveLayoutSnapshot>;

function storageKey() {
  return wsKey(STORAGE_BASE);
}

function readVault(): Vault {
  try {
    return JSON.parse(localStorage.getItem(storageKey()) || "{}") as Vault;
  } catch {
    return {};
  }
}

function writeVault(v: Vault) {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(v));
  } catch {
    /* ignore */
  }
}

export function normalizeLayoutRole(roleId: string | null | undefined): LayoutRoleKey {
  if (!roleId) return "default";
  if (roleId === "owner" || roleId === "platform_owner") return "owner";
  if (roleId === "administrator" || roleId === "admin") return "administrator";
  if (roleId === "manager" || roleId === "sales" || roleId === "support") return "manager";
  if (roleId === "client") return "client";
  if (roleId === "demo" || roleId.includes("demo")) return "demo";
  return "default";
}

function loadForRole(role: LayoutRoleKey): AdaptiveLayoutSnapshot {
  const vault = readVault();
  const snap = vault[role];
  if (!snap) return { ...DEFAULTS };
  return {
    ...DEFAULTS,
    ...snap,
    preFocus: snap.preFocus ?? null,
  };
}

type AdaptiveState = AdaptiveLayoutSnapshot & {
  roleKey: LayoutRoleKey;
  hydrateForRole: (roleId: string | null | undefined) => void;
  persist: () => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
  setHeaderCollapsed: (v: boolean) => void;
  toggleHeader: () => void;
  setActivityMode: (m: PanelMode) => void;
  cycleActivity: () => void;
  setRuntimeMode: (m: PanelMode) => void;
  cycleRuntime: () => void;
  setFocusMode: (v: boolean) => void;
  toggleFocusMode: () => void;
};

const PANEL_CYCLE: PanelMode[] = ["expanded", "compact", "hidden"];

function nextMode(cur: PanelMode): PanelMode {
  const i = PANEL_CYCLE.indexOf(cur);
  return PANEL_CYCLE[(i + 1) % PANEL_CYCLE.length]!;
}

function syncDom(s: AdaptiveLayoutSnapshot) {
  try {
    document.documentElement.dataset.sidebarCollapsed = s.sidebarCollapsed ? "1" : "0";
    document.documentElement.dataset.headerCollapsed = s.headerCollapsed ? "1" : "0";
    document.documentElement.dataset.activityMode = s.activityMode;
    document.documentElement.dataset.runtimeMode = s.runtimeMode;
    document.documentElement.dataset.focusMode = s.focusMode ? "1" : "0";
  } catch {
    /* ignore */
  }
}

export const useAdaptiveShellStore = create<AdaptiveState>((set, get) => {
  const initial = typeof localStorage !== "undefined" ? loadForRole("default") : { ...DEFAULTS };
  return {
    ...initial,
    roleKey: "default",

    hydrateForRole: (roleId) => {
      const key = normalizeLayoutRole(roleId);
      const snap = loadForRole(key);
      set({ ...snap, roleKey: key });
      syncDom(snap);
    },

    persist: () => {
      const s = get();
      const vault = readVault();
      vault[s.roleKey] = {
        sidebarCollapsed: s.sidebarCollapsed,
        headerCollapsed: s.headerCollapsed,
        activityMode: s.activityMode,
        runtimeMode: s.runtimeMode,
        focusMode: s.focusMode,
        preFocus: s.preFocus ?? null,
      };
      writeVault(vault);
      syncDom(s);
    },

    setSidebarCollapsed: (v) => {
      if (get().focusMode) {
        get().setFocusMode(false);
      }
      set({ sidebarCollapsed: v });
      get().persist();
    },
    toggleSidebar: () => get().setSidebarCollapsed(!get().sidebarCollapsed),

    setHeaderCollapsed: (v) => {
      if (get().focusMode) {
        get().setFocusMode(false);
      }
      set({ headerCollapsed: v });
      get().persist();
    },
    toggleHeader: () => get().setHeaderCollapsed(!get().headerCollapsed),

    setActivityMode: (m) => {
      if (get().focusMode) {
        get().setFocusMode(false);
      }
      set({ activityMode: m });
      get().persist();
    },
    cycleActivity: () => get().setActivityMode(nextMode(get().activityMode)),

    setRuntimeMode: (m) => {
      if (get().focusMode) {
        get().setFocusMode(false);
      }
      set({ runtimeMode: m });
      get().persist();
    },
    cycleRuntime: () => get().setRuntimeMode(nextMode(get().runtimeMode)),

    setFocusMode: (v) => {
      if (v) {
        const cur = get();
        set({
          focusMode: true,
          preFocus: {
            sidebarCollapsed: cur.sidebarCollapsed,
            headerCollapsed: cur.headerCollapsed,
            activityMode: cur.activityMode,
            runtimeMode: cur.runtimeMode,
          },
          sidebarCollapsed: true,
          headerCollapsed: true,
          activityMode: "hidden",
          runtimeMode: "hidden",
        });
      } else {
        const prev = get().preFocus;
        if (prev) {
          set({
            focusMode: false,
            sidebarCollapsed: prev.sidebarCollapsed,
            headerCollapsed: prev.headerCollapsed,
            activityMode: prev.activityMode,
            runtimeMode: prev.runtimeMode,
            preFocus: null,
          });
        } else {
          set({
            focusMode: false,
            sidebarCollapsed: false,
            headerCollapsed: false,
            activityMode: "compact",
            runtimeMode: "compact",
            preFocus: null,
          });
        }
      }
      get().persist();
    },
    toggleFocusMode: () => get().setFocusMode(!get().focusMode),
  };
});

export const ADAPTIVE_SHELL_KEY = STORAGE_BASE;
