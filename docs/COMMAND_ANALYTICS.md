# Command Analytics

**Sprint:** 28.7  
**API:** `commandIntelligenceAnalytics` / `commandRuntime.analytics()`

## Metrics

| Metric | Source |
|--------|--------|
| Execution time | per-command durationMs |
| Success rate | ok / total |
| Failures | count + recent error list |
| Usage | command id → count |
| Favorites | `commandHistory.favorites()` |
| AI usage | `via: "ai"` / palette AI |
| Popular | top commands |

## Persistence

Optional snapshot key `ews_cmd_analytics_v1` via `persist()`.

## Inspector

The Runtime Inspector Analytics card shows live snapshot values.
