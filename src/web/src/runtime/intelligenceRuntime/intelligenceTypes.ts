/**
 * Enterprise Intelligence Runtime types — Sprint 29.7.
 * Advisory insights & recommendations only — no autonomous execution.
 */

export const INTELLIGENCE_RUNTIME_VERSION = "29.7";
export const INTELLIGENCE_PERSIST_KEY = "ews_intelligence_runtime_v1";
export const INTELLIGENCE_API_PREFIX = "/api/enterprise-intelligence/v1";

export type InsightCategory =
  | "business_activity"
  | "workflow"
  | "citizen"
  | "asset"
  | "partner"
  | "project"
  | "district"
  | "operations";

export type RecommendationAudience =
  | "manager"
  | "owner"
  | "department"
  | "project"
  | "asset"
  | "partner"
  | "citizen";

export type RiskKind =
  | "process_delay"
  | "idle_asset"
  | "overloaded_employee"
  | "workflow_failure"
  | "missing_approval"
  | "operational";

export type Severity = "info" | "low" | "medium" | "high" | "critical";

export type IntelligenceEventName =
  | "InsightCreated"
  | "RecommendationCreated"
  | "RiskDetected"
  | "TrendUpdated"
  | "PatternDetected";

export type EnterpriseInsight = {
  id: string;
  category: InsightCategory;
  title: string;
  summary: string;
  severity: Severity;
  subjectIds: string[];
  metrics: Record<string, number | string>;
  source: string;
  createdAt: string;
};

export type EnterpriseRecommendation = {
  id: string;
  audience: RecommendationAudience;
  title: string;
  rationale: string;
  /** Suggested action id for Interaction Runtime — never auto-executed */
  suggestedActionId?: string;
  suggestedRoute?: string;
  priority: Severity;
  relatedInsightIds: string[];
  relatedRiskIds: string[];
  subjectIds: string[];
  requiresApproval: true;
  createdAt: string;
};

export type EnterpriseRisk = {
  id: string;
  kind: RiskKind;
  title: string;
  detail: string;
  severity: Severity;
  subjectIds: string[];
  mitigationHint?: string;
  createdAt: string;
};

export type TrendPoint = {
  key: string;
  label: string;
  value: number;
  delta: number;
  direction: "up" | "down" | "flat";
};

export type EnterpriseTrend = {
  id: string;
  domain: InsightCategory;
  label: string;
  points: TrendPoint[];
  updatedAt: string;
};

export type DetectedPattern = {
  id: string;
  name: string;
  description: string;
  confidence: number;
  evidence: string[];
  category: InsightCategory;
  createdAt: string;
};

export type AnalyticsSnapshot = {
  businessActivity: number;
  workflowBottlenecks: number;
  citizenOnline: number;
  assetUtilizationPct: number;
  partnerRelations: number;
  projectHealth: number;
  districtActivityAvg: number;
  openRisks: number;
  insightCount: number;
  recommendationCount: number;
};

export type IntelligenceCycleResult = {
  revision: number;
  insights: EnterpriseInsight[];
  recommendations: EnterpriseRecommendation[];
  risks: EnterpriseRisk[];
  trends: EnterpriseTrend[];
  patterns: DetectedPattern[];
  analytics: AnalyticsSnapshot;
  at: string;
};
