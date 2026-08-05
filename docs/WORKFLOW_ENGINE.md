# Workflow Engine

**Sprint:** 28.8  
**Module:** `workflowExecution.ts` + `workflowCatalog.ts`

## Node kinds

| Kind | Behavior |
|------|----------|
| start / end / sequential | Graph control |
| parallel | Schedule branch heads |
| condition | `vars[conditionKey]` truthiness |
| loop | Body until `maxIterations` |
| delay | Wait then resume (timer) |
| wait_event | Pause until EventBus type |
| ai_action | `commandRuntime.routeAiIntent` / execute `via:ai` |
| approval | Pause until `vars.approved` |
| notification | Notification store |
| command | `commandRuntime.execute` |
| http / webhook | fetch or simulated |
| script | Future-ready stub |

## Context

`vars` · `memory` · `outputs` · `temp` · `meta`

## Catalog sources

- `BUSINESS_WORKFLOW_TEMPLATES` → `tpl_*` graphs
- Demo: `demo_parallel_ops`, `demo_approval_gate`, `demo_wait_event`

No second workflow engine — vertical live-workflow pages remain UI demos and are not duplicated here.

## Production Studio builder (Sprint 32.0)

`WorkflowBuilderPanel` in `ai-production-studio` is a **pipeline stage UI** over Production pipelines + Runtime execution.  
It does **not** replace this Workflow Engine or the kernel `WorkflowEngine`. Graph workflows continue to use `workflowExecution.ts` / `platform_workflow`.
