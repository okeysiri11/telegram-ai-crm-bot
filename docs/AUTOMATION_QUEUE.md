# Automation Queue

**Sprint:** 28.9  
**Module:** `automationQueue.ts`

## Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Waiting for a concurrency slot |
| `running` | `workflowRuntime.start` in flight |
| `waiting` | Workflow paused / wait_event / automation paused |
| `completed` | Terminal success (or skip/continue policy) |
| `failed` | Terminal failure after retries exhausted |
| `cancelled` | Operator cancel |
| `retry` | Backoff delay before re-queue as `pending` |

## Pump

`automationEngine` pumps pending jobs up to max concurrency across enabled automations. Per-automation concurrency is also enforced at enqueue time.

## Timeline

Each job keeps an in-memory timeline (`enqueued` · `running` · `retry` · `completed` · …) used by the Automation Inspector Execution Timeline.

## Persistence

Queue is in-memory for the SPA session. History entries persist under `ews_automation_history_v1`.
