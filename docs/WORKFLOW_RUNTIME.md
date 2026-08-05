# Workflow Runtime — Sprint 36.2

## Architecture decision

**Canonical SoR:** `platform_workflow` (existing).  
**Rejected:** new `platform_workflow_runtime` / `platform_core/` package (second engine forbidden).

Sprint 36.2 productizes a **graph execution runtime** *inside* `platform_workflow/`:

| Layer | Module |
|-------|--------|
| Task collaboration engine (existing) | `workflow_engine.py` |
| Graph runtime (36.2) | `runtime_engine.py` |
| Registry + versions | `registry.py` |
| Facades / API | `service.py`, `router.py` |
| Models | `runtime_models.py` |

```
Designer / REST / UI
        ↓
WorkflowRuntimeService
        ↓
WorkflowRegistry  +  WorkflowRuntimeEngine
        ↓
platform_enterprise_event_bus (topic=workflow)
        ↓
PlatformEventBus (SoR)
```

---

## Capabilities

- **Conditions** — expression eval over `vars` / `outputs` / `memory`
- **Loops** — iterate `vars[list]` with body step
- **Parallel branches** — concurrent branch walks + join
- **Expressions / set_variable**
- **Retry** per step (`max_retries`)
- **Rollback** via `compensate` step links
- **Timeout** per run / per step
- **Cancellation**
- **Sync / async / scheduled** execution
- **Checkpoints + logs + execution history**

### Step kinds

`start` · `end` · `task` · `condition` · `loop` · `parallel` · `delay` · `set_variable` · `expression` · `rollback`

### Registry states

`draft` → `published` → `archived` (+ semantic versions)

---

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/workflows/*` | Primary product API |
| `/api/workflow-runtime/*` | Alias |
| `/management/v1/workflows/*` | Management dual-prefix |

Key routes: list/create/update workflows, publish/archive, versions, execute, runs, cancel/retry/rollback, scheduler tick, monitoring.

---

## Database

Alembic `k4e567890123` (after `j3d456789012`):

- `workflow_registry`
- `workflow_versions`
- `workflow_runs`
- `workflow_steps`
- `workflow_variables`
- `workflow_logs`
- `workflow_checkpoints`

---

## UI

`/platform-builder/workflows` — Designer, Runtime, Executions, Logs, Variables, Versions, Scheduler, Monitoring.

---

## Examples

```python
from platform_workflow import workflow_runtime_service as wrs

wrs.ensure_seed()
run = await wrs.execute("wf_approval_pipeline", {"variables": {"amount": 1000}})
assert run["status"] == "completed"
```

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8080/api/workflows/workflows/wf_loop_sum/execute \
  -d '{"variables":{"items":[1,2,3],"items_out":[]}}'
```

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_workflow_runtime_36_2.py -vv
```

---

## See also

- [WORKFLOW_ENGINE.md](./WORKFLOW_ENGINE.md)
- [EVENT_BUS.md](./EVENT_BUS.md)
- [SERVICE_BUILDER.md](./SERVICE_BUILDER.md)
- [SPRINT_36_2_RESULT.md](./SPRINT_36_2_RESULT.md)
