/**
 * Integration Hub hooks — Sprint 28.0 / 33.2.1 stability.
 */

import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useRuntimeHealth } from "@/enterprise-runtime/useRuntimeHealth";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { useIntegrationContext } from "./integrationContextStore";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { registerIntegrationSearch } from "./searchRegistration";
import { sessionCoordinator } from "./sessionCoordinator";
import type { SharedAppContext } from "./types";

/**
 * Boot + keep shared context in sync with the SPA router.
 * Mount once in Providers (TelemetryRouterBridge replacement helper).
 */
export function useIntegrationBoot() {
  const location = useLocation();
  const syncFromRoute = useIntegrationContext((s) => s.syncFromRoute);

  useEffect(() => {
    enterpriseEventBus.connectLiveBridge();
    registerIntegrationSearch();
    sessionCoordinator.restoreAll();
    runtimeEngine.start();
  }, []);

  useEffect(() => {
    syncFromRoute(location.pathname, location.search);
  }, [location.pathname, location.search, syncFromRoute]);
}

/** Shared context snapshot for any surface — shallow compare (Sprint 33.2.1). */
export function useSharedContext(): SharedAppContext {
  return useIntegrationContext(
    useShallow((s) => ({
      workspaceId: s.workspaceId,
      userId: s.userId,
      userName: s.userName,
      organization: s.organization,
      project: s.project,
      moduleId: s.moduleId,
      surface: s.surface,
      aiSessionId: s.aiSessionId,
      runtimeLabel: s.runtimeLabel,
      profileId: s.profileId,
      path: s.path,
    })),
  );
}

/**
 * One runtime health subscription for OS surfaces.
 * Backed by Health Service singleton (Sprint 28.1) — no duplicated polling.
 */
export function useIntegrationRuntimeHealth() {
  return useRuntimeHealth();
}

/** Same notification list everywhere — existing store only. */
export function useIntegrationNotifications() {
  const items = useNotificationStore((s) => s.items);
  const push = useNotificationStore((s) => s.push);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const unread = items.filter((i) => !i.read).length;
  return { items, unread, push, markRead, markAllRead };
}

/**
 * Navigate via SPA + publish hub event (City → Production, Desktop → CRM, …).
 */
export function useIntegrationNavigate() {
  const navigate = useNavigate();
  return {
    go(path: string, source: Parameters<typeof enterpriseEventBus.openModule>[1] = "hub") {
      enterpriseEventBus.openModule(path, source);
      navigate(path);
    },
  };
}
