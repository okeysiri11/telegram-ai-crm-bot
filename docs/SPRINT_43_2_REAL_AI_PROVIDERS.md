# Sprint 43.2 — Real AI Providers, Multimodal Generation & Enterprise Connectors

**Дата:** 2026-08-07  
**Режим:** Production Integration · Provider Layer · Multimodal · Russian First  
**База:** Sprint 43.1 Unified AI Runtime Pipeline (без переписывания)

## Цель

Подключить реальные AI-провайдеры через единый Provider Manager.  
Live-режим при наличии ключа + `ADOS_AI_LIVE=1`; иначе production-контракт в sandbox с автоматическим fallback.

## Provider Manager

`platform_ai/providers/manager.py`

Каждый провайдер: ID · Название · Тип · API · Стоимость · Лимиты · Статус · key_ref · Fallback · Timeout · Retry · Health.

### Каталог

| Тип | Провайдеры |
|-----|------------|
| Image | OpenAI Images, Flux, Recraft, Ideogram, BFL, Stability, Fal.ai, Replicate |
| Video | Runway, Veo, Pika, Kling, Luma, Hailuo |
| Voice | ElevenLabs, Cartesia, Google Speech, Azure Speech, OpenAI Voice |
| Text | OpenAI, Anthropic, Gemini, DeepSeek, Mistral |

## API Keys (vault)

`platform_ai/providers/vault.py` → `platform_security.SecretManager`  
Имена: `ai.provider.<vendor>.api_key`  
Опциональный bootstrap из env (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …).

## Адаптеры

`platform_ai/providers/adapters.py`

- Live HTTP при ключе + `ADOS_AI_LIVE=1`
- Sandbox с cost metadata иначе
- Авто-failover по цепочке без участия пользователя

## Unified Pipeline (обновлён)

`UnifiedAiPipeline` v43.2 исполняет генерацию через **ProviderManager**, не через mock-only Creative Factory.

Результат содержит: `mode`, `cost_breakdown`, `tried`, `failover_used`.

## Multimodal Pipeline

`platform_ai/multimodal.py`

```
Prompt → LLM → Image → Video → Voice → Music → Subtitle → Publishing
```

## Telegram UX (43.2)

После генерации: Скачать · Повторить · Изменить · Избранное · Отправить · Видео · Озвучить · Reels · Реклама + стоимость/токены.

Beauty Studio: Instagram Post/Story, Reels, TikTok, До/После, Акция, Прайс, сертификат, баннер, голос, музыка, хештеги, контент-план, ответ клиенту.

Owner AI: лендинг, прибыль, CRM, продажи, КП, отчёт, реклама, презентация.

## Health & Analytics

- `provider_manager.health_check()` — API / ошибка / ключ / latency  
- `enterprise_analytics()` + Owner Dashboard (топ моделей, расход, ключи)

## Тесты

| Suite | Status |
|-------|--------|
| `tests/test_ai_providers_43_2.py` | ✓ |
| `tests/test_ai_runtime_pipeline_43_1.py` | ✓ |
| `tests/test_telegram_ai_super_app_43_0.py` | ✓ |

## Как включить live

1. Сохранить ключ: `provider_key_vault.store("openai", "sk-...")` или env `OPENAI_API_KEY`  
2. `export ADOS_AI_LIVE=1`  
3. Генерация из Telegram / `unified_ai_pipeline.run(...)`

## Deferred

- Полные vendor-specific request schemas для каждого endpoint  
- Postgres persistence ключей (сейчас encrypted in-memory SecretManager + env)  
- Web Provider Admin UI

## Принцип

Каналы (Telegram/Web) **никогда** не вызывают вендоров напрямую.  
Только `UnifiedAiPipeline` → `ProviderManager` → adapters.
