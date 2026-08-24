export type {
  DistanceTier,
  LodThresholds,
  LodScoreInput,
  LodVisibilityInput,
  LodDecision,
  LodDiagnostics,
} from "./lodTypes";
export { lodThresholdsFor, radiusFromBounds, LOD_HYSTERESIS, LOD_TARGET_PROTECT_M } from "./lodThresholds";
export {
  scoreLodPriority,
  starveBoost,
  screenSpaceImportance,
  isScreenImportant,
  isSeaOrCoastProtected,
  resolveRuntimeAssetUrl,
  isInventedLodUrl,
} from "./lodScore";
export { classifyDistanceTier, classifyDistanceTierHysteresis, shouldAssetBeVisible } from "./lodVisibility";
export { LodVisibilityManager } from "./lodManager";
export type { LodEvalAsset, LodEvalContext } from "./lodManager";
