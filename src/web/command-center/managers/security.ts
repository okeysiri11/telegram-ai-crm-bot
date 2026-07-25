import { COMMAND_CATALOG } from "./quickActions";
import { contextEngine } from "./contextEngine";
import { commandAnalytics } from "./analytics";
import { navigationIndex } from "./omnibox";

export function canExecute(permission: string | undefined, perms: string[]): boolean {
  if (!perms.length) return false;
  if (perms.includes("*") || !permission || permission === "*") return true;
  return perms.includes(permission) || perms.includes(permission.split("_")[0]!);
}

export const actionExecutor = {
  execute(actionOrId: string): { ok: boolean; route?: string; label?: string; error?: string } {
    const t0 = performance.now();
    const cmd = COMMAND_CATALOG.find((c) => c.action === actionOrId || c.id === actionOrId);
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
  },
};
