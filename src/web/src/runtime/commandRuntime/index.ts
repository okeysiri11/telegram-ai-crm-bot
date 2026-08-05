/**
 * Command Runtime public API — Sprint 28.6 / 28.7.
 */

export { COMMAND_RUNTIME_VERSION } from "./commandTypes";
export type {
  CommandArgs,
  CommandDefinition,
  CommandExecutionContext,
  CommandHandlerResult,
  CommandHistoryEntry,
  CommandKind,
  CommandResult,
  CommandRole,
  CommandEventName,
  UndoableCommand,
  CommandMacro,
  CommandMacroStep,
  CommandPolicyContext,
  PolicyScope,
  CommandAnalyticsSnapshot,
} from "./commandTypes";

export { commandRegistry } from "./commandRegistry";
export { commandHistory } from "./commandHistory";
export {
  bindCommandNavigator,
  setCommandSurface,
  buildCommandContext,
  syncAuthIntoContextEngine,
  navigateViaRuntime,
} from "./commandContext";
export {
  canExecutePermission,
  meetsMinRole,
  resolveCommandRole,
  permissionsForRole,
  ROLE_PERMISSIONS,
} from "./commandPermissions";
export {
  assertCommandAllowed,
  executeDefinition,
  executeDefinitionSync,
  runDefaultHandler,
} from "./commandExecutor";
export { commandRuntime } from "./commandRuntime";
export { commandUndoStack } from "./commandUndoStack";
export { commandMacros } from "./commandMacros";
export { commandPolicy } from "./commandPolicy";
export { commandIntelligenceAnalytics } from "./commandIntelligenceAnalytics";
export { launcherRegistry, LAUNCHER_COMMAND_MAP } from "./launcherRegistry";
export { interpretAiIntent, type AiIntentResult } from "./aiIntentRouter";
