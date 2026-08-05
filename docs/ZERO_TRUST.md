# Zero Trust

**Sprint:** 32.4 · **Engine:** `platform_security.zero_trust.ZeroTrustEngine`

## Principles

1. Verify explicitly — never trust internal or external clients by default.
2. Least privilege — RBAC / ABAC / resource permissions.
3. Assume breach — continuous validation of identity, session, tenant, device.
4. Continuous validation — `evaluate_continuous` on every request context.

## Checks

Base: user · device · token · ip · context · risk_level · security_policy  

Continuous extras: authorization · tenant_isolation · session_integrity · trusted_device (optional)

## API

```python
from platform_security.security_center import enterprise_security_center

result = enterprise_security_center.verify_request({
    "user": "u1",
    "device": "d1",
    "token": "…",
    "ip": "10.0.0.1",
    "context": "api",
    "risk_level": 0.1,
    "security_policy": "default",
    "roles": ["operator"],
    "tenant_id": "t1",
    "require_tenant": True,
    "session_valid": True,
})
```

Denied requests emit Threat Timeline events and may open incidents.
