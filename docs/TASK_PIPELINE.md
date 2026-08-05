# Task Pipeline

**Sprint:** 30.5  
**File:** `src/web/src/ai-runtime/taskPipeline.ts`

## Stages

| Stage | RU |
|-------|-----|
| Waiting | Ожидание |
| Preparing | Подготовка |
| Running | Выполнение |
| Review | Проверка |
| Completed | Завершено |
| Failed | Ошибка |

Mapped from `JobLifecycle` + progress via `stageFromLifecycle`.

Creative Production pipelines remain: Draft → Archive (`productionCatalog.PIPELINE_STAGES`).
