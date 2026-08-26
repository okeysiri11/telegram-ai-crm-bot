/** Sprint 42.1 — Multi-role parallel workspaces. */

export { getWorkspaceSlot, wsKey, workspaceSlotLabel, WORKSPACE_PORT_SLOTS } from "./workspaceSlot";
export { MULTI_ROLE_DEMO_USERS, demoUserByEmail, isMultiRoleDemoEmail, MULTI_ROLE_DEMO_PASSWORD } from "./demoUsers";
export type { DemoUserDef } from "./demoUsers";
export { applyDemoUserSession, openClientDemoWorkspace, openOwnerDemoWorkspace } from "./applyDemoSession";
export { ClientOnboardingPage } from "./ClientOnboardingPage";
export {
  loadClientOnboarding,
  saveClientOnboarding,
  isClientOnboardingComplete,
  markClientOnboardingComplete,
  resetClientOnboarding,
  CLIENT_ONBOARDING_STEPS,
} from "./clientOnboardingStore";
export { seedClientDemoData, readClientDemoSeed } from "./clientDemoSeed";
export { snapshotRoleSession, restoreRoleSession, switchRoleSession } from "./roleSessionVault";
export { DevRoleSwitcher } from "./DevRoleSwitcher";
export { WorkspaceSlotBanner } from "./WorkspaceSlotBanner";
