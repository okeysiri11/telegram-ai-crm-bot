/**
 * Sprint 33.1 — Enterprise UX Revolution (Foundation).
 * Frontend-only: modes, role workspaces, context nav, AI intents, executive dashboard.
 */

export {
  useExperienceModeStore,
  type ExperienceMode,
  EXPERIENCE_MODE_KEY,
} from "./experienceModeStore";
export { SIMPLE_MODE_NAV, SIMPLE_MODE_NAV_IDS, isSimpleModeRoute, filterNavForMode } from "./simpleModeNav";
export {
  ROLE_WORKSPACE_CATALOG,
  roleWorkspaceById,
  ENTERPRISE_UX_ROLES,
  type RoleWorkspace,
} from "./roleWorkspaceCatalog";
export {
  MODULE_CONTEXT_NAV,
  resolveModuleContext,
  type ContextNavItem,
  type ModuleContext,
} from "./moduleContextNav";
export { useModuleContextNav } from "./useModuleContextNav";
export {
  AI_NAVIGATION_INTENTS,
  matchAiNavigationIntent,
  type AiNavigationIntent,
  type AiNavigationMatch,
} from "./aiNavigationIntents";
export { SimpleProModeToggle } from "./SimpleProModeToggle";
export { RoleWorkspaceSelector } from "./RoleWorkspaceSelector";
export { ExecutiveSummaryDashboard } from "./ExecutiveSummaryDashboard";
export { QUICK_ACTION_SECTIONS, buildUxPaletteCommands } from "./quickActionSections";
export { UX_REVOLUTION_VERSION, UX_REVOLUTION_SPRINT } from "./constants";
export { ensureProMode } from "./ensureProMode";
