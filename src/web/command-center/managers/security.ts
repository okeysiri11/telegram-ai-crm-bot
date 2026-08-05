import { COMMAND_CATALOG } from "./quickActions";
import { contextEngine } from "./contextEngine";
import { commandAnalytics } from "./analytics";
import { navigationIndex } from "./omnibox";
import { DEVELOPER_COMMANDS } from "@/command-center-runtime/developerCommands";
import { commandRuntime } from "@/runtime/commandRuntime";

export function canExecute(permission: string | undefined, perms: string[]): boolean {
  if (!perms.length) return false;
  if (perms.includes("*") || !permission || permission === "*") return true;
  return perms.includes(permission) || perms.includes(permission.split("_")[0]!);
}

/**
 * Legacy sync facade — Sprint 28.6 delegates to Command Runtime.
 * Prefer `commandRuntime.execute` / `executeSync` for new callers.
 */
export const actionExecutor = {
  execute(actionOrId: string): { ok: boolean; route?: string; label?: string; error?: string } {
    const res = commandRuntime.executeSync(actionOrId);
    return {
      ok: res.ok,
      route: res.route,
      label: res.label,
      error: res.error,
    };
  },
};

/** @deprecated Kept for any direct catalog lookups outside Command Runtime. */
export function legacyCatalogLookup(actionOrId: string) {
  return (
    COMMAND_CATALOG.find((c) => c.action === actionOrId || c.id === actionOrId) ||
    DEVELOPER_COMMANDS.find((c) => c.action === actionOrId || c.id === actionOrId)
  );
}

/** @deprecated Prefer commandRuntime — retained for rare diagnostic use. */
export function legacyDirectExecute(actionOrId: string): {
  ok: boolean;
  route?: string;
  label?: string;
  error?: string;
} {
  const t0 = performance.now();
  const cmd = legacyCatalogLookup(actionOrId);
  const perms = contextEngine.get().permissions;
  if (!cmd) {
    commandAnalytics.track(actionOrId, false, performance.now() - t0);
    return { ok: false, error: "command_not_found" };
  }
  if (!canExecute(cmd.permission ?? "*", perms)) {
    commandAnalytics.track(cmd.id, false, performance.now() - t0);
    return { ok: false, error: "permission_denied" };
  }
  if (cmd.route) {
    contextEngine.pushPage(cmd.route);
    navigationIndex.recordUse(cmd.id);
  }
  commandAnalytics.track(cmd.id, true, performance.now() - t0);
  return { ok: true, route: cmd.route, label: cmd.label };
}
