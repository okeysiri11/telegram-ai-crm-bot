/**
 * Enterprise Intelligence Runtime public API — Sprint 29.7.
 */

export {
  INTELLIGENCE_RUNTIME_VERSION,
  INTELLIGENCE_PERSIST_KEY,
  INTELLIGENCE_API_PREFIX,
} from "./intelligenceTypes";
export type {
  InsightCategory,
  RecommendationAudience,
  RiskKind,
  Severity,
  IntelligenceEventName,
  EnterpriseInsight,
  EnterpriseRecommendation,
  EnterpriseRisk,
  TrendPoint,
  EnterpriseTrend,
  DetectedPattern,
  AnalyticsSnapshot,
  IntelligenceCycleResult,
} from "./intelligenceTypes";

export { intelligenceEvents, publishIntelligenceEvent } from "./intelligenceEvents";
export { intelligenceCache } from "./intelligenceCache";
export { collectLiveSignals } from "./liveSignals";
export type { LiveSignals } from "./liveSignals";
export { patternDetector } from "./patternDetector";
export { trendAnalyzer } from "./trendAnalyzer";
export { riskDetector } from "./riskDetector";
export { insightEngine, buildAnalytics } from "./insightEngine";
export { recommendationEngine } from "./recommendationEngine";
export { intelligenceRuntime } from "./intelligenceRuntime";
export { intelligenceRuntimeApi, intelligenceApiPrefix } from "./intelligenceRuntimeApi";
