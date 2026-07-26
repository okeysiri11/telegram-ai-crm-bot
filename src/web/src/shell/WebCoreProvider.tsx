/**
 * Web Core bootstrap — Sprint 30.5.
 * Completes shared application shell contexts without a parallel state architecture.
 * Reuses authStore, workspaceStore, themeStore, navigationManager.
 */

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useThemeStore } from "@/theme/themeStore";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { getIdentityContext } from "@/integrations/apiClient";
import type { MenuItem } from "../../navigation/types";

export type WebCoreState = {
  ready: boolean;
  organization: string;
  department: string;
  project: string;
  userId: string | null;
  email: string | null;
  roleId: string | null;
  tenantId: string | null;
  permissions: string[];
  themeMode: string;
  navigation: MenuItem[];
  modulesHealthy: number;
  modulesTotal: number;
  ecosystemsReady: boolean;
};

const WebCoreContext = createContext<WebCoreState | null>(null);

export function WebCoreProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const user = useAuthStore((s) => s.user);
  const ws = useWorkspaceStore((s) => s.workspace);
  const themeMode = useThemeStore((s) => s.mode);

  useEffect(() => {
    setReady(true);
  }, []);

  const value = useMemo<WebCoreState>(() => {
    const identity = getIdentityContext();
    const permissions = [
      ...ws.permissions,
      ...(user?.roleId ? [user.roleId] : []),
    ];
    const navigation = navigationManager.forTenant(
      identity.tenantId || "demo",
      permissions.length ? permissions : ["read"],
      "sidebar",
    );
    const health = moduleRegistry.healthSummary();
    return {
      ready,
      organization: ws.company,
      department: ws.department,
      project: ws.project,
      userId: identity.userId,
      email: identity.email,
      roleId: identity.roleId,
      tenantId: identity.tenantId,
      permissions: ws.permissions,
      themeMode,
      navigation,
      modulesHealthy: health.filter((h) => h.health === "healthy").length,
      modulesTotal: health.length,
      ecosystemsReady: moduleRegistry.ecosystemsRegistered(),
    };
  }, [ready, user, ws, themeMode]);

  return <WebCoreContext.Provider value={value}>{children}</WebCoreContext.Provider>;
}

export function useWebCore(): WebCoreState {
  const ctx = useContext(WebCoreContext);
  if (!ctx) {
    throw new Error("useWebCore requires WebCoreProvider");
  }
  return ctx;
}
