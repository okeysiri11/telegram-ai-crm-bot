---
title: ADOS Enterprise Event Bus Implementation 1.1
aliases:
  - Event Bus Implementation
tags:
  - ados-os
  - event-bus
  - implementation
status: active
---

# ADOS Enterprise Event Bus (Sprint OS 1.1)

## Location

`src/kernel/event_bus/` — production TypeScript.

Design (prior): [[EVENT_BUS]] · Kernel: [[KERNEL_IMPLEMENTATION_1_0]]

## Backbone

```text
Kernel → Event Bus → Runtime → Agents → Business Modules
```

Business modules do not call each other; they publish/subscribe.

## Capabilities

publish · subscribe · unsubscribe · once · broadcast · replay · history · filter · sync/async/delayed · priority · sticky · wildcards

## Verify

```bash
cd src/kernel && npm test && npm run typecheck && npm run build
```

Package README: `src/kernel/event_bus/README.md`  
Architecture: `src/kernel/docs/EVENT_BUS_ARCHITECTURE.md`
