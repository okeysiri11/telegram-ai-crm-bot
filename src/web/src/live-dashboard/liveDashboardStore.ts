import { create } from "zustand";
import {
  LIVE_DASHBOARD_KEY,
  type DashboardProfileId,
  type LiveDashboardLayout,
  type LiveDashboardState,
  type LiveWidgetId,
  type LiveWidgetPlacement,
} from "./types";
import { bootstrapLayouts, layoutForProfile } from "./liveDashboardCatalog";

function readState(): LiveDashboardState | null {
  try {
    const raw = localStorage.getItem(LIVE_DASHBOARD_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LiveDashboardState;
    if (parsed.version !== 1 || !Array.isArray(parsed.layouts)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function persist(state: Omit<LiveDashboardStore, keyof LiveDashboardActions>) {
  const snap: LiveDashboardState = {
    version: 1,
    profileId: state.profileId,
    activeLayoutId: state.activeLayoutId,
    layouts: state.layouts,
    fullscreenId: state.fullscreenId,
    activityFilter: state.activityFilter,
    updatedAt: new Date().toISOString(),
  };
  try {
    localStorage.setItem(LIVE_DASHBOARD_KEY, JSON.stringify(snap));
  } catch {
    /* ignore */
  }
}

type LiveDashboardActions = {
  hydrate: () => void;
  setProfile: (id: DashboardProfileId) => void;
  setActiveLayout: (id: string) => void;
  saveCurrentAs: (name: string) => void;
  restoreProfileLayout: () => void;
  moveWidget: (fromId: LiveWidgetId, toId: LiveWidgetId) => void;
  resizeWidget: (id: LiveWidgetId, colSpan: 1 | 2 | 3 | 4) => void;
  toggleCollapse: (id: LiveWidgetId) => void;
  togglePin: (id: LiveWidgetId) => void;
  setFullscreen: (id: LiveWidgetId | null) => void;
  setActivityFilter: (filter: string) => void;
  getActiveWidgets: () => LiveWidgetPlacement[];
};

type LiveDashboardStore = {
  hydrated: boolean;
  profileId: DashboardProfileId;
  activeLayoutId: string;
  layouts: LiveDashboardLayout[];
  fullscreenId: LiveWidgetId | null;
  activityFilter: string;
  tick: number;
  bumpTick: () => void;
} & LiveDashboardActions;

function sortWidgets(widgets: LiveWidgetPlacement[]): LiveWidgetPlacement[] {
  const pinned = widgets.filter((w) => w.pinned).sort((a, b) => a.order - b.order);
  const rest = widgets.filter((w) => !w.pinned).sort((a, b) => a.order - b.order);
  return [...pinned, ...rest].map((w, order) => ({ ...w, order }));
}

function patchActive(
  state: { layouts: LiveDashboardLayout[]; activeLayoutId: string },
  patch: (widgets: LiveWidgetPlacement[]) => LiveWidgetPlacement[],
): LiveDashboardLayout[] {
  return state.layouts.map((l) =>
    l.id === state.activeLayoutId ? { ...l, widgets: sortWidgets(patch([...l.widgets])) } : l,
  );
}

export const useLiveDashboardStore = create<LiveDashboardStore>((set, get) => ({
  hydrated: false,
  profileId: "ceo",
  activeLayoutId: "layout_ceo",
  layouts: bootstrapLayouts(),
  fullscreenId: null,
  activityFilter: "all",
  tick: 0,

  hydrate: () => {
    if (get().hydrated) return;
    const snap = typeof window !== "undefined" ? readState() : null;
    if (snap) {
      set({
        profileId: snap.profileId,
        activeLayoutId: snap.activeLayoutId,
        layouts: snap.layouts.length ? snap.layouts : bootstrapLayouts(),
        fullscreenId: snap.fullscreenId,
        activityFilter: snap.activityFilter || "all",
        hydrated: true,
      });
      return;
    }
    const layouts = bootstrapLayouts();
    set({
      profileId: "ceo",
      activeLayoutId: "layout_ceo",
      layouts,
      hydrated: true,
    });
    persist({ ...get(), layouts, profileId: "ceo", activeLayoutId: "layout_ceo" });
  },

  bumpTick: () => set((s) => ({ tick: s.tick + 1 })),

  setProfile: (id) => {
    const layout = layoutForProfile(id);
    set((s) => {
      const layouts = s.layouts.some((l) => l.id === layout.id)
        ? s.layouts.map((l) => (l.id === layout.id ? layout : l))
        : [...s.layouts, layout];
      const next = {
        ...s,
        profileId: id,
        activeLayoutId: layout.id,
        layouts,
      };
      persist(next);
      return next;
    });
  },

  setActiveLayout: (id) => {
    if (!get().layouts.some((l) => l.id === id)) return;
    set((s) => {
      const next = { ...s, activeLayoutId: id };
      persist(next);
      return next;
    });
  },

  saveCurrentAs: (name) => {
    const cur = get().layouts.find((l) => l.id === get().activeLayoutId);
    if (!cur) return;
    const id = `layout_custom_${Math.random().toString(36).slice(2, 8)}`;
    const layout: LiveDashboardLayout = {
      id,
      name: name.trim() || "Custom layout",
      widgets: cur.widgets.map((w) => ({ ...w })),
    };
    set((s) => {
      const next = { ...s, layouts: [...s.layouts, layout], activeLayoutId: id };
      persist(next);
      return next;
    });
  },

  restoreProfileLayout: () => {
    const layout = layoutForProfile(get().profileId);
    set((s) => {
      const layouts = s.layouts.map((l) => (l.id === layout.id ? layout : l));
      if (!layouts.some((l) => l.id === layout.id)) layouts.push(layout);
      const next = { ...s, layouts, activeLayoutId: layout.id };
      persist(next);
      return next;
    });
  },

  moveWidget: (fromId, toId) => {
    if (fromId === toId) return;
    set((s) => {
      const layouts = patchActive(s, (widgets) => {
        const from = widgets.findIndex((w) => w.id === fromId);
        const to = widgets.findIndex((w) => w.id === toId);
        if (from < 0 || to < 0) return widgets;
        const next = [...widgets];
        const [moved] = next.splice(from, 1);
        next.splice(to, 0, moved!);
        return next.map((w, order) => ({ ...w, order }));
      });
      const next = { ...s, layouts };
      persist(next);
      return next;
    });
  },

  resizeWidget: (id, colSpan) => {
    set((s) => {
      const layouts = patchActive(s, (widgets) =>
        widgets.map((w) => (w.id === id ? { ...w, colSpan } : w)),
      );
      const next = { ...s, layouts };
      persist(next);
      return next;
    });
  },

  toggleCollapse: (id) => {
    set((s) => {
      const layouts = patchActive(s, (widgets) =>
        widgets.map((w) => (w.id === id ? { ...w, collapsed: !w.collapsed } : w)),
      );
      const next = { ...s, layouts };
      persist(next);
      return next;
    });
  },

  togglePin: (id) => {
    set((s) => {
      const layouts = patchActive(s, (widgets) =>
        widgets.map((w) => (w.id === id ? { ...w, pinned: !w.pinned } : w)),
      );
      const next = { ...s, layouts };
      persist(next);
      return next;
    });
  },

  setFullscreen: (id) => set({ fullscreenId: id }),

  setActivityFilter: (filter) => {
    set((s) => {
      const next = { ...s, activityFilter: filter };
      persist(next);
      return next;
    });
  },

  getActiveWidgets: () => {
    const s = get();
    const layout = s.layouts.find((l) => l.id === s.activeLayoutId);
    return layout ? sortWidgets(layout.widgets) : [];
  },
}));
