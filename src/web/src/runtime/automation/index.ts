/**
 * Automation Engine public API — Sprint 28.9.
 */

export {
  AUTOMATION_ENGINE_VERSION,
  AUTOMATION_PERSIST_KEY,
  AUTOMATION_HISTORY_KEY,
  DEFAULT_POLICY,
} from "./automationTypes";
export type {
  AutomationTriggerKind,
  AutomationQueueStatus,
  ErrorPolicy,
  AutomationPolicy,
  AutomationTrigger,
  AutomationDefinition,
  AutomationJob,
  AutomationTimelineEvent,
  AutomationHistoryEntry,
} from "./automationTypes";

export { normalizePolicy, validatePolicy, validateAutomation, computeBackoffDelay } from "./automationPolicies";
export { automationRegistry } from "./automationRegistry";
export { automationQueue } from "./automationQueue";
export { automationHistory } from "./automationHistory";
export { automationScheduler } from "./automationScheduler";
export { automationTriggers } from "./automationTriggers";
export { automationEngine } from "./automationEngine";
