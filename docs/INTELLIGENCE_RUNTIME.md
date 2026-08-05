# Enterprise Intelligence Runtime

**Sprint:** 29.7  
**Package:** `src/web/src/runtime/intelligenceRuntime`  
**Policy:** Advisory only — **no autonomous execution**.

## Purpose

Continuously analyzes living Enterprise City activity and produces insights, recommendations, trends, and risk signals. All recommendations require user or workflow approval; this runtime never executes actions.

## Engines

| Component | Role |
|-----------|------|
| EnterpriseIntelligenceRuntime | Facade · analyze cycle · policy gate |
| InsightEngine | Category insights from live signals |
| RecommendationEngine | Audience-targeted advisory recs (`requiresApproval: true`) |
| PatternDetector | Correlated activity patterns |
| TrendAnalyzer | Incremental trend deltas |
| RiskDetector | Delays · idle assets · overload · failures · approvals |

## Analyzes

Business activity · workflow bottlenecks · citizen activity · asset utilization · partner relations · project health · district activity

## Events

`InsightCreated` · `RecommendationCreated` · `RiskDetected` · `TrendUpdated` · `PatternDetected`

EventBus: `intelligence_runtime_update` (payload includes `advisory: true`).

## UI / API

- UI: `/intelligence`
- REST: `/api/enterprise-intelligence/v1`
- `executeRecommendation()` always returns `autonomous_execution_forbidden`
