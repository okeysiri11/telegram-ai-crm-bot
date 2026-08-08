# Hercules Runtime

## Entry

```python
from platform_hercules import hercules_runtime
from platform_hercules.core.models import ExecutionContext

job = await hercules_runtime.submit_ai(
    ExecutionContext(owner_id="owner-1", channel="telegram", vertical="beauty"),
    prompt="Создай пост для салона",
    modality="text",
)
print(hercules_runtime.status(job.id))
```

## Lifecycle (RU)

создана → в_очереди → выполняется → успех | ошибка | повтор | отменена

## SessionRuntime

```python
session = hercules_runtime.session("s1", "owner-1")
job = await session.run_ai("Анализ продаж", modality="text")
```

## Dashboard

`hercules_runtime.dashboard()` — version, health, GPU/CPU, queues, workers, metrics, jobs.

## Integration

Prefer `platform_hercules.integration.run_via_hercules(domain, ...)` from CRM/ERP/Studio façades.
AI generation still executes through `UnifiedAiPipeline` inside TaskExecutor.
