---
title: ADOS Provider Security
aliases:
  - Provider Security
tags:
  - providers
  - upp
  - security
status: foundation
---

# ADOS Provider Security

## Purpose

Describe how UPP handles **credentials, encryption, scopes, and audit** so external integrations do not leak secrets into modules, Core, or knowledge docs.

UPP: [[UNIVERSAL_PROVIDER_PLATFORM]] · Interface: [[PROVIDER_INTERFACE]] · Workforce Security: [[../workforce/ORGANIZATION_CHART|ORGANIZATION_CHART]]

---

## Controls

### API Keys

- Stored in secret storage; referenced by handle in `configuration()`.  
- Injected at `initialize()` / `authenticate()` only inside provider process.  
- Rotation supported without Core changes—update secret, re-auth.

### OAuth

- Authorization code / client credentials as appropriate.  
- Tokens in secret storage; refresh via `authenticate()`.  
- Redirect/webhook endpoints are provider-edge only.

### Service Accounts

- Preferred for server-to-server (Google, Microsoft, cloud).  
- Least-privilege roles; separate accounts per environment.

### Encryption

- Secrets encrypted at rest (platform KMS/vault).  
- TLS in transit to external services.  
- Normalized payloads avoid unnecessary PII; redact in logs.

### Secret Storage

- Vault / OS secret manager / env of host—never git, never Obsidian vault commits, never module source.  
- Provider Registry stores **references**, not key material.

### Permission Scopes

- Map tenant/user roles to provider scopes (e.g. repo read vs write).  
- Capability **payments** / medical data → elevated Security class; Security Lead review.  
- Router may deny provider selection when scopes insufficient.

### Audit Logging

- Log: who (actor), what capability, which Provider ID, Package-ID, result code, latency.  
- Do **not** log tokens, raw keys, or full regulated payloads.  
- Security-relevant failures (`auth_failed`) alert Owner + Security Lead path.

---

## Security rules for adapters

1. No business authorization reinvented differently from ADOS security context—**enforce** context.  
2. No cross-tenant credential reuse.  
3. Webhook signatures verified in provider before `events()` fan-in.  
4. Provider replacement drains sessions; revoke where vendor supports.

---

## Failure handling

| Event | Security action |
|-------|-----------------|
| auth_expired | Refresh; audit |
| auth_failed | Stop; alert; no blind failover to another identity | 
| Secret missing | Fail initialize; Status failed |

---

## Related

[[FAILOVER_SYSTEM]] · [[PROVIDER_MANAGER]] · [[../ados_os/EVENT_BUS|EVENT_BUS]] · [[../execution/DECISION_ENGINE|DECISION_ENGINE]]
