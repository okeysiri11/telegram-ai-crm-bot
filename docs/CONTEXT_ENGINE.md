# Enterprise Context Engine — Sprint 36.4

## Architecture decision

**Canonical SoR:** `platform_memory` (existing AI context engine).  
**Rejected:** new `platform_context` / `platform_core/` package (second engine forbidden).

Sprint 36.4 productizes an **Enterprise Context Engine** *inside* `platform_memory/`:

| Layer | Module |
|-------|--------|
| Memory assembler (existing) | `context_assembler.py`, `memory_service.py` |
| Context engine | `runtime_engine.py` |
| Sources | `context_sources.py` |
| Policies | `context_policies.py` |
| Facades / API | `service.py`, `router.py` |
| Models | `runtime_models.py` |

```
AI Runtime / Workflow / Service Builder
                ↓
      ContextEngineService
                ↓
   resolve → collect → filter → prioritize → merge → optimize → cache
                ↓
         ContextAssembler (optional enrichment)
```

---

## Capabilities

- **Sources** — User Profile, Organization, Project, Workspace, Documents, Knowledge Base, Workflow State, Conversation History, Agent Memory, Runtime Variables
- **Policies** — permissions, sensitivity, visibility, expiration, isolation, versioning
- **Token optimizer** — priority-ranked truncation under budget
- **Context cache** — keyed resolve bundles with TTL
- **Context graph** — session → source → fragment nodes/edges
- **Integrations** — `for_ai_runtime`, `for_workflow`, `for_service_builder` (+ opt-in flags on AI/Workflow execute)

---

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/context/*` | Primary product API |
| `/api/context-engine/*` | Alias |
| `/management/v1/context/*` | Management dual-prefix |

### Key endpoints

- `POST /resolve` · `GET /sources` · `GET|POST /graph`
- `GET|POST /sessions` · `GET /cache` · `POST /cache/clear`
- `GET /permissions` · `POST /permissions`
- `GET /statistics` · `GET /history` · `GET /embeddings`
- `POST /integrations/ai-runtime|workflow|service-builder`

---

## Database (Alembic `m6g789012345`)

`context_sessions` · `context_sources` · `context_cache` · `context_history` · `context_permissions` · `context_embeddings` · `context_statistics`

ORM: `database/models/context_engine.py`

---

## UI

`/platform-builder/context-engine` (alias `/context-engine`)

Pages: Context Explorer · Sources · Graph · Cache · Sessions · Statistics · Permissions

---

## Success criteria

- Context aggregation ✓
- Permission-aware filtering ✓
- Token optimization ✓
- Context caching ✓
- Context graph ✓
- AI Runtime integration ✓
- Workflow integration ✓
- Service Builder integration ✓
