# Sprint 43.1 — Unified AI Runtime Pipeline + Telegram AI Studio

**Дата:** 2026-08-07  
**Режим:** Enterprise Architecture · Unified AI Runtime · Queue · Provider Layer · Russian First  
**Область:** `platform_ai` (SoR) + Telegram channel façade (без переписывания Sprint 43.0)

## Цель

Единый AI Runtime Pipeline для любой генерации (изображение, видео, голос, текст, документ, презентация, реклама).  
Источник (Telegram / Web / Desktop / Mobile / REST / Automation / Workflow) не меняет архитектуру.

## Конвейер

```
Create → Validate → Choose Provider → Reserve Credits → Queue →
Execute → Progress → Store Result → History → Notify → Cache → Analytics
```

Реализация: `platform_ai/pipeline.py` → `UnifiedAiPipeline`.

## Статусы очереди (RU)

создана · в_очереди · подготавливается · генерируется · обрабатывается · готово · ошибка · отменена · повтор

## Job card

UUID · Owner · Provider · стоимость · время · тип · источник · история · метаданные · platform_job_id (`platform_jobs.UnifiedQueueArchitecture`)

## Provider Layer

Каталог ids (без хардкода вендоров в каналах):

- Image: OpenAI, Imagen, Flux, Recraft, Ideogram, BFL, Stability  
- Video: Veo, Runway, Pika, Luma, Kling, Hailuo  
- Voice: OpenAI, ElevenLabs, Cartesia, Azure, Google TTS  
- Text: OpenAI, Anthropic, Gemini, OpenRouter  

Исполнение — `CreativeFactoryEngine.MediaProviderManager` (как и прежде).

## Prompt Engine

`platform_ai/prompt_engine.py` — идея → оптимизированный промпт (фото, видео, реклама, beauty, авто, юр, crypto, agro, ERP, CRM).

## Telegram AI Studio (43.1 меню)

Изображения · Видео · Голос · Промпты · Реклама · Reels · Дизайн · Документы · Презентации · История · Избранное · Студия красоты  

Генерации идут только через `UnifiedAiPipeline` (`TelegramAiSuperApp` v43.1).

## Beauty Creative Studio

Полный продуктовый набор (Instagram, TikTok, Stories, Reels, прайсы, акции, до/после, контент-план, календарь, хештеги, сценарии, …).

## History · Cache · Analytics · Owner Dashboard

- Центр истории: поиск / фильтр / избранное / повтор / дубликат / экспорт / удалить  
- Кэш одинаковых генераций  
- Аналитика: объём, стоимость, время, модели, ошибки, нагрузка  
- Дашборд владельца в Telegram «📊 Дашборд»

## Developer

Меню `⚙ Developer` (только Owner) — полностью на русском: конструктор платформы, runtime, context, event bus, memory, skills, health, security, консоль разработчика.

## Архитектурные решения

| Решение | Почему | Отклонено |
|---------|--------|-----------|
| Pipeline в `platform_ai` | Единый SoR для всех клиентов | Новый `platform_ai_runtime` пакет |
| Очередь через `platform_jobs.unified_queue` | Уже есть lanes AI/RENDER | Четвёртая in-process очередь |
| Telegram = façade | Не дублировать логику | Отдельный Telegram-only engine |
| Legacy `job_queue.py` shim | Совместимость 43.0 | Удаление без миграции |

## Тесты

| Suite | Result |
|-------|--------|
| `tests/test_ai_runtime_pipeline_43_1.py` | ✓ |
| `tests/test_telegram_ai_super_app_43_0.py` | ✓ (адаптирован) |

## Файлы

- `platform_ai/pipeline.py`, `pipeline_models.py`, `pipeline_cache.py`, `pipeline_analytics.py`, `prompt_engine.py`
- `services/telegram_ai_super_app/service.py` (v43.1)
- `services/telegram_ai_super_app/catalog.py`, `studios.py`, `keyboards.py`, `job_queue.py` (shim)
- `routers/telegram_super_app_router.py`
- `docs/SPRINT_43_1_UNIFIED_AI_RUNTIME_PIPELINE.md`

## Deferred

- Live vendor credentials in Provider Hub  
- Persist pipeline tasks to Postgres (`AIRuntimeSessionRow` / creative assets)  
- Web REST thin wrapper calling `unified_ai_pipeline.run` (same contract)

## Принцип

**Любой канал → UnifiedAiPipeline → Provider Layer.**  
Дублирующей логики генерации между Telegram и Web быть не должно.
