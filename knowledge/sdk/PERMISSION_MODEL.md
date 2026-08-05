---
title: ADOS Plugin Permission Model
aliases:
  - Permission Model
  - Plugin Permissions
tags:
  - sdk
  - security
  - permissions
status: foundation
---

# ADOS Plugin Permission Model

## Purpose

Describe **plugin permissions**—deny-by-default grants that scope what an Enabled plugin may do through SDK APIs.

SDK: [[SDK_OVERVIEW]] · Manifest: [[PLUGIN_MANIFEST]] · Security: [[../providers/PROVIDER_SECURITY|PROVIDER_SECURITY]]

---

## Permission classes

| Permission | Allows |
|------------|--------|
| **Read** | Read Knowledge/Task/Workflow metadata and allowed events |
| **Write** | Create/update allowed Knowledge/Memory/Task artifacts |
| **Execute** | Start Tasks/workflows, invoke non-secret Provider capabilities |
| **Admin** | Enable/Disable other plugins (restricted), manage grants within tenant policy |
| **Provider Access** | Call Provider API (optionally capability-scoped) |
| **Memory Access** | Memory API read/write within declared scopes (working vs durable) |
| **Workflow Access** | Register or run workflows |
| **Secret Access** | Resolve secret handles for provider auth (highest sensitivity) |

Permissions may be **scoped** (Project, capability, event type, memory class).

---

## Grant model

```text
Manifest requests permissions
    → Admin / Security reviews
    → Grant stored per Plugin ID + Version range
    → Enable activates grant
    → Disable/Remove revokes use (Remove destroys grant)
```

Request ≠ Grant. Store-verified plugins may have pre-cleared permission templates; Secret Access and Admin still require explicit enterprise approval.

---

## Mapping to SDK APIs (illustrative)

| API | Minimum permission |
|-----|-------------------|
| Knowledge read | Read |
| Knowledge write | Write (+ Knowledge policy) |
| Memory API | Memory Access |
| Provider API | Provider Access (+ Execute often) |
| Workflow API | Workflow Access |
| Task API | Execute (write tasks may need Write) |
| Runtime cancel | Execute or Admin |
| Security elevation request | Read; grant needs Admin/Security |
| Event publish | Write or Execute (type allow-list) |
| Secret resolve | Secret Access |

---

## Rules

1. **Least privilege** — Store and review reject over-broad manifests.  
2. Secret Access never implied by Provider Access.  
3. Admin does not bypass CEO/Architect L3 product gates.  
4. UI Plugins default to Read; Write/Execute require justification.  
5. Security Plugins may hold elevated rights but Enable is dual-controlled.  
6. Audit every grant change and Secret Access use.

---

## Related

[[PLUGIN_STORE]] · [[PLUGIN_LIFECYCLE]] · [[../runtime/EXECUTION_LOG|EXECUTION_LOG]] · [[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]]
