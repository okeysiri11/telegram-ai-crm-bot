# Architecture — service layer and PostgreSQL-only production

## Target architecture

```mermaid
flowchart TB
    TG[Telegram UI / HTTP API]
    R[Routers / Handlers]
    S[Services Layer]
    REPO[Repositories]
    PG[(PostgreSQL)]

    TG --> R
    R --> S
    S --> REPO
    REPO --> PG
```

## Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Routers | `routers/`, `*_handlers.py` | Parse Telegram updates, render UI |
| Services | `services/*_service.py` | Business rules, orchestration |
| Repositories | `repositories/*_repository.py` | SQL only |
| Models | `database/models/` | ORM entities |
| Migrations | `migrations/` (Alembic) | Schema evolution |

## Production data policy

- **PostgreSQL** — единственный источник истины (`POSTGRES_ONLY=true` по умолчанию).
- **SQLite** (`memory.db`) — deprecated; критические функции перенаправлены в сервисы.
- **MemoryStorage** — только FSM-состояния aiogram (не users/requests/roles).

## Service layer

| Service | File | Role |
|---------|------|------|
| UserService | `services/user_service.py` | Users, profiles, verticals |
| RequestService | `services/request_service.py` | Unified requests (all verticals) |
| ManagerService | `services/manager_service.py` | Lead routing rules |
| RoleService | `services/role_service.py` | Permissions |
| NotificationService | `services/notification_service.py` | Manager/client alerts |
| MediaService | `services/media_service.py` | File storage |

## Manager routing rules

| Vertical | Auto-assignee | Notes |
|----------|---------------|-------|
| AUTO | Boroda_0003 | `DEFAULT_AUTO_MANAGER_ID` |
| AGRO | Christopher Moltisanti | grain, rapeseed, soy, freight, etc. |
| SUPER_ADMIN | Tony Soprano | Full access, **not** auto-assigned |

## Adding a vertical

1. Add enum/registry entry (`services/system_roles.py`, `src/verticals/`)
2. Extend `RequestService.SUPPORTED_VERTICALS`
3. Add `ManagerService.DEFAULT_ASSIGNEES` if needed
4. Create router under `routers/`
5. **Do not** modify core engines unless necessary

## Migration status

| Component | Status |
|-----------|--------|
| Auto client requests | PostgreSQL via `RequestService` / `AutoClientRequestEngineV1` |
| Agro buy flow (`handlers.py`) | PostgreSQL via `RequestService` |
| User ensure (`entry_point`, onboarding) | PostgreSQL via `UserService` |
| Legacy `handlers.py` admin/AI | Partial — still `from database import` (Phase 2) |

## Rollback

Set `POSTGRES_ONLY=false` in `.env` to re-enable SQLite fallbacks for unmigrated legacy functions.

See also: [services.md](services.md), [database.md](database.md), [verticals.md](verticals.md).

## Platform Memory Engine (Sprint 2.1–2.2)

```mermaid
flowchart TB
    MS[MemoryService]
    MSS[MemorySearchService]
    CA[ContextAssembler]
    MR[(MemoryRepository)]
    EP[EmbeddingProvider]

    MS --> MSS
    MS --> CA
    MSS --> MR
    MSS --> EP
    CA --> MSS
    CA --> MR
```

| Component | Path | Role |
|-----------|------|------|
| MemoryEntity | `platform_memory/entities.py` | Universal searchable memory object |
| MemoryRepository | `platform_memory/repositories/memory_repository.py` | Abstract persistence (no SQL in services) |
| InMemoryMemoryRepository | `platform_memory/repositories/in_memory_semantic_repository.py` | Default in-memory backend |
| DummyEmbeddingProvider | `platform_memory/providers/embedding_provider.py` | Deterministic embeddings (no OpenAI) |
| MemorySearchService | `platform_memory/search/memory_search_service.py` | Semantic + keyword search with ranking |
| ContextAssembler | `platform_memory/context_assembler.py` | LLM prompt context builder |

**Context priority:** current conversation → semantic memories → important memories → recent memories → summarized history.

**Future backends:** pgvector, Qdrant, Milvus, Weaviate — implement `MemoryRepository` + `EmbeddingProvider` without changing services.

Full details: [PLATFORM_MEMORY.md](architecture/PLATFORM_MEMORY.md), [SEMANTIC_MEMORY_REPORT.md](architecture/SEMANTIC_MEMORY_REPORT.md).

## Platform Multi-Agent Orchestrator (Sprint 2.3)

```mermaid
flowchart TB
    PO[PlatformOrchestrator]
    CR[CapabilityRouter]
    AR[AgentRegistry]
    MB[AgentMessageBus]
    AG[BaseAgent implementations]

    PO --> CR
    PO --> AR
    PO --> MB
    CR --> AR
    AR --> AG
```

| Component | Path | Role |
|-----------|------|------|
| BaseAgent | `platform_orchestrator/base_agent.py` | Abstract agent contract |
| AgentRegistry | `platform_orchestrator/agent_registry.py` | Agent discovery and lifecycle |
| CapabilityRouter | `platform_orchestrator/capability_routing.py` | Route by capability (not name) |
| PlatformOrchestrator | `platform_orchestrator/orchestrator.py` | Central execution engine |
| AgentMessageBus | `platform_orchestrator/message_bus.py` | Inter-agent messaging |
| Built-in agents | `platform_orchestrator/agents/builtin.py` | 8 vertical agent stubs |

**Routing:** capability-based (e.g. `buy_car` → Auto Agent, `legal_contract` → Legal Agent).

Full details: [ORCHESTRATOR.md](architecture/ORCHESTRATOR.md), [ORCHESTRATOR_REPORT.md](architecture/ORCHESTRATOR_REPORT.md).

## Platform Agent Registry (Sprint 3.1)

```mermaid
flowchart LR
    AR[AgentRegistry]
    PL[AgentPluginLoader]
    BA[BaseAgent]
    PP[platform_plugins/]

    AR --> BA
    PL --> AR
    PP --> PL
```

| Component | Path | Role |
|-----------|------|------|
| BaseAgent | `platform_agents/base_agent.py` | Agent contract |
| AgentRegistry | `platform_agents/registry.py` | Register, enable, discover |
| AgentPluginLoader | `platform_agents/plugin_loader.py` | Auto-discovery from `platform_plugins/` |
| Built-in agents | `platform_agents/agents/builtin.py` | 6 demonstration agents |

**Plugin drop-in:** add `platform_plugins/<name>/plugin.json` + `agent.py` — no core changes.

Full details: [AGENT_REGISTRY.md](../AGENT_REGISTRY.md).

## Platform Workflow & Task Engine (Sprint 3.2)

```mermaid
flowchart LR
    WE[WorkflowEngine]
    TQ[TaskQueue]
    AR[AgentRegistry]
    HA[HumanAssignment]

    WE --> TQ
    WE --> AR
    WE --> HA
```

| Component | Path | Role |
|-----------|------|------|
| WorkflowEngine | `platform_workflow/workflow_engine.py` | Create, execute, pause, cancel workflows |
| TaskQueue | `platform_workflow/task_queue.py` | Priority FIFO queue with retry/schedule |
| AgentAssignmentService | `platform_workflow/agent_assignment.py` | Route to agents by capability |
| HumanAssignmentService | `platform_workflow/human_assignment.py` | Assign to Manager/Admin/Operator/Owner |
| TelegramTaskInterface | `platform_workflow/telegram_interface.py` | Bot integration contract |

Full details: [WORKFLOW_ENGINE.md](../WORKFLOW_ENGINE.md).
