# Sprint 28.9 — Enterprise Automation Engine

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.9`  
**Constraint:** Reuse Workflow Runtime · EventBus · Command Runtime — no second workflow engine.

## Implementation summary

- Package `src/web/src/runtime/automation/` — engine · registry · queue · triggers · policies · scheduler · history  
- Triggers: Manual · Startup · Shutdown · Schedule · Webhook · EventBus · Command · AI Intent · Notification · Workflow Completed  
- Engine API: register · run · cancel · pause · resume · retry · validate  
- Queue statuses + policy-driven retry/backoff/concurrency/priority/error handling  
- Automation Center UI at `/automation` with Inspector · Queue · History · Timeline  
- Wired into Shell startup, Desktop launcher, Command Runtime, AI Studio strip, module catalog, Workflow Runtime inspector  

## Architecture

```
Triggers ──► Automation Engine (queue · policies)
                      │
                      ▼
              Workflow Runtime
                      │
         Command Runtime · EventBus · Notifications
```

## Modified / added (primary)

**New:** `src/web/src/runtime/automation/*`  
**Wired:** `enterpriseShellRuntime`, `App.tsx`, launcher/desktop, `commandRuntime.routeAiIntent`, shell quick actions, AI Studio strip, module catalog  
**Docs:** `AUTOMATION_ENGINE.md`, `AUTOMATION_QUEUE.md`, `AUTOMATION_POLICIES.md`, `AUTOMATION_CENTER.md`, `SPRINT_28_9_RESULT.md`, Architecture Map  

## Remaining work before Sprint 29.0

- Durable server-side automation queue / workers  
- Webhook signature verification + ingress API  
- Visual automation graph editor over Workflow Runtime registry  
- Distributed concurrency across tenants  
- Rich Notification Center deep-links for failed automations  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **215 passed** |
| build | OK |
