/**
 * Session restore coordinator — Sprint 28.0.
 * Ordered hydrate of existing surface stores. No duplicated persistence.
 */

import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useDesktopStore } from "@/enterprise-desktop/desktopStore";
import { useLiveDashboardStore } from "@/live-dashboard/liveDashboardStore";
import { useProductionStore } from "@/ai-production-studio/productionStore";
import { readViewport } from "@/enterprise-city/cityEngine";
import { getCityFocus } from "@/enterprise-city/cityVisualLanguage";
import { useLastModuleStore } from "@/modules/lastModuleStore";
import { enterpriseEventBus } from "./enterpriseEventBus";
import { INTEGRATION_BOOT_KEY, INTEGRATION_HUB_VERSION } from "./types";

export type SessionRestoreReport = {
  version: string;
  auth: boolean;
  workspaceTabs: boolean;
  desktop: boolean;
  dashboard: boolean;
  production: boolean;
  cityViewport: { x: number; y: number; zoom: number } | null;
  cityFocus: string | null;
  lastModule: string;
  at: string;
};

let restored = false;

export const sessionCoordinator = {
  isRestored() {
    return restored;
  },

  /**
   * Hydrate surface stores once after auth is ready.
   * Safe to call from Providers — idempotent.
   */
  restoreAll(): SessionRestoreReport {
    if (typeof window === "undefined") {
      return emptyReport();
    }
    if (!restored) {
      try {
        useWorkspaceManager.getState().hydrate();
      } catch {
        /* ignore */
      }
      try {
        useDesktopStore.getState().hydrate();
      } catch {
        /* ignore */
      }
      try {
        useLiveDashboardStore.getState().hydrate();
      } catch {
        /* ignore */
      }
      try {
        useProductionStore.getState().hydrate();
      } catch {
        /* ignore */
      }
      restored = true;
      try {
        localStorage.setItem(
          INTEGRATION_BOOT_KEY,
          JSON.stringify({ version: INTEGRATION_HUB_VERSION, at: new Date().toISOString() }),
        );
      } catch {
        /* ignore */
      }
    }

    const report: SessionRestoreReport = {
      version: INTEGRATION_HUB_VERSION,
      auth: Boolean(useAuthStore.getState().user),
      workspaceTabs: useWorkspaceManager.getState().hydrated,
      desktop: useDesktopStore.getState().hydrated,
      dashboard: useLiveDashboardStore.getState().hydrated,
      production: useProductionStore.getState().hydrated,
      cityViewport: readViewport(),
      cityFocus: getCityFocus(),
      lastModule: useLastModuleStore.getState().lastRoute,
      at: new Date().toISOString(),
    };

    enterpriseEventBus.publish({
      type: "session_restored",
      source: "system",
      payload: { ...report },
    });

    return report;
  },
};

function emptyReport(): SessionRestoreReport {
  return {
    version: INTEGRATION_HUB_VERSION,
    auth: false,
    workspaceTabs: false,
    desktop: false,
    dashboard: false,
    production: false,
    cityViewport: null,
    cityFocus: null,
    lastModule: "/dashboard",
    at: new Date().toISOString(),
  };
}
