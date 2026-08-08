/** Sprint 46.4 — Unified Intent Bar public exports */
export { UnifiedIntentBar } from "./UnifiedIntentBar";
export type { UnifiedIntentBarProps } from "./UnifiedIntentBar";
export { TaskInboxPanel } from "./TaskInboxPanel";
export { executeUnifiedIntent, intentKindLabel } from "./executeUnifiedIntent";
export type { ExecuteCtx } from "./executeUnifiedIntent";
export {
  classifyUnifiedIntent,
  isChatCapabilityQuestion,
  isSearchRefine,
  CAPABILITY_REPLY_RU,
  EMPTY_EXAMPLES,
  QUICK_HINTS,
  friendlyCategoryLabel,
} from "./unifiedIntentRouter";
export { useUnifiedIntentStore } from "./unifiedIntentStore";
export { resolveVerticalIntentConfig, VERTICAL_INTENT_CONFIGS } from "./verticalIntentConfig";
export type {
  UnifiedIntentKind,
  InteractionStatus,
  IntentInteraction,
  VerticalIntentConfig,
} from "./unifiedIntentTypes";
export { STATUS_LABEL_RU } from "./unifiedIntentTypes";
