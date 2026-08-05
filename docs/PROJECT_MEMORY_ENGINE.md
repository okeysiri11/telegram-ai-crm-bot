# Project Memory Engine — Sprint 36.5

## Architecture decision

**Canonical SoR:** `platform_memory` (existing AI memory / context SoR).  
**Rejected:** new `platform_project_memory` / `platform_core/` package (second memory engine forbidden).

Sprint 36.5 productizes an **Enterprise Project Memory Engine** *inside* `platform_memory/`:

| Layer | Module |
|-------|--------|
| Models | `project_memory_models.py` |
| Engine | `project_memory_engine.py` |
| Facade | `project_memory_service.py` |
| HTTP | `project_memory_router.py` |
| ORM | `database/models/project_memory.py` |
| Migration | `migrations/versions/o8i901234567_project_memory_engine_v1.py` |

```
AI Agent / AI Runtime / Workflow / Context Engine / Service Builder
                ↓
      ProjectMemoryService
                ↓
   remember → chunk → embed → search / link / session / feedback
                ↓
         DummyEmbeddingProvider (cosine similarity)
                ↓
         Enterprise Event Bus (memory.*)
```

---

## Memory Registry

Kinds: `project` · `agent` · `client` · `workflow` · `document`

## Semantic Search

- Embeddings via `DummyEmbeddingProvider` (pluggable `EmbeddingProvider`)
- Cosine similarity + keyword boost + importance
- Contextual retrieval for AI / Context Engine consumers

## Memory Layers

| Layer | Default TTL |
|-------|-------------|
| `short_term` | 1 hour |
| `working` | 24 hours |
| `long_term` | none |
| `shared_team` | none |

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/project-memory/*` | Primary product API |
| `/api/memory/*` | Alias |
| `/management/v1/project-memory/*` | Management dual-prefix |

### Key endpoints

- `POST /remember` · `GET /memories` · `GET|DELETE /memories/{id}`
- `POST|GET /search` · `POST /relations` · `GET /graph`
- `GET|POST /sessions` · `POST /sessions/{id}/pin`
- `GET /timeline` · `POST /feedback` · `GET /analytics`
- `POST /agents/{agent_id}/remember` · `GET /agents/{agent_id}/memories`
- `POST /integrations/ai-runtime|context-engine|workflow|service-builder`

## Database (Alembic `o8i901234567`)

`project_memory` · `memory_chunks` · `memory_embeddings` · `memory_relations` · `memory_sessions` · `memory_history` · `memory_feedback`

## UI

`/platform-builder/project-memory` (alias `/project-memory`)

Pages: Memory Dashboard · Search · Timeline · Relations Graph · Sessions · Analytics

## Integrations

| Consumer | Flag / hook |
|----------|-------------|
| AI Runtime | `use_project_memory` on complete |
| Context Engine | merges project memory into `for_ai_runtime` |
| Workflow Runtime | `use_project_memory` on execute |
| Event Bus | `memory.remembered` publish |
| Service Builder | `svc_project_memory` |

Every AI Agent can read/write via `/agents/{agent_id}/memories` and `/agents/{agent_id}/remember`.

## Success criteria

- Memory registry ✓
- Semantic search ✓
- Memory layers ✓
- REST + management dual-prefix ✓
- Alembic + ORM ✓
- UI console ✓
- Cross-runtime integrations ✓
