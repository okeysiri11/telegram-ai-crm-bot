---
title: ADOS Provider Interface
aliases:
  - Provider Interface
  - Provider Contract
tags:
  - providers
  - upp
  - contract
status: foundation
---

# ADOS Provider Interface

## Purpose

Define the **standard provider contract**. Every provider—LLM, VCS, messaging, storage, or vertical SaaS—must implement this interface so ADOS can load, health-check, route, and replace it uniformly.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Manager: [[PROVIDER_MANAGER]] · Security: [[PROVIDER_SECURITY]]

---

## Contract methods

Every provider must implement:

| Method | Responsibility |
|--------|----------------|
| **initialize()** | Load configuration, establish clients, validate required secrets present (not values in logs) |
| **shutdown()** | Flush, revoke short-lived sessions, release connections; emit stopped health |
| **health()** | Return health status + optional latency/quota signals |
| **authenticate()** | Perform or refresh auth (API key check, OAuth token, service account) |
| **execute()** | Run a normalized capability request; return normalized response |
| **stream()** | Stream partial results for capabilities that support streaming; same normalization |
| **events()** | Declare/subscribe provider-side event mappings (webhooks → ADOS events) |
| **capabilities()** | List supported capability ids from [[CAPABILITY_REGISTRY]] |
| **configuration()** | Return non-secret config schema/values (models, regions, base URLs) |
| **version()** | Provider adapter version (semver) |

---

## Method semantics

### initialize()

- Called once by Provider Manager after registry accept.  
- Must be idempotent or clearly reject double-init.  
- Failure → provider Status = failed; not eligible for routing.

### shutdown()

- Called on OS drain or provider replacement.  
- In-flight `execute`/`stream` should be cancelled or drained per policy.  
- After shutdown, Router must not select this instance.

### health()

Returns at least:

```text
status: healthy | degraded | unhealthy | unknown
checks: { auth, reachability, quota, ... }
message: <optional>
```

Aligns with [[PROVIDER_REGISTRY]] Health and OS Service Registry.

### authenticate()

- Establishes credentials for subsequent calls.  
- May be invoked on start and on `authentication expired` ([[FAILOVER_SYSTEM]]).  
- Must not log secrets.

### execute()

```text
Input:  Normalized Request (capability, params, context, Package-ID)
Output: Normalized Response (ok | error, data, provider_meta)
```

Vendor-specific payloads stay inside the adapter; only normalized shapes cross the UPP boundary ([[NORMALIZATION_LAYER]]).

### stream()

- Same input as execute; yields normalized chunks then a terminal response.  
- Providers without streaming return a single chunk equivalent or explicit `capability unsupported`.

### events()

- Maps inbound webhooks / polling to ADOS Event Bus types where relevant.  
- Outbound: may publish infrastructure facts only (e.g. delivery failed)—never domain decisions.

### capabilities()

- Subset of [[CAPABILITY_REGISTRY]].  
- Router uses this for matching; lying about capabilities is a validation failure.

### configuration()

- Safe, non-secret settings for operators and Manager.  
- Secret references by **handle/id**, never raw key material.

### version()

- Adapter version, distinct from upstream vendor API version (report vendor API in configuration/meta if needed).

---

## Interface invariants

1. No CRM/ERP/Marketplace logic inside methods.  
2. All user/tenant context passed in; provider does not invent enterprise policy.  
3. Errors mapped to normalized error codes (timeout, unavailable, quota, auth, invalid).  
4. `capabilities()` ⊆ registered capabilities for that Provider ID.

---

## Related

[[PROVIDER_REGISTRY]] · [[NORMALIZATION_LAYER]] · [[PROVIDER_SECURITY]]
