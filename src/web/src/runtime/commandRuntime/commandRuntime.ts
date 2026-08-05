/**
 * Enterprise Command Runtime — Sprint 28.6 / 28.7.
 * Central execution engine: Palette · Shell · Desktop · AI · Macros · Undo.
 */

import { COMMAND_CATALOG } from "../../../command-center/managers/quickActions";
import { DEVELOPER_COMMANDS } from "@/command-center-runtime/developerCommands";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { SHELL_QUICK_ACTIONS } from "@/shell/enterprise/shellQuickActions";
import { shellModuleRegistry } from "@/shell/enterprise/shellModuleRegistry";
import {
  bindCommandNavigator,
  navigateViaRuntime,
  setCommandSurface,
  syncAuthIntoContextEngine,
} from "./commandContext";
import { commandHistory } from "./commandHistory";
import { commandRegistry } from "./commandRegistry";
import {
  executeDefinition,
  executeDefinitionSync,
  mapLegacyKind,
  resolveCommand,
} from "./commandExecutor";
import { commandUndoStack } from "./commandUndoStack";
import { commandMacros } from "./commandMacros";
import { commandIntelligenceAnalytics } from "./commandIntelligenceAnalytics";
import { commandPolicy } from "./commandPolicy";
import { interpretAiIntent } from "./aiIntentRouter";
import { launcherRegistry } from "./launcherRegistry";
import {
  COMMAND_RUNTIME_VERSION,
  type CommandArgs,
  type CommandDefinition,
  type CommandResult,
} from "./commandTypes";

let booted = false;
const running = new Set<string>();

function emitCommand(
  type: "command.started" | "command.completed" | "command.failed" | "command.cancelled",
  payload: Record<string, unknown>,
  path?: string,
) {
  enterpriseEventBus.publish({
    type,
    source: "system",
    path,
    payload,
  });
}

function currentPath() {
  return typeof window !== "undefined" ? window.location.pathname + window.location.search : "/";
}

function toResult(
  def: CommandDefinition,
  handler: { ok: boolean; route?: string; message?: string; error?: string; cancelled?: boolean },
  durationMs: number,
): CommandResult {
  return {
    id: def.id,
    action: def.action,
    label: def.label,
    ok: handler.ok,
    route: handler.route,
    message: handler.message,
    error: handler.error,
    cancelled: handler.cancelled,
    durationMs,
  };
}

function finish(def: CommandDefinition, result: CommandResult, args: CommandArgs, previousPath: string) {
  commandHistory.push({
    commandId: def.id,
    action: def.action,
    label: def.label,
    ok: result.ok,
    route: result.route,
    error: result.error,
  });

  const viaAi = args.via === "ai";
  try {
    commandIntelligenceAnalytics.track(def.id, result.ok, result.durationMs, {
      ai: viaAi,
      error: result.error,
    });
  } catch {
    /* ignore */
  }

  if (result.ok && !result.cancelled && !commandUndoStack.isApplying()) {
    if (def.kind !== "undo" && def.kind !== "redo" && def.id !== "sys_undo" && def.id !== "sys_redo") {
      commandUndoStack.push({
        commandId: def.id,
        action: def.action,
        label: def.label,
        args,
        previousPath,
        route: result.route,
        kind: def.kind,
      });
      commandMacros.capture({ commandId: def.id, action: def.action, args });
    }
  }

  if (result.cancelled) {
    emitCommand("command.cancelled", {
      commandId: def.id,
      action: def.action,
      label: def.label,
    }, result.route);
    return result;
  }
  if (result.ok) {
    emitCommand(
      "command.completed",
      {
        commandId: def.id,
        action: def.action,
        label: def.label,
        durationMs: result.durationMs,
        route: result.route,
      },
      result.route,
    );
    if (result.route && !commandUndoStack.isApplying()) {
      enterpriseEventBus.openModule(result.route, "hub", {
        commandId: def.id,
        via: "command_runtime",
      });
    }
  } else {
    emitCommand(
      "command.failed",
      {
        commandId: def.id,
        action: def.action,
        label: def.label,
        error: result.error || "failed",
        durationMs: result.durationMs,
      },
      result.route,
    );
  }
  return result;
}

function registerCatalogCommands() {
  const defs: CommandDefinition[] = [];

  for (const c of [...COMMAND_CATALOG, ...DEVELOPER_COMMANDS]) {
    defs.push({
      id: c.id,
      action: c.action,
      label: c.label,
      kind: mapLegacyKind(c.kind),
      keywords: c.keywords || [],
      route: c.route,
      permission: c.permission ?? "*",
      minRole: c.id.startsWith("dev_") ? "developer" : undefined,
    });
  }

  for (const a of SHELL_QUICK_ACTIONS) {
    defs.push({
      id: a.id,
      action: a.id,
      label: a.label,
      kind: a.group === "create" ? "quick_action" : a.group === "command" ? "system" : "open_module",
      keywords: a.keywords,
      route: a.path,
      permission: "*",
    });
  }

  for (const m of shellModuleRegistry.list()) {
    defs.push({
      id: `mod_${m.id}`,
      action: `open_module_${m.id}`,
      label: `Open ${m.label}`,
      kind: m.id === "desktop" ? "open_desktop_window" : "open_module",
      keywords: m.keywords,
      route: m.route,
      permission: "*",
    });
  }

  defs.push(
    {
      id: "desk_close_focused",
      action: "close_focused_window",
      label: "Close Focused Window",
      kind: "close_window",
      keywords: ["close", "window", "desktop"],
      permission: "*",
    },
    {
      id: "desk_minimize_focused",
      action: "minimize_focused_window",
      label: "Minimize Focused Window",
      kind: "minimize_window",
      keywords: ["minimize", "window", "desktop"],
      permission: "*",
    },
    {
      id: "desk_maximize_focused",
      action: "maximize_focused_window",
      label: "Maximize Focused Window",
      kind: "maximize_window",
      keywords: ["maximize", "window", "desktop"],
      permission: "*",
    },
    {
      id: "desk_open_dashboard",
      action: "desktop_open_dashboard",
      label: "Desktop: Open Dashboard",
      kind: "open_desktop_window",
      keywords: ["desktop", "dashboard"],
      route: "/dashboard",
      permission: "*",
    },
    {
      id: "desk_open_city",
      action: "desktop_open_city",
      label: "Desktop: Open Enterprise City",
      kind: "open_desktop_window",
      keywords: ["desktop", "city"],
      route: "/enterprise-city",
      permission: "*",
    },
    {
      id: "desk_open_production",
      action: "desktop_open_production",
      label: "Desktop: Open Production",
      kind: "open_desktop_window",
      keywords: ["desktop", "production"],
      route: "/production-studio",
      permission: "*",
    },
    {
      id: "desk_open_crm",
      action: "desktop_open_crm",
      label: "Desktop: Open CRM",
      kind: "open_desktop_window",
      keywords: ["desktop", "crm"],
      route: "/crm",
      permission: "*",
    },
    {
      id: "desk_open_studio",
      action: "desktop_open_studio",
      label: "Desktop: Open AI Studio",
      kind: "open_desktop_window",
      keywords: ["desktop", "studio", "ai"],
      route: "/ai-studio",
      permission: "*",
    },
    {
      id: "sys_undo",
      action: "undo",
      label: "Undo Last Command",
      kind: "undo",
      keywords: ["undo", "history"],
      permission: "*",
      handler: () => {
        const batch = commandUndoStack.popUndo();
        if (!batch.length) return { ok: false, error: "nothing_to_undo" };
        commandUndoStack.setApplying(true);
        try {
          for (const e of batch) {
            navigateViaRuntime(e.previousPath);
          }
        } finally {
          commandUndoStack.setApplying(false);
        }
        return { ok: true, message: `undid ${batch.length}`, route: batch[0]?.previousPath };
      },
    },
    {
      id: "sys_redo",
      action: "redo",
      label: "Redo Command",
      kind: "redo",
      keywords: ["redo", "history"],
      permission: "*",
      handler: () => {
        const batch = commandUndoStack.popRedo();
        if (!batch.length) return { ok: false, error: "nothing_to_redo" };
        commandUndoStack.setApplying(true);
        try {
          for (const e of [...batch].reverse()) {
            const d = resolveCommand(e.commandId);
            if (d) executeDefinitionSync(d, e.args);
            else if (e.route) navigateViaRuntime(e.route);
          }
        } finally {
          commandUndoStack.setApplying(false);
        }
        return { ok: true, message: `redid ${batch.length}`, route: batch[batch.length - 1]?.route };
      },
    },
    {
      id: "dev_open_cmd_inspector",
      action: "open_command_inspector",
      label: "Developer: Command Runtime Inspector",
      kind: "navigate",
      keywords: ["inspector", "runtime", "commands", "dev"],
      route: "/command-runtime",
      permission: "*",
      minRole: "developer",
    },
  );

  commandRegistry.registerMany(defs);
}

async function runExecute(actionOrId: string, args: CommandArgs, sync: boolean): Promise<CommandResult> {
  commandRuntime.startup();
  const t0 = performance.now();
  const previousPath = currentPath();
  const def = resolveCommand(actionOrId);
  if (!def) {
    const miss: CommandResult = {
      id: actionOrId,
      action: actionOrId,
      label: actionOrId,
      ok: false,
      error: "command_not_found",
      durationMs: performance.now() - t0,
    };
    emitCommand("command.failed", {
      commandId: actionOrId,
      action: actionOrId,
      error: "command_not_found",
    });
    commandIntelligenceAnalytics.track(actionOrId, false, miss.durationMs, {
      ai: args.via === "ai",
      error: "command_not_found",
    });
    return miss;
  }

  running.add(def.id);
  emitCommand(
    "command.started",
    { commandId: def.id, action: def.action, label: def.label, args },
    def.route,
  );

  try {
    const handler = sync ? executeDefinitionSync(def, args) : await executeDefinition(def, args);
    const result = toResult(def, handler, performance.now() - t0);
    return finish(def, result, args, previousPath);
  } finally {
    running.delete(def.id);
  }
}

export const commandRuntime = {
  version: COMMAND_RUNTIME_VERSION,

  bindNavigator: bindCommandNavigator,
  setSurface: setCommandSurface,

  startup() {
    if (!booted) {
      registerCatalogCommands();
      commandMacros.hydrate();
      booted = true;
    }
    syncAuthIntoContextEngine();
    return {
      version: COMMAND_RUNTIME_VERSION,
      commands: commandRegistry.list().length,
      booted: true,
    };
  },

  isReady() {
    return booted;
  },

  register(def: CommandDefinition) {
    this.startup();
    return commandRegistry.register(def);
  },

  search(query: string, limit = 24) {
    this.startup();
    return commandRegistry.search(query, limit);
  },

  history(limit = 40) {
    return commandHistory.list(limit);
  },

  clearHistory() {
    commandHistory.clear();
    commandUndoStack.clearHistory();
  },

  undo() {
    return this.executeSync("sys_undo");
  },

  redo() {
    return this.executeSync("sys_redo");
  },

  undoStack() {
    return commandUndoStack.history();
  },

  beginGroup(label?: string) {
    return commandUndoStack.beginGroup(label);
  },

  endGroup() {
    return commandUndoStack.endGroup();
  },

  beginTransaction() {
    return commandUndoStack.beginTransaction();
  },

  commitTransaction() {
    return commandUndoStack.commitTransaction();
  },

  rollbackTransaction() {
    return commandUndoStack.rollbackTransaction();
  },

  /** Macros */
  macros: commandMacros,

  async playMacro(id: string): Promise<CommandResult[]> {
    this.startup();
    const macro = commandMacros.get(id);
    if (!macro) {
      return [
        {
          id,
          action: "play_macro",
          label: "Play Macro",
          ok: false,
          error: "macro_not_found",
          durationMs: 0,
        },
      ];
    }
    const out: CommandResult[] = [];
    this.beginGroup(`macro_${macro.name}`);
    try {
      for (const step of macro.steps) {
        out.push(await this.execute(step.action || step.commandId, step.args || {}));
      }
    } finally {
      this.endGroup();
    }
    return out;
  },

  /** AI intent → Runtime only · also fan-out matching Automation Engine triggers */
  async routeAiIntent(utterance: string) {
    this.setSurface("palette");
    try {
      const { automationTriggers } = await import("@/runtime/automation/automationTriggers");
      automationTriggers.fireAiIntent(utterance);
    } catch {
      /* automation package optional during early boot */
    }
    const intent = interpretAiIntent(utterance);
    if (!intent.ok || !intent.intent) {
      return {
        id: "ai_intent",
        action: "ai_intent",
        label: "AI Intent",
        ok: false,
        error: "intent_not_recognized",
        durationMs: 0,
        intent,
      } as CommandResult & { intent: typeof intent };
    }
    const res = await this.execute(intent.intent, {
      path: intent.route,
      via: "ai",
      utterance,
    });
    return { ...res, intent };
  },

  interpretAiIntent,

  policy: commandPolicy,
  launcher: launcherRegistry,
  analytics() {
    return commandIntelligenceAnalytics.snapshot();
  },

  runningCommands() {
    return [...running];
  },

  inspectorSnapshot() {
    this.startup();
    const stack = commandUndoStack.history();
    return {
      version: COMMAND_RUNTIME_VERSION,
      registered: commandRegistry.list(),
      history: commandHistory.list(40),
      undo: stack.undo,
      redo: stack.redo,
      running: this.runningCommands(),
      macros: commandMacros.list(),
      analytics: commandIntelligenceAnalytics.snapshot(),
      policy: commandPolicy.buildContext(),
      launcher: launcherRegistry.all(),
    };
  },

  async execute(actionOrId: string, args: CommandArgs = {}): Promise<CommandResult> {
    return runExecute(actionOrId, args, false);
  },

  executeSync(actionOrId: string, args: CommandArgs = {}): CommandResult {
    const t0 = performance.now();
    const previousPath = currentPath();
    this.startup();
    const def = resolveCommand(actionOrId);
    if (!def) {
      const miss: CommandResult = {
        id: actionOrId,
        action: actionOrId,
        label: actionOrId,
        ok: false,
        error: "command_not_found",
        durationMs: performance.now() - t0,
      };
      emitCommand("command.failed", {
        commandId: actionOrId,
        action: actionOrId,
        error: "command_not_found",
      });
      commandIntelligenceAnalytics.track(actionOrId, false, miss.durationMs, {
        error: "command_not_found",
      });
      return miss;
    }
    running.add(def.id);
    emitCommand(
      "command.started",
      { commandId: def.id, action: def.action, label: def.label, args },
      def.route,
    );
    try {
      const handler = executeDefinitionSync(def, args);
      const res = toResult(def, handler, performance.now() - t0);
      return finish(def, res, args, previousPath);
    } finally {
      running.delete(def.id);
    }
  },
};
