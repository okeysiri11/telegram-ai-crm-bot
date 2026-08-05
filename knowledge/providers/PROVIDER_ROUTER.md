---
title: ADOS Provider Router
aliases:
  - Provider Router
tags:
  - providers
  - upp
  - routing
status: foundation
---

# ADOS Provider Router

## Purpose

Explain how ADOS **routes** external capability requests: find providers that support the capability, choose the healthiest eligible provider, execute, and return a **normalized** response.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Manager: [[PROVIDER_MANAGER]] · Normalization: [[NORMALIZATION_LAYER]]

---

## Routing algorithm

### Example: Generate Image

```text
Generate Image
    ↓
Find provider supporting image_generation
    ↓
Choose healthiest provider
    ↓
Execute
    ↓
Return normalized response
```

### General steps

1. **Accept** normalized request (`capability`, params, user/security context, Package-ID).  
2. **Match** Registry: Status active/degraded (policy), capability ∈ Capabilities.  
3. **Rank** by Health (healthy > degraded), then Priority, then optional cost/latency class.  
4. **Authenticate** if session stale (`authenticate()`).  
5. **Execute** or **stream** via chosen provider.  
6. **Normalize** response (adapter + Normalization Layer).  
7. On failure class in [[FAILOVER_SYSTEM]] → next Fallback → repeat.  
8. Return normalized success or terminal normalized error to caller (Orchestrator/module).

---

## Selection policy

| Factor | Rule |
|--------|------|
| Capability match | Hard requirement |
| Health unhealthy / disabled | Skip |
| Priority | Prefer configured primary |
| Degraded | Allowed if no healthy candidate |
| Explicit pin | Optional `provider_id` override (ops/debug only; discouraged in modules) |
| User/tenant allow-list | Security scopes may exclude providers |

Modules should **not** pin vendors in business code; pinning is an OS/ops concern.

---

## Caller view

```text
Orchestrator / Module / Agent
    → UPP Router.execute(capability, normalized_request)
    → Normalized Response
```

Callers never import `openai` or `octokit` types.

---

## Streaming

Same routing; use `stream()` when capability and provider support it. Failover mid-stream: abort stream, retry on fallback if policy allows, else terminal error.

---

## Observability

- Log Provider ID chosen, capability, latency, failover count (no secrets).  
- Correlate with Package-ID and Event Bus where useful.

---

## Related

[[CAPABILITY_REGISTRY]] · [[FAILOVER_SYSTEM]] · [[PROVIDER_REGISTRY]]
