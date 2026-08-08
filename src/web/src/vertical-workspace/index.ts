/**
 * Sprint 42.8 — Universal Vertical Workspace Framework.
 */

export type { VerticalDef, VerticalNavItem, VerticalAgent } from "./types";
export {
  VERTICAL_WORKSPACES,
  VERTICAL_BY_ID,
  getVertical,
  verticalHomePath,
  sectionPath,
} from "./catalog";
export { useVerticalWorkspaceStore } from "./verticalWorkspaceStore";
export { WorkspaceSwitcher } from "./WorkspaceSwitcher";
export { VerticalWorkspacePage } from "./VerticalWorkspacePage";
export { VerticalDashboard } from "./VerticalDashboard";
