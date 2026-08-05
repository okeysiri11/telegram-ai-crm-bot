/**
 * Shared application context — Sprint 28.0.
 * Single reactive snapshot over auth · workspace · tabs · dashboard profile · route.
 */

import { create } from "zustand";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useLiveDashboardStore } from "@/live-dashboard/liveDashboardStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { contextEngine } from "../../command-center/managers/contextEngine";
import { enterpriseEventBus } from "./enterpriseEventBus";
import {
  surfaceFromPath,
  type SharedAppContext,
} from "./types";

type IntegrationContextState = SharedAppContext & {
  syncedAt: string | null;
  syncFromRoute: (pathname: string, search?: string) => SharedAppContext;
  snapshot: () => SharedAppContext;
};

function buildContext(pathname: string): SharedAppContext {
  const user = useAuthStore.getState().user;
  const ws = useWorkspaceStore.getState().workspace;
  const first = loadFirstEntry();
  const tabs = useWorkspaceManager.getState();
  const profileId = useLiveDashboardStore.getState().profileId || "ceo";
  const surface = surfaceFromPath(pathname);
  const organization = first.companyName || ws.company || "demo-corp";
  const project = ws.project || first.workspaceId || "default";
  const workspaceId = tabs.activeWorkspaceId || project || "ws_default";
  const moduleId = surface === "other" ? pathname.split("/").filter(Boolean)[0] || "app" : surface;

  return {
    workspaceId,
    userId: user?.id || user?.email || null,
    userName: user?.name || user?.email || null,
    organization,
    project,
    moduleId,
    surface,
    aiSessionId: typeof sessionStorage !== "undefined" ? sessionStorage.getItem("ews_ai_session_v1") : null,
    runtimeLabel: "enterprise-web",
    profileId,
    path: pathname,
  };
}

export const useIntegrationContext = create<IntegrationContextState>((set, get) => ({
  workspaceId: "ws_default",
  userId: null,
  userName: null,
  organization: "demo-corp",
  project: "default",
  moduleId: "dashboard",
  surface: "dashboard",
  aiSessionId: null,
  runtimeLabel: "enterprise-web",
  profileId: "ceo",
  path: "/dashboard",
  syncedAt: null,

  syncFromRoute: (pathname) => {
    const next = buildContext(pathname);
    const prev = get().snapshot();
    const unchanged =
      prev.path === next.path &&
      prev.workspaceId === next.workspaceId &&
      prev.userId === next.userId &&
      prev.userName === next.userName &&
      prev.organization === next.organization &&
      prev.project === next.project &&
      prev.moduleId === next.moduleId &&
      prev.surface === next.surface &&
      prev.aiSessionId === next.aiSessionId &&
      prev.profileId === next.profileId;
    // Idempotent contextEngine writes (Sprint 33.2.1).
    contextEngine.pushPage(pathname);
    contextEngine.patch({
      workspace: next.workspaceId,
      organization: next.organization,
      role: loadFirstEntry().roleId || useAuthStore.getState().user?.roleId || "user",
      department: useWorkspaceStore.getState().workspace.department || next.surface,
      currentModule: next.moduleId,
      selectedProject: next.project,
      currentDashboard: next.surface === "dashboard" ? "command_center" : null,
    });
    if (!unchanged) {
      set({ ...next, syncedAt: new Date().toISOString() });
    }
    if (
      prev.surface !== next.surface ||
      prev.workspaceId !== next.workspaceId ||
      prev.organization !== next.organization ||
      prev.project !== next.project
    ) {
      enterpriseEventBus.publish({
        type: "context_changed",
        source: "hub",
        path: pathname,
        payload: { ...next },
      });
    }
    return next;
  },

  snapshot: () => {
    const s = get();
    return {
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
    };
  },
}));
