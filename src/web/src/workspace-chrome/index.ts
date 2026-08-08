/** Unified Enterprise Workspace chrome — Sprint 32.3.6 / 41.3. */
export { GlobalWorkspaceBar } from "./GlobalWorkspaceBar";
export { WorkspaceQuickDock } from "./WorkspaceQuickDock";
export {
  useWorkspaceDockStore,
  WORKSPACE_DOCK_KEY,
  DOCK_CATALOG,
} from "./workspaceDockStore";
export type { DockFavourite } from "./workspaceDockStore";
export { UnifiedToastStrip } from "./UnifiedToastStrip";
export { registerUnifiedWorkspaceSearch } from "./registerUnifiedSearch";
export {
  GLOBAL_QUICK_SWITCH,
  detectActiveEcosystem,
  labelForSegment,
  workspaceStatusLabel,
} from "./workspaceContext";
export {
  UnifiedIntentBar,
  TaskInboxPanel,
  executeUnifiedIntent,
  classifyUnifiedIntent,
  useUnifiedIntentStore,
  resolveVerticalIntentConfig,
} from "./unified-intent";
