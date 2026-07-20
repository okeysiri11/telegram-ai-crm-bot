# Platform Security Layer

> Sprint 5.1 — enterprise-grade authentication, authorization, secrets, and audit

## Overview

The Platform Security Layer provides **unified enterprise access control** across the entire platform — authentication, RBAC authorization, secret management, and comprehensive audit logging.

**Bridges to `platform_identity` without modifying Sprint 1–4.5 architecture.**

---

## Architecture

```mermaid
flowchart TB
    subgraph Security Layer
        SM[SecurityManager]
        AP[AuthenticationProvider]
        AM[AuthorizationManager]
        PM[PermissionManager]
        RM[RoleManager]
        SEC[SecretManager]
        SESS[SessionManager]
        AUD[AuditManager]
    end

    subgraph Auth Methods
        AK[API Keys]
        JWT[JWT]
        OA[OAuth]
        SA[Service Accounts]
        AN[Anonymous]
    end

    subgraph Integration
        IAM[platform_identity]
        WF[Workflow Engine]
        TF[Tool Framework]
        AR[Agent Registry]
        ME[Memory Engine]
        OR[Orchestrator]
    end

    SM --> AP --> Auth Methods
    SM --> AM --> PM --> RM
    SM --> SEC
    SM --> SESS
    SM --> AUD
    AP -.-> IAM
    AM -.-> IAM
```

---

## Core Components

| Component | Role |
|-----------|------|
| `SecurityManager` | Unified security entry point |
| `AuthenticationProvider` | API key, JWT, OAuth, service account, anonymous auth |
| `AuthorizationManager` | RBAC + access policy evaluation |
| `PermissionManager` | Capability, agent, tool, workflow, repository permissions |
| `RoleManager` | Role definitions, inheritance, custom roles |
| `SecretManager` | Encrypted secret storage & rotation |
| `SessionManager` | Session lifecycle (bridges platform_identity) |
| `AuditManager` | Authentication, authorization, tool, workflow, config audit |
| `AccessPolicy` | Configurable allow/deny policies |

---

## Authentication Methods

| Method | Description |
|--------|-------------|
| API Key | Bridge to `platform_identity.api_keys` |
| JWT | Access token verification via `jwt_service` |
| OAuth | Provider abstraction with registration interface |
| Service Account | Machine-to-machine credentials |
| Anonymous | Configurable read-only anonymous access |

---

## Roles

| Role | Access Level |
|------|-------------|
| Owner | Full platform access (`*`) |
| Administrator | System, workflow, tool, agent, audit admin |
| Developer | Read/write workflows, execute tools & agents |
| Operator | Execute workflows, tools, agents |
| Manager | Read + execute, audit read |
| Viewer | Read-only across resources |
| AI Agent | Execute agent, tool, capability, workflow |
| Service | Service automation permissions |
| Custom | User-defined via `register_custom_role()` |

---

## Permission Model

Permissions follow `{scope}.{action}` pattern:

| Scope | Examples |
|-------|----------|
| `capability` | `capability.read`, `capability.execute` |
| `agent` | `agent.read`, `agent.execute` |
| `tool` | `tool.read`, `tool.execute` |
| `workflow` | `workflow.read`, `workflow.write`, `workflow.execute` |
| `repository` | `repository.read`, `repository.write` |
| `system` | `system.*`, `audit.*`, `config.*` |

Wildcard permissions supported: `workflow.*`, `*`

---

## Secret Management

- Encrypted in-memory storage (XOR + SHA-256 derived key)
- Master key via `SecurityConfig.secret_master_key` (use `SecurityConfig.from_configuration()` in production)
- Secret rotation interface with version tracking
- Environment abstraction via `get_from_configuration()`
- Secure retrieval with authorization check

---

## Audit Events

| Event Type | Logged Actions |
|------------|----------------|
| Authentication | Login success/failure |
| Authorization | Permission grants/denials |
| Tool access | Tool execution attempts |
| Workflow access | Workflow execution attempts |
| Config change | Configuration modifications |
| Security | General security events |
| Secret access | Secret retrieval attempts |

Bridges to `platform_identity.audit_hooks` for IAM persistence.

---

## Usage

### Authenticate & authorize

```python
from platform_security import security_manager, SecurityRole

# JWT authentication
principal = await security_manager.authenticate(jwt_token="eyJ...")

# Service account
principal = await security_manager.authenticate(
    service_account_id="worker-1",
    service_credential="cred",
)

# Authorize
allowed = await security_manager.authorize(principal, "workflow.execute", resource="wf-123")
await security_manager.require(principal, "tool.execute")  # raises if denied
```

### Secrets

```python
record = security_manager.store_secret("db_password", "my-secret")
value = await security_manager.retrieve_secret("db_password", principal=principal)
security_manager.rotate_secret(record.secret_id, "new-secret")
```

### Custom roles & policies

```python
from platform_security import AccessPolicy

security_manager.register_custom_role("analyst", ["workflow.read", "audit.read"])

security_manager.register_policy(AccessPolicy(
    policy_id="deny-secrets",
    name="Deny Secret Access",
    roles=["viewer"],
    permissions=["config.*"],
    effect="deny",
    priority=100,
))
```

### Permission matrix

```python
matrix = security_manager.permission_matrix(["developer"])
# {"workflow.read": True, "workflow.write": True, "config.write": False, ...}
```

---

## Integration Bridges

| Layer | Method |
|-------|--------|
| Workflow | `check_workflow_access()` |
| Tools | `check_tool_access()` |
| Agents | `check_agent_access()`, `agent_permissions_from_registry()` |
| Orchestrator | `authorize_orchestrator_route()` |
| Memory | `protect_memory_access()` |
| Identity | `bridge_identity_authorize()` |

---

## Developer Guide

1. Authenticate requests via `security_manager.authenticate()` with appropriate credentials
2. Check permissions before executing workflows, tools, or agents
3. Store sensitive values in `SecretManager`, never in code
4. Configure `SecurityConfig.secret_master_key` for production secret encryption
5. Disable anonymous access in production environments
6. Review audit logs via `security_manager.audit_log()`
7. Register custom roles for vertical-specific access patterns

Package location: `platform_security/`

Tests: `tests/test_security_layer.py`
