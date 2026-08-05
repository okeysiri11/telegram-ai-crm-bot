import { create } from "zustand";

/** Sprint 27.4 — dock layout persistence (left / right / bottom). */
export const DOCK_LAYOUT_KEY = "ews_dock_layout_v1";
const PANEL_KEY = "ews_activity_panel_open_v1";

export type DockSide = "left" | "right" | "bottom";

export type DockPanelState = {
  open: boolean;
  collapsed: boolean;
  pinned: boolean;
  autoHide: boolean;
  /** Width (left/right) or height (bottom) in px. */
  size: number;
};

export type DockLayout = {
  left: DockPanelState;
  right: DockPanelState;
  bottom: DockPanelState;
};

const DEFAULT_LAYOUT: DockLayout = {
  left: { open: false, collapsed: true, pinned: false, autoHide: true, size: 220 },
  right: { open: true, collapsed: false, pinned: false, autoHide: false, size: 300 },
  bottom: { open: false, collapsed: false, pinned: false, autoHide: true, size: 180 },
};

function clampSize(side: DockSide, size: number): number {
  if (side === "bottom") return Math.min(360, Math.max(120, size));
  return Math.min(480, Math.max(180, size));
}

function readLegacyActivityOpen(): boolean | null {
  try {
    const v = localStorage.getItem(PANEL_KEY);
    if (v === null) return null;
    return v === "1";
  } catch {
    return null;
  }
}

function readLayout(): DockLayout {
  try {
    const raw = localStorage.getItem(DOCK_LAYOUT_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<DockLayout>;
      return {
        left: { ...DEFAULT_LAYOUT.left, ...parsed.left },
        right: { ...DEFAULT_LAYOUT.right, ...parsed.right },
        bottom: { ...DEFAULT_LAYOUT.bottom, ...parsed.bottom },
      };
    }
  } catch {
    /* fall through */
  }
  const legacy = readLegacyActivityOpen();
  if (legacy !== null) {
    return {
      ...DEFAULT_LAYOUT,
      right: { ...DEFAULT_LAYOUT.right, open: legacy, collapsed: !legacy },
    };
  }
  return { ...DEFAULT_LAYOUT, left: { ...DEFAULT_LAYOUT.left }, right: { ...DEFAULT_LAYOUT.right }, bottom: { ...DEFAULT_LAYOUT.bottom } };
}

function persistLayout(layout: DockLayout) {
  try {
    localStorage.setItem(DOCK_LAYOUT_KEY, JSON.stringify(layout));
    localStorage.setItem(PANEL_KEY, layout.right.open && !layout.right.collapsed ? "1" : "0");
  } catch {
    /* ignore */
  }
}

type ShellLayoutState = {
  docks: DockLayout;
  /** @deprecated Prefer docks.right — kept for ActivityPanel / TopNavigation. */
  activityOpen: boolean;
  setActivityOpen: (open: boolean) => void;
  toggleActivity: () => void;
  setDock: (side: DockSide, patch: Partial<DockPanelState>) => void;
  toggleDock: (side: DockSide) => void;
  toggleDockCollapse: (side: DockSide) => void;
  toggleDockPin: (side: DockSide) => void;
  toggleDockAutoHide: (side: DockSide) => void;
  resizeDock: (side: DockSide, size: number) => void;
};

function syncActivity(docks: DockLayout): boolean {
  return docks.right.open && !docks.right.collapsed;
}

export const useShellLayoutStore = create<ShellLayoutState>((set, get) => {
  const initial = typeof window !== "undefined" ? readLayout() : DEFAULT_LAYOUT;
  return {
    docks: initial,
    activityOpen: syncActivity(initial),

    setActivityOpen: (open) => {
      const { docks } = get();
      if (syncActivity(docks) === open && docks.right.open === open) return;
      const next: DockLayout = {
        ...docks,
        right: { ...docks.right, open, collapsed: !open },
      };
      persistLayout(next);
      set({ docks: next, activityOpen: syncActivity(next) });
    },

    toggleActivity: () => get().setActivityOpen(!get().activityOpen),

    setDock: (side, patch) => {
      const { docks } = get();
      const cur = docks[side];
      const merged = { ...cur, ...patch };
      if (patch.size != null) merged.size = clampSize(side, patch.size);
      const next = { ...docks, [side]: merged };
      persistLayout(next);
      set({ docks: next, activityOpen: syncActivity(next) });
    },

    toggleDock: (side) => {
      const d = get().docks[side];
      get().setDock(side, { open: !d.open, collapsed: d.open ? true : false });
    },

    toggleDockCollapse: (side) => {
      const d = get().docks[side];
      if (d.collapsed) {
        get().setDock(side, { collapsed: false, open: true });
      } else {
        get().setDock(side, { collapsed: true });
      }
    },

    toggleDockPin: (side) => {
      const d = get().docks[side];
      get().setDock(side, { pinned: !d.pinned, autoHide: d.pinned ? d.autoHide : false });
    },

    toggleDockAutoHide: (side) => {
      const d = get().docks[side];
      get().setDock(side, { autoHide: !d.autoHide, pinned: d.autoHide ? d.pinned : false });
    },

    resizeDock: (side, size) => {
      get().setDock(side, { size: clampSize(side, size) });
    },
  };
});
