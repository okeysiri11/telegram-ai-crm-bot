# Automation Policies

**Sprint:** 28.9  
**Module:** `automationPolicies.ts`

## Fields

| Field | Role |
|-------|------|
| `retryCount` | Max automatic retries (0–20) |
| `timeoutMs` | Soft timeout around workflow start/execution (1s–10m) |
| `backoffMs` | Linear backoff base; delay = `backoffMs * attempt` |
| `concurrency` | Max active jobs for this automation (1–20) |
| `priority` | Queue sort key (0–100, higher first) |
| `errorPolicy` | `fail` · `retry` · `skip` · `continue` |

## Validation

`validatePolicy` / `validateAutomation` reject out-of-range values and incomplete triggers (schedule without `scheduleMs`, event without `eventType`, etc.).

## Defaults

```ts
{ retryCount: 2, timeoutMs: 60000, backoffMs: 500, concurrency: 2, priority: 50, errorPolicy: "retry" }
```
