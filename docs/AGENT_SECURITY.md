# Agent Security

**Sprint:** 32.1

## Controls

| Control | Owner |
|---|---|
| Agent permissions | `DEFAULT_AGENTS.permissions` + task RBAC (`aiTaskSecurity`) |
| Tenant isolation | `tenantId` on agents / memory / messages |
| Prompt Firewall | `aiPromptSecurity` / APH firewall |
| Rate limits | `platform_integrations.rate_limiter` + job queue |
| Secrets isolation | ESH vault refs — never inline keys |
| Audit trail | `agentOs.auditTrail` |

Owner can force-stop / restart via `OwnerAiDashboard` + AgentOS monitor.

**Sprint 32.4:** Agent sandboxing / certificates / unknown-runtime rejection — see [`AI_AGENT_SECURITY.md`](./AI_AGENT_SECURITY.md) and `ExternalAiGuard`.
