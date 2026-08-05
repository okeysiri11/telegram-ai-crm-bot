---
title: ADOS Enterprise Workflow Engine Implementation 1.3
aliases:
  - Workflow Engine Implementation
tags:
  - ados-os
  - workflow
  - implementation
status: active
---

# ADOS Enterprise Workflow Engine (Sprint OS 1.3)

## Location

`src/kernel/workflow/` — production TypeScript (`@ados/kernel` **1.3.0**).

Prior: [[KERNEL_IMPLEMENTATION_1_0]] · [[EVENT_BUS_IMPLEMENTATION_1_1]] · [[SERVICE_MESH_IMPLEMENTATION_1_2]]  
Design refs: [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]] · [[../workforce/WORKFLOW_PATTERNS|WORKFLOW_PATTERNS]]

## Backbone

```text
Kernel → Event Bus → Service Mesh → Workflow Engine → Runtime → Agents → Modules
```

## Interfaces

`IWorkflowEngine` · `IWorkflow` · `IWorkflowStep` · `IWorkflowExecutor` · `IWorkflowScheduler` · `IWorkflowContext`

## Verify

```bash
cd src/kernel && npm test && npm run typecheck && npm run build
```

README: `src/kernel/workflow/README.md`  
Architecture: `src/kernel/docs/WORKFLOW_ENGINE_ARCHITECTURE.md`
