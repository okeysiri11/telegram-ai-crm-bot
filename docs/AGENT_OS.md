# AgentOS

**Sprint:** 32.1 (Enterprise Multi-Agent OS track)  
**SoR:** Enterprise Runtime (`aiAgentRuntime` + `jobManager` + `agentOs` facade)  
**Hard rule:** No isolated agents. No second orchestrator. n8n = external only.

## Naming collision

Sprint **32.1** is also **External Pilot Hardening** (`SPRINT_REPORT_32_1.md`).  
This document covers the **AgentOS** track only.

## Architecture

```
Agent Center / Owner / Production Studio
        ↓
     agentOs facade
        ↓
 aiAgentRuntime · DEFAULT_AGENTS · jobManager · productionRuntime
        ↓
     APH (model calls) · n8n (external callbacks only)
```

## Surfaces

| Concern | Module |
|---|---|
| Registry | `defaultAgents.ts` + `agentOs.registry()` |
| Lifecycle | `aiAgentRuntime.setPhase` / launch/pause/resume/complete/fail/cancel/retry |
| Communication | `agentOs.sendMessage` / inbox |
| Memory | `agentOs.remember` / recall / sharedContext |
| Observability | `agentOs.observe` + `AgentOsMonitor` |
| Collab | `agentOs.runCollaborative` |

## Related

`AGENT_RUNTIME.md`, `AGENT_REGISTRY.md`, `AGENT_COMMUNICATION.md`, `AGENT_MEMORY.md`, `AGENT_SECURITY.md`, `SPRINT_32_1_RESULT.md`
