/**
 * Sprint 33.2 — Accordion: only one nav group expanded; persist in localStorage.
 */

import { create } from "zustand";
import type { NavGroupId } from "./intelligentNavGroups";
import { NAV_ACCORDION_KEY } from "./intelligentNavGroups";

function readExpanded(): NavGroupId | null {
  try {
    const raw = localStorage.getItem(NAV_ACCORDION_KEY);
    if (
      raw === "workspace" ||
      raw === "business" ||
      raw === "ai" ||
      raw === "city" ||
      raw === "platform" ||
      raw === "owner"
    ) {
      return raw;
    }
  } catch {
    /* ignore */
  }
  return "workspace";
}

type NavAccordionState = {
  expandedId: NavGroupId | null;
  /** Expand this group; collapses any other. Pass null to collapse all. */
  expand: (id: NavGroupId | null) => void;
  /** Toggle: if already open, collapse; else expand (closing previous). */
  toggle: (id: NavGroupId) => void;
  /** Ensure group for current route is open without clearing user choice unless unset. */
  ensureForRoute: (id: NavGroupId | null) => void;
};

export const useNavAccordionStore = create<NavAccordionState>((set, get) => ({
  expandedId: typeof window !== "undefined" ? readExpanded() : "workspace",
  expand: (id) => {
    if (get().expandedId === id) return;
    try {
      if (id) localStorage.setItem(NAV_ACCORDION_KEY, id);
      else localStorage.removeItem(NAV_ACCORDION_KEY);
    } catch {
      /* ignore */
    }
    set({ expandedId: id });
  },
  toggle: (id) => {
    const cur = get().expandedId;
    get().expand(cur === id ? null : id);
  },
  /** Expand the group that owns the current route (keeps one-open accordion). */
  ensureForRoute: (id) => {
    if (!id) return;
    if (get().expandedId !== id) get().expand(id);
  },
}));
