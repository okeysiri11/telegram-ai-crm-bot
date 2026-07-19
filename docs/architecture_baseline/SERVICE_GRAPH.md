# Service Graph — Architecture Baseline

> Generated: 2026-07-19 12:25:41 UTC

- **Service modules:** 487

## Service → downstream dependencies

### `events.adapters.crm_adapter`
- `events.event_bus` (services)
- `events.generic_events` (services)

### `events.adapters.legacy_adapter`
- `events.event_bus` (services)
- `events.generic_events` (services)
- `platform_legacy` (shared)

### `events.configuration_events`
- `events.base_event` (services)

### `events.crm_publisher`
- `services.crm_event_bus` (unknown)

### `events.event_bus`
- `events.base_event` (services)

### `events.generic_events`
- `events.base_event` (services)

### `events.handlers.audit_handler`
- `events.base_event` (services)

### `events.handlers.configuration_handler`
- `events.configuration_events` (services)
- `platform_configuration.config_provider` (services)
- `platform_sdk.workflow_loader` (services)

### `events.handlers.kpi_handler`
- `events.base_event` (services)
- `services.kpi_service` (unknown)

### `events.handlers.metrics_handler`
- `events.base_event` (services)
- `events.owner_events` (services)
- `events.request_events` (services)
- `services.kpi_service` (unknown)
- `services.platform_metrics_service` (unknown)

### `events.handlers.notification_handler`
- `events.base_event` (services)
- `events.request_events` (services)
- `services.notification_service` (unknown)

### `events.handlers.owner_notification_handler`
- `events.base_event` (services)
- `events.owner_events` (services)
- `services.owner_escalation_service` (unknown)

### `events.handlers.sla_handler`
- `events.base_event` (services)
- `events.request_events` (services)
- `platform_legacy` (shared)

### `events.manager_pool_events`
- `events.base_event` (services)

### `events.owner_events`
- `events.base_event` (services)

### `events.publisher`
- `events.base_event` (services)
- `events.crm_publisher` (services)
- `events.event_bus` (services)

### `events.request_events`
- `events.base_event` (services)

### `events.smart_assignment_events`
- `events.base_event` (services)

### `events.workflow_events`
- `events.base_event` (services)

### `platform_ai`
- `platform_ai.ai_service` (services)

### `platform_ai.ai_events`
- `events.base_event` (services)
- `events.publisher` (services)

### `platform_ai.ai_router`
- `platform_ai.ai_service` (services)
- `platform_ai.cache` (services)
- `platform_ai.cost_tracker` (services)
- `platform_ai.model_registry` (services)
- `platform_ai.models` (services)
- `platform_ai.prompt_service` (services)
- `platform_ai.provider_manager` (services)
- `platform_api.versioning` (shared)
- `platform_identity.identity_service` (services)
- `platform_management.management_context` (shared)
- `platform_management.permissions` (shared)
- `platform_management.response_models` (shared)

### `platform_ai.ai_service`
- `platform_ai.ai_events` (services)
- `platform_ai.cache` (services)
- `platform_ai.context_builder` (services)
- `platform_ai.conversation_manager` (services)
- `platform_ai.cost_tracker` (services)
- `platform_ai.exceptions` (services)
- `platform_ai.model_registry` (services)
- `platform_ai.models` (services)
- `platform_ai.prompt_service` (services)
- `platform_ai.provider_manager` (services)
- `platform_ai.provider_router` (services)
- `platform_ai.token_manager` (services)

### `platform_ai.cache`
- `platform_ai.models` (services)

### `platform_ai.context_builder`
- `platform_ai.conversation_manager` (services)
- `platform_ai.models` (services)
- `platform_configuration.config_provider` (services)
- `platform_management.statistics` (shared)
- `platform_sdk.workflow_loader` (services)

### `platform_ai.conversation_manager`
- `platform_ai.models` (services)

### `platform_ai.cost_tracker`
- `platform_ai.model_registry` (services)
- `platform_ai.models` (services)

### `platform_ai.memory`
- `platform_ai.memory.memory_service` (services)

### `platform_ai.memory.chunking`
- `platform_ai.memory.models` (services)

### `platform_ai.memory.document_store`
- `platform_ai.memory.exceptions` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.knowledge_base`
- `platform_ai.memory.chunking` (services)
- `platform_ai.memory.document_store` (services)
- `platform_ai.memory.knowledge_index` (services)
- `platform_ai.memory.knowledge_loader` (services)
- `platform_ai.memory.memory_embeddings` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.knowledge_index`
- `platform_ai.memory.models` (services)

### `platform_ai.memory.knowledge_loader`
- `platform_ai.memory.models` (services)

### `platform_ai.memory.knowledge_search`
- `platform_ai.memory.memory_retriever` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_context`
- `platform_ai.memory.memory_retriever` (services)
- `platform_ai.memory.memory_store` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_embeddings`
- `platform_ai.memory.exceptions` (services)

### `platform_ai.memory.memory_manager`
- `platform_ai.ai_service` (services)
- `platform_ai.memory.exceptions` (services)
- `platform_ai.memory.memory_registry` (services)
- `platform_ai.memory.memory_retriever` (services)
- `platform_ai.memory.memory_store` (services)
- `platform_ai.memory.models` (services)
- `platform_ai.models` (services)

### `platform_ai.memory.memory_ranker`
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_registry`
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_retriever`
- `platform_ai.memory.document_store` (services)
- `platform_ai.memory.knowledge_index` (services)
- `platform_ai.memory.memory_embeddings` (services)
- `platform_ai.memory.memory_ranker` (services)
- `platform_ai.memory.memory_store` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_service`
- `events.base_event` (services)
- `events.publisher` (services)
- `platform_ai.memory.document_store` (services)
- `platform_ai.memory.knowledge_base` (services)
- `platform_ai.memory.knowledge_index` (services)
- `platform_ai.memory.knowledge_search` (services)
- `platform_ai.memory.memory_context` (services)
- `platform_ai.memory.memory_embeddings` (services)
- `platform_ai.memory.memory_manager` (services)
- `platform_ai.memory.memory_registry` (services)
- `platform_ai.memory.memory_retriever` (services)
- `platform_ai.memory.memory_store` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory.memory_store`
- `platform_ai.memory.exceptions` (services)
- `platform_ai.memory.models` (services)

### `platform_ai.memory_router`
- `platform_ai.memory.memory_service` (services)
- `platform_ai.memory.models` (services)
- `platform_api.versioning` (shared)
- `platform_identity.identity_service` (services)
- `platform_management.management_context` (shared)
- `platform_management.permissions` (shared)
- `platform_management.response_models` (shared)

### `platform_ai.model_registry`
- `platform_ai.exceptions` (services)
- `platform_ai.models` (services)

### `platform_ai.prompt_service`
- `platform_ai.exceptions` (services)
- `platform_ai.models` (services)
- `platform_ai.prompt_templates` (services)

### `platform_ai.prompt_templates`
- `platform_ai.models` (services)

### `platform_ai.provider_base`
- `platform_ai.models` (services)

### `platform_ai.provider_manager`
- `platform_ai.exceptions` (services)
- `platform_ai.model_registry` (services)
- `platform_ai.models` (services)
- `platform_ai.provider_base` (services)
- `platform_ai.provider_registry` (services)

### `platform_ai.provider_registry`
- `platform_ai.exceptions` (services)
- `platform_ai.provider_base` (services)

### `platform_ai.provider_router`
- `platform_ai.exceptions` (services)
- `platform_ai.model_registry` (services)
- `platform_ai.models` (services)
- `platform_ai.provider_manager` (services)

### `platform_ai.response_parser`
- `platform_ai.provider_base` (services)

### `platform_ai.skills`
- `platform_ai.skills.skill_manager` (services)

### `platform_ai.skills.builtin`
- `platform_ai.models` (services)
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_base` (services)
- `platform_ai.skills.skill_context` (services)
- `platform_ai.skills.skill_registry` (services)

### `platform_ai.skills.skill_base`
- `platform_ai.models` (services)
- `platform_ai.provider_base` (services)
- `platform_ai.response_parser` (services)
- `platform_ai.skills.exceptions` (services)
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_context` (services)

### `platform_ai.skills.skill_cache`
- `platform_ai.skills.models` (services)

### `platform_ai.skills.skill_events`
- `events.base_event` (services)
- `events.publisher` (services)

### `platform_ai.skills.skill_executor`
- `platform_ai.ai_service` (services)
- `platform_ai.memory.memory_service` (services)
- `platform_ai.models` (services)
- `platform_ai.skills.exceptions` (services)
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_base` (services)
- `platform_ai.skills.skill_cache` (services)
- `platform_ai.skills.skill_context` (services)
- `platform_ai.skills.skill_events` (services)
- `platform_ai.skills.skill_metrics` (services)
- `platform_ai.skills.skill_registry` (services)

### `platform_ai.skills.skill_manager`
- `platform_ai.skills` (services)
- `platform_ai.skills.exceptions` (services)
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_base` (services)
- `platform_ai.skills.skill_cache` (services)
- `platform_ai.skills.skill_context` (services)
- `platform_ai.skills.skill_events` (services)
- `platform_ai.skills.skill_executor` (services)
- `platform_ai.skills.skill_metrics` (services)
- `platform_ai.skills.skill_permissions` (services)
- `platform_ai.skills.skill_registry` (services)

### `platform_ai.skills.skill_metrics`
- `platform_ai.skills.models` (services)

### `platform_ai.skills.skill_permissions`
- `platform_ai.skills.exceptions` (services)
- `platform_ai.skills.models` (services)

### `platform_ai.skills.skill_registry`
- `platform_ai.skills.exceptions` (services)
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_base` (services)

### `platform_ai.skills_router`
- `platform_ai.skills.models` (services)
- `platform_ai.skills.skill_manager` (services)
- `platform_api.versioning` (shared)
- `platform_identity.identity_service` (services)
- `platform_management.management_context` (shared)
- `platform_management.permissions` (shared)
- `platform_management.response_models` (shared)

### `platform_ai.workflows`
- `platform_ai.workflows.workflow_engine` (services)

### `platform_ai.workflows.models`
- `platform_workflows.models` (workflow)

### `platform_ai.workflows.workflow_builder`
- `platform_ai.workflows.models` (services)
- `platform_workflows.exceptions` (workflow)
- `platform_workflows.workflow_validator` (workflow)

### `platform_ai.workflows.workflow_cache`
- `platform_ai.workflows.models` (services)

### `platform_ai.workflows.workflow_engine`
- `platform_ai.workflows.models` (services)
- `platform_ai.workflows.workflow_cache` (services)
- `platform_ai.workflows.workflow_metrics` (services)
- `platform_workflows.workflow_engine` (workflow)
- `platform_workflows.workflow_executor` (workflow)

### `platform_ai.workflows.workflow_events`
- `events.base_event` (services)
- `events.publisher` (services)

### `platform_ai.workflows.workflow_executor`
- `platform_workflows.workflow_executor` (workflow)
