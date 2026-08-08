/**
 * Sprint 46.4 — interaction / task inbox store.
 */

import { create } from "zustand";
import type { IntentInteraction, InteractionStatus, UnifiedIntentKind } from "./unifiedIntentTypes";

const STORAGE_KEY = "ados_unified_intent_v46_4";

function load(): IntentInteraction[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as IntentInteraction[];
    return Array.isArray(parsed) ? parsed.slice(0, 40) : [];
  } catch {
    return [];
  }
}

function persist(items: IntentInteraction[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 40)));
  } catch {
    /* ignore */
  }
}

function nid(): string {
  return `ix-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

type State = {
  items: IntentInteraction[];
  showTech: boolean;
  inboxOpen: boolean;
  hydrate: () => void;
  setShowTech: (v: boolean) => void;
  setInboxOpen: (v: boolean) => void;
  create: (text: string, intent: UnifiedIntentKind, verticalId?: string) => IntentInteraction;
  patch: (id: string, patch: Partial<IntentInteraction>) => void;
  setStatus: (id: string, status: InteractionStatus, extra?: Partial<IntentInteraction>) => void;
  recent: (n?: number) => IntentInteraction[];
  byFilter: (f: "all" | "running" | "done" | "failed") => IntentInteraction[];
};

export const useUnifiedIntentStore = create<State>((set, get) => ({
  items: [],
  showTech: false,
  inboxOpen: false,

  hydrate: () => set({ items: load() }),

  setShowTech: (v) => set({ showTech: v }),
  setInboxOpen: (v) => set({ inboxOpen: v }),

  create: (text, intent, verticalId) => {
    const now = Date.now();
    const item: IntentInteraction = {
      id: nid(),
      text,
      intent,
      status: "received",
      createdAt: now,
      updatedAt: now,
      verticalId,
    };
    set((s) => {
      const items = [item, ...s.items].slice(0, 40);
      persist(items);
      return { items };
    });
    return item;
  },

  patch: (id, patch) => {
    set((s) => {
      const items = s.items.map((it) =>
        it.id === id ? { ...it, ...patch, updatedAt: Date.now() } : it,
      );
      persist(items);
      return { items };
    });
  },

  setStatus: (id, status, extra) => {
    get().patch(id, { status, ...extra });
  },

  recent: (n = 5) => get().items.slice(0, n),

  byFilter: (f) => {
    const items = get().items;
    if (f === "running") {
      return items.filter((i) =>
        ["received", "routing", "running", "waiting_user"].includes(i.status),
      );
    }
    if (f === "done") return items.filter((i) => i.status === "completed");
    if (f === "failed") return items.filter((i) => i.status === "failed" || i.status === "cancelled");
    return items;
  },
}));
