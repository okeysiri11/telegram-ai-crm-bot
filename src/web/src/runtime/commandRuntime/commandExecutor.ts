/**
 * Command executor — Sprint 28.6.
 * Permission gate · default handlers · desktop window ops.
 */

import { contextEngine } from "../../../command-center/managers/contextEngine";
import { navigationIndex } from "../../../command-center/managers/omnibox";
import { useDesktopStore } from "@/enterprise-desktop/desktopStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { canExecutePermission, meetsMinRole } from "./commandPermissions";
import { buildCommandContext } from "./commandContext";
import { commandRegistry } from "./commandRegistry";
import { commandPolicy } from "./commandPolicy";
import type {
  CommandArgs,
  CommandDefinition,
  CommandExecutionContext,
  CommandHandlerResult,
  CommandKind,
} from "./commandTypes";

export function assertCommandAllowed(
  def: CommandDefinition,
  ctx: CommandExecutionContext,
): { ok: true } | { ok: false; error: string } {
  if (!meetsMinRole(ctx.role, def.minRole)) {
    return { ok: false, error: "role_denied" };
  }
  if (!canExecutePermission(def.permission ?? "*", ctx.permissions)) {
    return { ok: false, error: "permission_denied" };
  }
  const policy = commandPolicy.evaluate(def, ctx);
  if (!policy.allowed) {
    return { ok: false, error: policy.reason || "policy_denied" };
  }
  return { ok: true };
}

function openOnDesktop(path: string): boolean {
  try {
    useDesktopStore.getState().openApp(path);
    return true;
  } catch {
    return false;
  }
}

export function runDefaultHandler(
  def: CommandDefinition,
  ctx: CommandExecutionContext,
  args: CommandArgs,
): CommandHandlerResult {
  const route = (typeof args.path === "string" && args.path) || def.route;

  if (def.kind === "close_window") {
    const id = String(args.windowId || useDesktopStore.getState().focusedId || "");
    if (!id) return { ok: false, error: "no_focused_window" };
    useDesktopStore.getState().closeWindow(id);
    return { ok: true, message: "closed" };
  }
  if (def.kind === "minimize_window") {
    const id = String(args.windowId || useDesktopStore.getState().focusedId || "");
    if (!id) return { ok: false, error: "no_focused_window" };
    useDesktopStore.getState().minimizeWindow(id);
    return { ok: true, message: "minimized" };
  }
  if (def.kind === "maximize_window") {
    const id = String(args.windowId || useDesktopStore.getState().focusedId || "");
    if (!id) return { ok: false, error: "no_focused_window" };
    useDesktopStore.getState().toggleMaximize(id);
    return { ok: true, message: "maximized" };
  }
  if (def.kind === "focus_window") {
    const id = String(args.windowId || "");
    if (!id) return { ok: false, error: "windowId_required" };
    useDesktopStore.getState().focusWindow(id);
    return { ok: true, message: "focused" };
  }
  if (def.kind === "open_desktop_window" || (ctx.surface === "desktop" && route)) {
    if (!route) return { ok: false, error: "route_required" };
    openOnDesktop(route);
    return { ok: true, route };
  }
  if (def.kind === "show_notification") {
    useNotificationStore.getState().push({
      kind: "info",
      title: def.label,
      body: String(args.message || args.body || "Command completed"),
    });
    return { ok: true, message: "notified" };
  }

  if (route) {
    contextEngine.pushPage(route);
    try {
      navigationIndex.recordUse(def.id);
    } catch {
      /* ignore */
    }
    if (ctx.surface === "desktop") {
      openOnDesktop(route);
    } else {
      ctx.navigate(route);
    }
    return { ok: true, route };
  }

  return { ok: true, message: "noop" };
}

export async function executeDefinition(
  def: CommandDefinition,
  args: CommandArgs = {},
): Promise<CommandHandlerResult> {
  const ctx = buildCommandContext(args);
  const gate = assertCommandAllowed(def, ctx);
  if (!gate.ok) return { ok: false, error: gate.error };

  if (def.handler) {
    return await Promise.resolve(def.handler(ctx, { ...args, ...ctx.args }));
  }
  return runDefaultHandler(def, ctx, args);
}

export function executeDefinitionSync(
  def: CommandDefinition,
  args: CommandArgs = {},
): CommandHandlerResult {
  const ctx = buildCommandContext(args);
  const gate = assertCommandAllowed(def, ctx);
  if (!gate.ok) return { ok: false, error: gate.error };

  if (def.handler) {
    const out = def.handler(ctx, { ...args, ...ctx.args });
    if (out && typeof (out as Promise<CommandHandlerResult>).then === "function") {
      void Promise.resolve(out);
      return { ok: true, message: "async_started" };
    }
    return out as CommandHandlerResult;
  }
  return runDefaultHandler(def, ctx, args);
}

export function resolveCommand(actionOrId: string): CommandDefinition | undefined {
  return commandRegistry.get(actionOrId);
}

export function mapLegacyKind(kind: string): CommandKind {
  switch (kind) {
    case "open_module":
    case "open":
    case "open_dashboard":
    case "open_report":
      return "open_module";
    case "navigate":
    case "open_settings":
      return "navigate";
    case "create":
    case "mass_update":
      return "quick_action";
    case "ai_execute":
      return "run_agent";
    case "run_workflow":
    case "run_automation":
      return "run_workflow";
    case "search":
      return "search";
    default:
      return "system";
  }
}
