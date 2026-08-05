/**
 * Command execution context — Sprint 28.6.
 * Syncs auth + path into Command Runtime (and legacy contextEngine).
 */

import { useAuthStore } from "@/auth/authStore";
import { contextEngine } from "../../../command-center/managers/contextEngine";
import { shellModuleRegistry } from "@/shell/enterprise/shellModuleRegistry";
import { permissionsForRole, resolveCommandRole } from "./commandPermissions";
import { commandPolicy } from "./commandPolicy";
import type { CommandArgs, CommandExecutionContext, CommandRole } from "./commandTypes";

let navigateFn: ((path: string) => void) | null = null;
let surface: CommandExecutionContext["surface"] = "shell";

export function bindCommandNavigator(fn: (path: string) => void) {
  navigateFn = fn;
}

export function setCommandSurface(next: CommandExecutionContext["surface"]) {
  surface = next;
}

export function navigateViaRuntime(path: string) {
  if (navigateFn) {
    navigateFn(path);
    return;
  }
  if (typeof window !== "undefined") {
    window.history.pushState({}, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }
}

function moduleIdForPath(path: string): string | null {
  const hit = shellModuleRegistry.list().find((m) => {
    const base = m.route.split("?")[0]!;
    return path === base || path.startsWith(base + "/");
  });
  return hit?.id || null;
}

export function syncAuthIntoContextEngine() {
  const user = useAuthStore.getState().user;
  const role = resolveCommandRole({ roleId: user?.roleId, roles: user?.roles });
  const permissions = permissionsForRole(role, user?.permissions || []);
  contextEngine.patch({
    role,
    permissions,
    organization: user?.tenantId || contextEngine.get().organization,
  });
  return { role, permissions };
}

export function buildCommandContext(args: CommandArgs = {}): CommandExecutionContext {
  const user = useAuthStore.getState().user;
  const role: CommandRole = resolveCommandRole({ roleId: user?.roleId, roles: user?.roles });
  const permissions = permissionsForRole(role, user?.permissions || []);
  const path =
    typeof window !== "undefined" ? window.location.pathname + window.location.search : "/";

  // Keep legacy palette permission gate in sync
  contextEngine.patch({ role, permissions });

  return {
    role,
    roles: user?.roles || [],
    permissions,
    userId: user?.id || null,
    path,
    moduleId: moduleIdForPath(path.split("?")[0] || path),
    surface,
    navigate: navigateViaRuntime,
    args,
    policy: commandPolicy.buildContext(),
  };
}
