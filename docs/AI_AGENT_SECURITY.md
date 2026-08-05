# AI Agent Security

**Sprint:** 32.4 · Extends [`AGENT_SECURITY.md`](./AGENT_SECURITY.md) / [`AI_SECURITY.md`](./AI_SECURITY.md)

## Controls

| Control | Owner |
|---|---|
| AI Agent Identity | AgentOS registry + External AI Guard certificates (`agc_*`) |
| Permission profiles | `AiSecurityCenter.agent_permission_profile` |
| Execution policies | `authorize_agent_execution` (+ human approval) |
| Sandboxing / runtime isolation | Enterprise Runtime + External AI Guard runtime allowlist |
| Tool access control | Agent permissions + External AI Guard |
| Reject unknown runtimes | `ExternalAiGuard.verify_ai_client` |
| Prevent unauthorized autonomous agents | `authorize_autonomous_agent(registered=True)` |

## Related

[`SECURITY_CENTER.md`](./SECURITY_CENTER.md) · [`PROMPT_FIREWALL.md`](./PROMPT_FIREWALL.md)
