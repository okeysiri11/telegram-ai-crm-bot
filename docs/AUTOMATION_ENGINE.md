# Automation Engine

**Sprint:** 28.9  
**Package:** `src/web/src/runtime/automation/`  
**Version:** `AUTOMATION_ENGINE_VERSION = "28.9"`

## Role

Enterprise Automation Engine sits **on top of Workflow Runtime**. It does not reimplement workflow execution.

Responsibilities:

- Register reusable automations (workflow id + triggers + policies)
- Enqueue and pump execution jobs
- Retry / timeout / concurrency / priority policies
- Trigger fan-in from Manual · Startup · Shutdown · Schedule · Webhook · EventBus · Command Runtime · AI Intent · Notification · Workflow Completed
- History + inspector monitoring

## Architecture

```
Triggers (EventBus · Command · AI · Schedule · …)
              │
              ▼
      Automation Engine
   Registry · Queue · Policies · History
              │
              ▼
      Workflow Runtime.start(workflowId)
              │
              ▼
      Command Runtime · EventBus · Notifications
```

## API

```ts
automationEngine.registerAutomation(def)
automationEngine.runAutomation(id, triggerKind?)
automationEngine.cancelAutomation(jobId)
automationEngine.pauseAutomation(automationId)
automationEngine.resumeAutomation(automationId)
automationEngine.retryAutomation(jobId)
automationEngine.validateAutomation(def)
automationEngine.fireWebhook(token, payload?)
automationEngine.inspectorSnapshot()
```

## Integration

| Surface | Wiring |
|---------|--------|
| Shell | `enterpriseShellRuntime.startup()` → `automationEngine.startup()` |
| Desktop | launcher `automation` / `automation_center` → `auto_open_center` |
| Command Runtime | `auto_open_center`, `auto_run`; AI intent → `automationTriggers.fireAiIntent` |
| Workflow Runtime | sole execution target |
| EventBus | `workflow_update` / `command.*` / `notification` / `runtime_update` |
| AI Studio | strip link → `/automation` |
| Module catalog | deepLink `/automation` |

## Related

- [`AUTOMATION_QUEUE.md`](./AUTOMATION_QUEUE.md)
- [`AUTOMATION_POLICIES.md`](./AUTOMATION_POLICIES.md)
- [`AUTOMATION_CENTER.md`](./AUTOMATION_CENTER.md)
- [`WORKFLOW_RUNTIME.md`](./WORKFLOW_RUNTIME.md)
- [`SPRINT_28_9_RESULT.md`](./SPRINT_28_9_RESULT.md)
