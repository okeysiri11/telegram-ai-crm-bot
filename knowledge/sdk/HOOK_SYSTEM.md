---
title: ADOS Hook System
aliases:
  - Hook System
tags:
  - sdk
  - hooks
  - extension
status: foundation
---

# ADOS Hook System

## Purpose

Describe **extension hooks**—named points where plugins can observe or augment platform flow without modifying Core.

SDK: [[SDK_OVERVIEW]] · Lifecycle: [[PLUGIN_LIFECYCLE]] · Events: [[../ados_os/EVENT_BUS|EVENT_BUS]]

---

## Hook vs event

| | Hook | Event |
|--|------|-------|
| Timing | Often synchronous *around* an action | Asynchronous fact after/during |
| Purpose | Extend/validate/enrich | Notify decoupled consumers |
| Failure | May fail the action if policy says so | Dead-letter / retry |

Prefer events for fan-out analytics; hooks for gated extension (e.g. Before Deployment checks).

---

## Example hooks

| Hook | When | Typical plugin use |
|------|------|-------------------|
| **Before Task** | Prior to Agent Runtime Running | Validate, enrich context, policy check |
| **After Task** | Task unit Completed/Failed | Analytics, Learning hints, notifications |
| **Before Deployment** | Prior to Deploying | Security/compliance gates |
| **After Deployment** | DeploymentCompleted/failed | Sync, announce, index |
| **Before Provider Call** | Prior to UPP execute/stream | Budget, allow-list, redaction |
| **After Provider Call** | After normalized response | Cost meters, audit |
| **Knowledge Updated** | Durable knowledge write | Reindex, UI refresh, agent notify |
| **Memory Updated** | Memory Engine durable/working write | Cache invalidate, monitors |
| **Agent Started** | Agent Session Running | Telemetry, session binders |
| **Agent Completed** | Agent Session Completed/Failed/Cancelled | Cleanup, Learning extraction |

---

## Registration

- Declared in Manifest Entry Points and/or Hook API at Initialize.  
- Only active while plugin **Enabled**.  
- Ordered by priority; Security/platform hooks outrank partner hooks where conflicting.

---

## Rules

1. Hooks must be **idempotent** where retries exist.  
2. Hooks cannot Approve Architect/CEO gates by themselves—only contribute checks.  
3. Before Provider Call must not embed business domain logic (use Business Plugin + Task instead).  
4. Long-running work in hooks should enqueue Tasks, not block forever.  
5. Hook errors are logged; `Before *` failure policy is per-hook (fail-closed for Security).

---

## Related

[[SDK_API]] · [[PERMISSION_MODEL]] · [[../runtime/SUPERVISOR|SUPERVISOR]] · [[../execution/EXECUTION_STATES|EXECUTION_STATES]]
