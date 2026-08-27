/**
 * Sprint 42.0 — Workspace Dock favourites (pin, close, reorder, persist).
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";

export const WORKSPACE_DOCK_KEY = wsKey("ewp_workspace_dock_v1");

export type DockFavourite = {
  id: string;
  label: string;
  route: string;
  pinned?: boolean;
};

export const DOCK_CATALOG: DockFavourite[] = [
  { id: "crm", label: "CRM", route: "/crm" },
  { id: "analytics", label: "Аналитика", route: "/analytics" },
  { id: "drone", label: "БПЛА", route: "/workspace/drone" },
  { id: "crypto", label: "Crypto OTC", route: "/workspace/crypto" },
  { id: "auto", label: "Авто", route: "/workspace/auto" },
  { id: "agro", label: "Агро", route: "/workspace/agro" },
  { id: "marketplace", label: "Маркетплейс", route: "/marketplace" },
  { id: "legal", label: "Юридический", route: "/workspace/legal" },
  { id: "recruiting", label: "Рекрутинг", route: "/workspace/recruiting" },
  { id: "knowledge", label: "Знания", route: "/knowledge" },
  { id: "documents", label: "Документы", route: "/documents" },
  { id: "ai", label: "AI", route: "/ai-agents" },
  { id: "platform", label: "Платформа", route: "/platform-builder" },
];

/** Defaults include verticals; client dock UI filters by view-mode allowlist. */
const DEFAULT_FAVS: DockFavourite[] = [
  { id: "crm", label: "CRM", route: "/crm", pinned: true },
  { id: "analytics", label: "Аналитика", route: "/analytics" },
  { id: "drone", label: "БПЛА", route: "/workspace/drone" },
  { id: "crypto", label: "Crypto OTC", route: "/workspace/crypto" },
  { id: "knowledge", label: "Знания", route: "/knowledge" },
  { id: "documents", label: "Документы", route: "/documents" },
  { id: "ai", label: "AI", route: "/ai-agents" },
];

function read(): DockFavourite[] {
  try {
    const raw = localStorage.getItem(WORKSPACE_DOCK_KEY);
    if (!raw) return DEFAULT_FAVS.map((x) => ({ ...x }));
    const parsed = JSON.parse(raw) as DockFavourite[];
    if (!Array.isArray(parsed) || !parsed.length) return DEFAULT_FAVS.map((x) => ({ ...x }));
    return parsed.filter((x) => x.id && x.route);
  } catch {
    return DEFAULT_FAVS.map((x) => ({ ...x }));
  }
}

function persist(items: DockFavourite[]) {
  try {
    localStorage.setItem(WORKSPACE_DOCK_KEY, JSON.stringify(items));
  } catch {
    /* ignore */
  }
}

type DockState = {
  favourites: DockFavourite[];
  setFavourites: (items: DockFavourite[]) => void;
  pin: (id: string) => void;
  unpin: (id: string) => void;
  close: (id: string) => void;
  add: (item: DockFavourite) => void;
  reorder: (fromId: string, toId: string) => void;
  reset: () => void;
};

export const useWorkspaceDockStore = create<DockState>((set, get) => ({
  favourites: typeof localStorage !== "undefined" ? read() : DEFAULT_FAVS.map((x) => ({ ...x })),

  setFavourites: (items) => {
    persist(items);
    set({ favourites: items });
  },

  pin: (id) => {
    const next = get().favourites.map((f) => (f.id === id ? { ...f, pinned: true } : f));
    // pinned first
    next.sort((a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)));
    get().setFavourites(next);
  },

  unpin: (id) => {
    get().setFavourites(get().favourites.map((f) => (f.id === id ? { ...f, pinned: false } : f)));
  },

  close: (id) => {
    const cur = get().favourites.find((f) => f.id === id);
    if (cur?.pinned) return;
    get().setFavourites(get().favourites.filter((f) => f.id !== id));
  },

  add: (item) => {
    if (get().favourites.some((f) => f.id === item.id)) return;
    get().setFavourites([...get().favourites, item]);
  },

  reorder: (fromId, toId) => {
    if (fromId === toId) return;
    const items = [...get().favourites];
    const from = items.findIndex((f) => f.id === fromId);
    const to = items.findIndex((f) => f.id === toId);
    if (from < 0 || to < 0) return;
    const [moved] = items.splice(from, 1);
    if (!moved) return;
    items.splice(to, 0, moved);
    // keep pinned block first
    items.sort((a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)));
    get().setFavourites(items);
  },

  reset: () => get().setFavourites(DEFAULT_FAVS.map((x) => ({ ...x }))),
}));
