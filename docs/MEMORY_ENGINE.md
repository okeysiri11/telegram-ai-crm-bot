# Memory Engine (Continuous Memory)

**Epic:** 45.2 · **Version:** 45.2.0  
**Package:** `platform_memory/` (extended — no new top-level package)

## Levels

| Level | Name | Module |
|-------|------|--------|
| 1 | Session Memory | `conversation_memory.py` |
| 2 | Working Memory | `working_memory.py` |
| 3 | Project Memory | working + existing Project Memory Engine |
| 4 | Long Term Memory | `long_term_memory.py` |
| 5 | Knowledge Memory | `memory_embeddings.py` + `memory_search.py` |

## Façade

`memory_manager.py` — save / search / context / timeline / resume / summary / project / pin / remove / workspace / recall / `run_with_memory`.

## Pipeline

```
Prompt → Context Engine 2.0 → (Mode Manager) → AI Command Center → Hercules
```

## Cross-platform

Telegram · Web · Desktop · Voice share `continuity_store`.
