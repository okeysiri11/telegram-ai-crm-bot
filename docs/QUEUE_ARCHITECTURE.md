# Queue Architecture

**Sprint:** 32.3 · **SoR:** `platform_jobs` (`JobQueue` + retry + DLQ)  
**Facade:** `platform_jobs/unified_queue.py` → `UnifiedQueueArchitecture`

## Lanes

| Lane | Purpose | Default priority | Default max retries |
|---|---|---|---|
| `ai` | AI / agent / provider jobs | 3 | 3 |
| `workflow` | Workflow step execution | 4 | 5 |
| `background` | General platform jobs | 6 | 5 |
| `notification` | Notification delivery | 2 | 4 |
| `render` | Media / studio render | 5 | 2 |

## Retry & dead letter

- Shared `JobRetryManager` — exponential backoff (1s … 300s).
- Exhausted retries → `JobState.DEAD_LETTER` via `move_to_dead_letter`.
- `fail_with_retry(job, error)` on the unified facade.

## Separation of concerns

| Concern | Owner |
|---|---|
| Infra queue | `platform_jobs.job_queue.JobQueue` |
| Logical lanes | `UnifiedQueueArchitecture` |
| Workflow step queue (engine-local) | `platform_workflow.task_queue` (adapter to workflow SoR) |
| Web UI jobs | `enterprise-runtime/jobManager` (client; not a second backend SoR) |

## Validation

```bash
python scripts/architecture_consolidation_scan.py
# or via
python scripts/architecture_sprint_review.py
```

## Related

[`CANONICAL_SERVICES.md`](./CANONICAL_SERVICES.md) · [`AUTOMATION_QUEUE.md`](./AUTOMATION_QUEUE.md)
