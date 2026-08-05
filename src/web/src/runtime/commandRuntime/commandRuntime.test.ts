import { beforeEach, describe, expect, it } from "vitest";
import {
  COMMAND_RUNTIME_VERSION,
  commandHistory,
  commandMacros,
  commandRegistry,
  commandRuntime,
  commandUndoStack,
  canExecutePermission,
  meetsMinRole,
  launcherRegistry,
  interpretAiIntent,
} from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { COMMAND_HISTORY_KEY } from "@/runtime/commandRuntime/commandHistory";
import { COMMAND_MACROS_KEY } from "@/runtime/commandRuntime/commandMacros";

describe("Sprint 28.6 Command Runtime", () => {
  beforeEach(() => {
    try {
      localStorage.removeItem(COMMAND_HISTORY_KEY);
      localStorage.removeItem(COMMAND_MACROS_KEY);
    } catch {
      /* ignore */
    }
    commandUndoStack.clearHistory();
    commandRuntime.startup();
  });

  it("boots with version and registers catalog commands", () => {
    const snap = commandRuntime.startup();
    expect(COMMAND_RUNTIME_VERSION).toBe("28.7");
    expect(snap.version).toBe("28.7");
    expect(snap.commands).toBeGreaterThan(20);
    expect(commandRegistry.get("open_crm") || commandRegistry.get("act_open_crm")).toBeTruthy();
    expect(commandRegistry.get("qa_studio")).toBeTruthy();
    expect(commandRegistry.get("close_focused_window")).toBeTruthy();
  });

  it("executes sync open commands and records history", () => {
    const res = commandRuntime.executeSync("open_crm");
    expect(res.ok).toBe(true);
    expect(res.route).toBe("/crm");
    expect(commandHistory.list(5)[0]?.commandId).toBe("act_open_crm");
    expect(commandHistory.recentCommandIds(3)).toContain("act_open_crm");
  });

  it("emits command.started and command.completed on the event bus", () => {
    const types: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type.startsWith("command.")) types.push(e.type);
    });
    commandRuntime.executeSync("open_settings");
    unsub();
    expect(types).toContain("command.started");
    expect(types).toContain("command.completed");
  });

  it("fails unknown commands and emits command.failed", () => {
    const types: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type.startsWith("command.")) types.push(e.type);
    });
    const res = commandRuntime.executeSync("definitely_missing_cmd_xyz");
    unsub();
    expect(res.ok).toBe(false);
    expect(res.error).toBe("command_not_found");
    expect(types).toContain("command.failed");
  });

  it("validates permissions and roles", () => {
    expect(canExecutePermission("crm", ["read", "crm"])).toBe(true);
    expect(canExecutePermission("admin", ["read"])).toBe(false);
    expect(canExecutePermission("*", ["read"])).toBe(true);
    expect(meetsMinRole("operator", "manager")).toBe(false);
    expect(meetsMinRole("admin", "developer")).toBe(true);
  });

  it("async execute resolves the same as sync for catalog routes", async () => {
    const res = await commandRuntime.execute("qa_dashboard");
    expect(res.ok).toBe(true);
    expect(res.route).toBe("/dashboard");
  });
});

describe("Sprint 28.7 Command Intelligence", () => {
  beforeEach(() => {
    try {
      localStorage.removeItem(COMMAND_HISTORY_KEY);
      localStorage.removeItem(COMMAND_MACROS_KEY);
    } catch {
      /* ignore */
    }
    commandUndoStack.clearHistory();
    commandRuntime.clearHistory();
    commandRuntime.startup();
  });

  it("supports undo and redo stacks", () => {
    commandRuntime.executeSync("open_crm");
    expect(commandUndoStack.canUndo()).toBe(true);
    const undo = commandRuntime.undo();
    expect(undo.ok).toBe(true);
    expect(commandUndoStack.canRedo()).toBe(true);
    const redo = commandRuntime.redo();
    expect(redo.ok).toBe(true);
  });

  it("records and plays macros", async () => {
    commandMacros.record();
    commandRuntime.executeSync("open_crm");
    commandRuntime.executeSync("open_settings");
    commandMacros.stop();
    const macro = commandMacros.save("Test Macro");
    expect(macro.steps.length).toBeGreaterThanOrEqual(2);
    const played = await commandRuntime.playMacro(macro.id);
    expect(played.every((p) => p.ok)).toBe(true);
    commandMacros.favorite(macro.id);
    expect(commandMacros.get(macro.id)?.favorite).toBe(true);
    commandMacros.rename(macro.id, "Renamed");
    expect(commandMacros.get(macro.id)?.name).toBe("Renamed");
    commandMacros.delete(macro.id);
    expect(commandMacros.get(macro.id)).toBeUndefined();
  });

  it("routes AI intent through Command Runtime", async () => {
    const intent = interpretAiIntent("open CRM please");
    expect(intent.ok).toBe(true);
    expect(intent.intent).toBe("open_crm");
    const res = await commandRuntime.routeAiIntent("open CRM please");
    expect(res.ok).toBe(true);
    expect(res.route).toBe("/crm");
  });

  it("maps launcher apps to registry command ids", () => {
    expect(launcherRegistry.resolveCommandId("crm")).toBe("act_open_crm");
    expect(launcherRegistry.resolveCommandId("dashboard")).toBe("mod_dashboard");
    expect(launcherRegistry.listDesktop().every((l) => Boolean(l.commandId))).toBe(true);
  });

  it("exposes inspector snapshot and analytics", () => {
    commandRuntime.executeSync("open_crm");
    const snap = commandRuntime.inspectorSnapshot();
    expect(snap.registered.length).toBeGreaterThan(10);
    expect(snap.analytics.executionCount).toBeGreaterThan(0);
    expect(snap.policy.scope).toBeTruthy();
  });

  it("supports transactions and clearHistory", () => {
    commandRuntime.beginTransaction();
    commandRuntime.executeSync("open_crm");
    commandRuntime.executeSync("qa_studio");
    commandRuntime.commitTransaction();
    expect(commandUndoStack.undoEntries().length).toBeGreaterThan(0);
    commandRuntime.clearHistory();
    expect(commandUndoStack.undoEntries().length).toBe(0);
  });
});
