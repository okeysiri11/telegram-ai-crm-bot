/**
 * Sprint 41.1 — View Mode store (UI only; never mutates auth permissions).
 */

import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import {
  VIEW_MODE_OPTIONS,
  legacyRoleToViewMode,
  type ViewModeId,
  type ViewModeOption,
} from "./viewModeCatalog";

export const VIEW_MODE_KEY = wsKey("ewp_view_mode_v1");
const LEGACY_ROLE_KEY = wsKey("ewp_role_switcher_v1");

function loadMode(): ViewModeId {
  try {
    const raw = localStorage.getItem(VIEW_MODE_KEY);
    if (raw && VIEW_MODE_OPTIONS.some((o) => o.id === raw)) return raw as ViewModeId;
    const legacy = localStorage.getItem(LEGACY_ROLE_KEY);
    const mapped = legacyRoleToViewMode(legacy);
    if (mapped) return mapped;
  } catch {
    /* ignore */
  }
  return "platform_owner";
}

type ViewModeState = {
  viewMode: ViewModeId;
  setViewMode: (mode: ViewModeId) => void;
  options: () => ViewModeOption[];
  isClientMode: () => boolean;
  isOwnerMode: () => boolean;
  isDeveloperMode: () => boolean;
};

export const useViewModeStore = create<ViewModeState>((set, get) => ({
  viewMode: typeof localStorage !== "undefined" ? loadMode() : "platform_owner",
  setViewMode: (mode) => {
    if (get().viewMode === mode) return;
    if (!VIEW_MODE_OPTIONS.some((o) => o.id === mode)) return;
    try {
      localStorage.setItem(VIEW_MODE_KEY, mode);
    } catch {
      /* ignore */
    }
    set({ viewMode: mode });
  },
  options: () => VIEW_MODE_OPTIONS,
  isClientMode: () => get().viewMode === "client",
  isOwnerMode: () => get().viewMode === "platform_owner",
  isDeveloperMode: () => get().viewMode === "developer",
}));
