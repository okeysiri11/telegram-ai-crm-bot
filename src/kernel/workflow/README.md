# ADOS Enterprise Workflow Engine (Sprint OS 1.3)

## Purpose

Orchestrates **multi-step execution** across agents, services, providers, and business modules — without direct module coupling.

```text
Kernel → Event Bus → Service Mesh → Workflow Engine → Runtime → Agents → Modules
```

## Location

`src/kernel/workflow/`

| File | Role |
|------|------|
| `WorkflowEngine.ts` | Facade + enterprise delivery example |
| `WorkflowDefinition.ts` | Graph definition |
| `WorkflowInstance.ts` | Running instance |
| `WorkflowStep.ts` | Step node |
| `WorkflowExecutor.ts` | Execution / parallel / retry / compensate |
| `WorkflowScheduler.ts` | Delays & deferred resume |
| `WorkflowState.ts` | Instance status FSM |
| `WorkflowContext.ts` | Shared variables |
| `WorkflowHistory.ts` | Persisted history log |
| `WorkflowValidator.ts` | Pre-flight validation |

## Capabilities

- Sequential & parallel branches  
- Conditional execution  
- Retry policies & timeouts  
- Rollback / compensation steps  
- Approval gates  
- Event-driven wait/resume  
- History persistence  
- Resume after interruption (Suspended / Waiting*)  

## Quick start

```ts
import {
  createWorkflowEngine,
  createEnterpriseDeliveryWorkflow,
} from "@ados/kernel";

const engine = createWorkflowEngine();
engine.registerHandler("agent.backend", async (ctx) => { /* … */ });
engine.register(createEnterpriseDeliveryWorkflow());

let inst = await engine.start("enterprise.delivery");
// … waits at approval.release
inst = await engine.approve(inst.id, "approval.release", { approved: true });
```

## Architecture rules

- Depends only on Kernel services (Event Bus + Service Mesh via DI)  
- No business-module imports  
- Plugin-ready handlers (`registerHandler`)  
- Provider-independent (mesh capabilities optional on task steps)  

## Verify

```bash
cd src/kernel && npm test && npm run typecheck
```

See `../docs/WORKFLOW_ENGINE_ARCHITECTURE.md`.
