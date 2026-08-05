---
title: ADOS Normalization Layer
aliases:
  - Normalization Layer
tags:
  - providers
  - upp
  - api
status: foundation
---

# ADOS Normalization Layer

## Purpose

Describe how **different providers expose different APIs** while ADOS exposes **one API** per capability. Vendor diversity stops at the adapter; Orchestrator and modules see only normalized requests and responses.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Interface: [[PROVIDER_INTERFACE]] · Router: [[PROVIDER_ROUTER]]

---

## Model

```text
OpenAI
Claude
Gemini
Local LLM
    ↓
Normalized Request
    ↓
ADOS (Orchestrator / Modules / Agents)
    ↓
Normalized Response
```

(Direction of call: ADOS issues Normalized Request → Router → Provider maps to vendor API → maps result to Normalized Response → ADOS.)

---

## Normalized Request (common envelope)

```text
capability:     chat | image_generation | …
params:         { … capability-specific … }
context:
  Package-ID:   …
  user / tenant / roles
  locale / timeout hints
options:
  stream:       bool
  provider_pin: optional (ops only)
```

### Example: chat params (illustrative)

```text
messages: [{ role, content }]
temperature: …
max_tokens: …
tools: …   # ADOS tool schema, not vendor-specific
```

Adapters translate tools/messages into OpenAI, Anthropic, Gemini, or Ollama shapes.

---

## Normalized Response (common envelope)

```text
ok:           true | false
capability:   chat
data:         { … capability-specific … }
error:        { code, message, retryable } | null
provider_meta:
  provider_id: provider.openai
  vendor_request_id: …
  latency_ms: …
  failover_count: …
```

### Error codes (stable)

`timeout` · `unavailable` · `quota_exceeded` · `auth_expired` · `auth_failed` · `invalid_request` · `unsupported` · `internal`

Failover reacts to retryable codes ([[FAILOVER_SYSTEM]]).

---

## Mapping responsibility

| Layer | Duty |
|-------|------|
| **ADOS caller** | Emit/consume normalized only |
| **Normalization schemas** | Canonical JSON/types per capability |
| **Provider adapter** | Bidirectional map vendor ↔ normalized |
| **Router** | Pass-through of normalized envelopes |

No vendor field names leak into CRM/ERP modules.

---

## Streaming normalization

Chunks:

```text
{ type: delta | status | error | done, data: … }
```

Terminal message carries full Normalized Response summary.

---

## Why this kills lock-in

- Swapping Claude for Ollama changes **adapter + registry**, not module code.  
- New vendor implements maps for the same schemas.  
- ADOS Core never imports vendor SDKs.

---

## Related

[[CAPABILITY_REGISTRY]] · [[PROVIDER_INTERFACE]] · [[SUPPORTED_PROVIDERS]]
