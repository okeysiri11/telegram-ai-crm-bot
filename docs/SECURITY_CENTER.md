# Enterprise Security Center

**Sprint:** 32.4 (Zero Trust Platform track)  
**Collision:** Historical Sprint **32.4** = AI Operating System Experience (`AI_OS_EXPERIENCE_32_4.md`) — preserved.  
**SoR:** `platform_security.security_center.EnterpriseSecurityCenter`

## Principle

Security is a **platform-wide** capability. Vertical modules must **not** implement parallel security engines. They call Security Center / ISAM / middleware / prompt firewall.

## Surfaces

| Surface | Module |
|---|---|
| Security Dashboard / Health / Risk / Timeline | `EnterpriseSecurityCenter.dashboard()` |
| Incident Center | `incident_center.IncidentCenter` |
| Audit Center | `audit_center.AuditCenter` |
| Zero Trust | `zero_trust.ZeroTrustEngine` |
| AI Security | `ai_security_center.AiSecurityCenter` → APH `prompt_firewall` |
| Anti-parsing | `anti_parsing.AntiParsingProtection` |
| External AI guard | `external_ai_guard.ExternalAiGuard` |
| API policy | `api_gateway_policy.ApiGatewayPolicy` → `middleware/security_middleware` |
| Knowledge security | `knowledge_security.KnowledgeSecurity` |
| Authorization | `authorization_center` + `permission_engine` + ISAM |
| Identity | ISAM (`applications/enterprise_hub/security`) |
| Secrets | `secret_policy` + ESH `SecretsManager` + `jwt_secrets` |
| Owner UI | `src/web/auth/pages/SecurityCenterPage.tsx` |

## Zero Trust

Every request context is verified via `verify_request` / `evaluate_continuous`. See [`ZERO_TRUST.md`](./ZERO_TRUST.md).

## Related docs

[`ZERO_TRUST.md`](./ZERO_TRUST.md) · [`AI_SECURITY.md`](./AI_SECURITY.md) · [`AI_AGENT_SECURITY.md`](./AI_AGENT_SECURITY.md) · [`ANTI_PARSING.md`](./ANTI_PARSING.md) · [`API_SECURITY.md`](./API_SECURITY.md) · [`KNOWLEDGE_SECURITY.md`](./KNOWLEDGE_SECURITY.md) · [`PROMPT_FIREWALL.md`](./PROMPT_FIREWALL.md) · [`AUDIT_CENTER.md`](./AUDIT_CENTER.md) · [`INCIDENT_RESPONSE.md`](./INCIDENT_RESPONSE.md) · [`SECURITY_MODEL.md`](./SECURITY_MODEL.md)
