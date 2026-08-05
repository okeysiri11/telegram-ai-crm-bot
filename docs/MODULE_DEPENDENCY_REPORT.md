# Module Dependency Report — Sprint 37.4

## Canonical SoR engines

| Module | Package | Engine / Service | Router registrar |
|--------|---------|------------------|------------------|
| AI Runtime | `platform_ai` | `ai_runtime_engine` / `ai_runtime_service` | `register_ai_runtime_routes` |
| Creative | `platform_ai` | `creative_factory_engine` | `register_creative_factory_routes` |
| Voice | `platform_ai` | `voice_runtime_engine` | `register_voice_runtime_routes` |
| Multi-Agent | `platform_orchestrator` | `multi_agent_runtime_engine` | `register_multi_agent_runtime_routes` |
| City / Search | `platform_orchestrator` | `enterprise_city_runtime_engine` | `register_enterprise_city_runtime_routes` |
| Project Memory | `platform_memory` | `project_memory_engine` | `register_project_memory_routes` |
| Workflow | `platform_workflow` | `workflow_runtime` | `register_workflow_runtime_routes` |
| Event Bus façade | `platform_enterprise_event_bus` | `enterprise_event_bus` | `register_enterprise_event_bus_routes` |
| Event Bus SoR | `events.event_bus` | `PlatformEventBus` | (in-process) |
| Service Builder | `platform_service_builder` | router | `register_service_builder_routes` |
| Jobs | `platform_jobs` | unified queue / scheduler | `register_jobs_routes` |
| Config | `platform_configuration` | `configuration_center` | management config APIs |

## Dependency rules (verified)

```
API (create_app)
  → management_router (registers platform_* routers)
  → enterprise_hub + vertical applications
  → health / metrics

platform_workflow.runtime_engine
  → platform_enterprise_event_bus (bridge=True)
    → events.event_bus.PlatformEventBus (SoR)

platform_ai.runtime_engine
  → platform_security.ai_security_center
  → platform_ai.ai_service
```

## Import graph health

All canonical package exports import without circular failure. **Fix:** `from platform_ai import ai_runtime_engine` now works (37.4).

## Known parallel stacks (not broken — debt)

| Debt | Peers | Pri | Effort |
|------|-------|-----|--------|
| TD-E03 | Multiple EventBus | P1 | 5–8d |
| TD-E05 | Triple workflow engines | P2 | 5–8d |
| TD-E06 | Dual MemoryService | P2 | 3–5d |

## Verdict

**Module dependency graph: consistent for enterprise runtime surfaces.** Parallel stacks documented, not redesigned (out of scope).
