/** Autonomous Enterprise & Human-in-the-Loop — Sprint 33.5. */
export {
  AUTONOMY_LEVELS,
  APPROVAL_CATEGORIES,
  CRITICAL_ACTIONS,
  levelLabel,
  resolveDefaultLevel,
} from "./autonomyCatalog";
export type { AutonomyLevel, ApprovalCategory, RiskLevel, ApprovalStatus } from "./autonomyCatalog";
export {
  getAutonomyLevel,
  setAutonomyLevel,
  listApprovals,
  decideApproval,
  listJournal,
} from "./autonomyState";
export { deriveAutonomy } from "./deriveAutonomy";
export type { AutonomyBundle, AutonomyDashboard, GovernanceStats } from "./deriveAutonomy";
export {
  AutonomousEnterprisePage,
  AutonomyStrip,
  AutonomousWidgetCompact,
} from "./AutonomousEnterprisePage";
