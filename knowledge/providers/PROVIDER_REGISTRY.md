---
title: ADOS Provider Registry
aliases:
  - Provider Registry
tags:
  - providers
  - upp
  - registry
status: foundation
---

# ADOS Provider Registry

## Purpose

Describe the **catalog of provider instances** known to UPP—identity, capabilities, priority, health, ownership, status, and fallback links.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · OS Service Registry: [[../ados_os/SERVICE_REGISTRY|SERVICE_REGISTRY]] · Router: [[PROVIDER_ROUTER]]

---

## Registration record

| Field | Description |
|-------|-------------|
| **Provider ID** | Stable id (`provider.openai`, `provider.github`, `provider.telegram`) |
| **Name** | Human-readable label |
| **Version** | Adapter semver (`version()`) |
| **Capabilities** | List from [[CAPABILITY_REGISTRY]] |
| **Priority** | Integer or tier for selection within a capability (lower = preferred, policy-defined) |
| **Health** | Latest `health()` snapshot |
| **Owner** | Team/Lead accountable (usually Infrastructure Division) |
| **Status** | `registered` \| `initializing` \| `active` \| `degraded` \| `disabled` \| `failed` \| `retired` |
| **Fallback** | Next Provider ID(s) in chain for same capability (or policy ref) |

Optional: region, edition flags, cost class, max concurrency, event types produced.

---

## Example

```text
Provider ID:   provider.openai
Name:          OpenAI
Version:       1.2.0
Capabilities:  chat, embeddings, image_generation, speech_to_text, …
Priority:      10
Health:        healthy
Owner:         Infrastructure Division
Status:        active
Fallback:      provider.claude → provider.ollama  (for chat)
```

---

## Relationship to OS Service Registry

- Each active provider **also** appears as a Service Registry entry (`provider.*`) with Capabilities, Dependencies, Health, Owner.  
- Provider Registry holds **UPP-specific** fields (Priority, Fallback, capability routing metadata).  
- Kernel loads providers → both registries updated ([[../ados_os/STARTUP_SEQUENCE|STARTUP_SEQUENCE]]).

---

## Lifecycle

```text
register → validate interface → initialize → Status active
    → health loop
    → disable / failover / replace
    → shutdown → retired
```

Duplicate Provider ID requires controlled version upgrade; two instances of same vendor use distinct IDs (`provider.openai.us`, `provider.openai.eu`) if needed.

---

## Query patterns

| Query | Use |
|-------|-----|
| By Capability | Router candidate set |
| By Provider ID | Admin, failover target |
| By Status=active + Health | Eligible set |
| By Priority | Ordered fallback chain |

---

## Related

[[PROVIDER_MANAGER]] · [[FAILOVER_SYSTEM]] · [[SUPPORTED_PROVIDERS]]
