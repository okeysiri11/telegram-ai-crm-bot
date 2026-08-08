# Sprint 43.0 — Telegram AI Super App

**Дата:** 2026-08-07  
**Режим:** Enterprise Telegram Platform · Owner First · AI Studio · Provider Layer · Russian First  
**Область:** Telegram bot shell поверх существующих модулей (без ломки архитектуры)

## Цель

Сделать Telegram главным мобильным интерфейсом ADOS Enterprise: простой Owner-меню, AI Консьерж, AI Studio (image/video/voice/prompt + вертикальные AI), память диалога, очередь/история, workflow после генерации — **только через Provider Layer**.

## Архитектурные решения

| Решение | Почему | Отклонено |
|---------|--------|-----------|
| Пакет `services/telegram_ai_super_app/` + `routers/telegram_super_app_router.py` | Не расширять `handlers.py` (`docs/TELEGRAM_INTERACTION.md`) | Новый engine в handlers |
| `owner_main_menu` → Super App shell | Простое первое меню | Полный MENU_CATALOG на ReplyKeyboard |
| `SuperAppProviderFacade` → Creative Factory `MediaProviderManager` | Нет vendor SDK в Telegram | Прямой OpenAI/Runway из хендлеров |
| Developer Tools отдельным меню | Owner/Developer only | Инженерные кнопки на первом экране |
| In-process conversation + job queue | UX-слой; можно позже bridge на `platform_state` / `UserMemoryService` | Пятый memory stack |

## Главное меню (RU)

```
🤖 AI Консьерж · 📊 Дашборд
📋 Задачи · 🔔 Уведомления
🏢 Бизнес · 🎨 AI Studio
⚙ Настройки · 📂 Все разделы
(+ ⚙ Developer Tools — только Owner/Developer)
```

Инженерные модули (Platform Builder, Runtime, Context Engine, Event Bus, …) убраны с первого экрана.

## AI Консьерж

- Приветствие + примеры на русском
- NL → вертикаль / агент / workflow / modality / LLM hint
- Follow-up: «ещё 5 вариантов», «измени стиль», «создай видео из этого» без повторного брифа

## AI Studio

Image · Video · Voice · Reels · Реклама · Соцсети · Дизайн · Пост · Сценарий · Промпт · Beauty / Авто / Агро / Юр / Крипто маркетинг.

Диалоги брифа (размер/стиль/платформа/… → генерация).

## Provider Layer (подготовка)

| Модальность | Провайдеры (ids) |
|-------------|------------------|
| Image | openai_image, google_imagen, flux_image, stability_image, ideogram_image, recraft_image, bfl_image |
| Video | google_veo, runway_video, pika_video, kling_video, luma_video, hailuo_video |
| Voice | openai_voice, elevenlabs_voice, cartesia_voice, azure_speech, google_tts |
| Publish | instagram/facebook/tiktok/youtube/telegram/linkedin `*_publish` |

Исполнение — mock/failover Creative Factory (как и прежде); реальные ключи подключаются в hub без смены Telegram-логики.

## История · Очередь · Workflow

- История / избранное / повтор / дубликат / экспорт
- Очередь: ожидает · выполняется · готово · ошибка · % · AI · стоимость · время
- После генерации: видео → голос → реклама → публикация → план

## Файлы

- `services/telegram_ai_super_app/*`
- `routers/telegram_super_app_router.py`
- `keyboards.py` (упрощённое owner menu)
- `platform_registry/clients/telegram_adapter.py`
- `platform_registry/menus/__init__.py` (RU titles + Super App items)
- `platform_legacy/adapter.py`, `startup.py` (router first)
- `tests/test_telegram_ai_super_app_43_0.py`
- `docs/SPRINT_43_0_TELEGRAM_AI_SUPER_APP.md`

## Тесты

| Проверка | Статус |
|----------|--------|
| `pytest tests/test_telegram_ai_super_app_43_0.py` | ✓ 24 passed |
| Navigation / reply keyboard / localization / memory / studios / providers | ✓ unit |
| Registry smoke | ✓ |
| Production vendor live calls | deferred (Provider Layer stubs) |

## Как проверить в Telegram

1. `/menu` или старт Owner → новое главное меню  
2. 🤖 AI Консьерж → «Создай картинку»  
3. 🎨 AI Studio → 🖼 Изображение → пройти бриф → очередь/workflow  
4. 📂 Все разделы → Developer Tools (если Owner)  

## Deferred

- Live API keys for Veo/Flux/ElevenLabs (адаптеры hub)
- Persist conversation to Redis/`platform_state`
- Deep link legacy vertical handlers from Бизнес without RU shell

## Принцип

Telegram UI → Super App service → Provider Layer / Creative Factory.  
**Никогда** не подключать OpenAI/Google/Runway напрямую из Telegram-хендлеров.
