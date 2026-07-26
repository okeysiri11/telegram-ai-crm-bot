/** Enterprise Strategy & OKR Intelligence — Sprint 33.8. */

export { ENTERPRISE_GOALS, getGoalDef } from "./goalsCatalog";
export type { EnterpriseGoalDef, GoalDomain, GoalPriority } from "./goalsCatalog";
export { deriveOkr, alignRecommendation } from "./deriveOkr";
export type {
  OkrBundle,
  LiveGoal,
  OkrCard,
  GoalAlignment,
  ExecutiveHorizon,
  TimelineItem,
  McGoalsBlock,
  GoalStatus,
} from "./deriveOkr";
export {
  EnterpriseOkrPage,
  OkrStrip,
  EnterpriseGoalsWidgetCompact,
} from "./EnterpriseOkrPage";
