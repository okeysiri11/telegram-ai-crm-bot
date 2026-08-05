---
title: ADOS Provider Manager
aliases:
  - Provider Manager
tags:
  - providers
  - upp
status: foundation
---

# ADOS Provider Manager

## Purpose

The **Provider Manager** owns the operational lifecycle of providers inside UPP: load, validate, resolve dependencies, match capabilities, monitor health, fail over, and replace—without touching ADOS Core or business modules.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Interface: [[PROVIDER_INTERFACE]] · Registry: [[PROVIDER_REGISTRY]]

---

## Responsibilities

### Provider loading

- Discover provider packages/manifests at OS startup (and hot-load when policy allows).  
- Instantiate adapters; call `initialize()`.  
- Write [[PROVIDER_REGISTRY]] + OS Service Registry records.

### Provider validation

- Confirm all contract methods exist and `capabilities()` ⊆ [[CAPABILITY_REGISTRY]].  
- Reject providers that embed domain modules or read business stores.  
- Validate configuration schema and secret **handles** (not values).

### Dependency resolution

- Order init by declared deps (e.g. storage before a provider that requires it).  
- Refuse activation if critical dependency unhealthy.  
- Prefer events over hard cycles between providers.

### Capability matching

- Maintain index: capability → [Provider IDs].  
- Serve Router candidate lists with Priority + Health.  
- Support multi-capability providers (one OpenAI entry, many capabilities).

### Health monitoring

- Periodic `health()` probes; on change update Registry and emit `ServiceHealthChanged` (OS bus).  
- Mark `degraded` / `unhealthy`; notify Owner on sustained failure.

### Automatic failover

- On timeout, unavailable, quota, auth expired → invoke [[FAILOVER_SYSTEM]].  
- Select next Fallback; retry normalized request.  
- Never invent a new vendor API in Manager—only re-route.

### Provider replacement

- Hot-swap: initialize new Version → drain old → `shutdown()` old → update Registry.  
- Same Provider ID upgrade or cutover to different Provider ID for a capability.  
- Orchestrator/modules keep calling capabilities; they do not recompile.

---

## Manager control flow

```text
Load → Validate → Resolve deps → Initialize → Register
     → Health loop
     → (Router asks for capability)
     → (Failover / Replace as needed)
     → Shutdown on OS drain
```

---

## Boundaries

| Manager does | Manager does not |
|--------------|------------------|
| Operate providers | Decide CRM business rules |
| Expose eligible providers to Router | Call vendor SDKs itself (adapters do) |
| Enforce interface & security hooks | Modify ADOS Core for new vendors |
| Coordinate failover | Skip Normalization Layer |

---

## Related

[[PROVIDER_ROUTER]] · [[PROVIDER_SECURITY]] · [[../ados_os/KERNEL|KERNEL]]
