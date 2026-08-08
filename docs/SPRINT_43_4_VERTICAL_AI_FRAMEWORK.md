# Sprint 43.4 — Vertical AI Framework + Beauty AI (First Vertical)

**Mode:** Enterprise Platform · Vertical AI Framework · AI Studio · Telegram First · Russian First  
**Date:** 2026-08-07  
**Status:** Done (builds on Sprint 43.1–43.3; no pipeline/provider rewrite)

---

## Goal

Единый **Vertical AI Framework**: отрасль = конфигурация.  
**Beauty AI** — первая полная вертикаль и эталон для Auto, Legal, Construction, Crypto OTC и остальных.

---

## Architecture

```
Vertical AI Framework (platform_vertical_ai)
        ↓
Vertical Configuration
        ↓
Templates · Agents · Knowledge · Prompt Library
        ↓
Vertical AI Studio / CRM / Analytics / Automations (inherited)
        ↓
UnifiedAiPipeline (Sprint 43.1–43.2 runtime)
        ↓
Telegram / Web / Desktop / Mobile channels
```

Все вертикали используют **один Runtime**. Новая вертикаль = `VerticalConfig` + `registry.register()`, без копирования кода.

---

## Framework-ready verticals

Beauty ✅ · Auto · Construction · Legal · Crypto OTC · Agro · Travel · Production · Manufacturing · Cafe · Medical · Real Estate · Education · Marketplace · Owner

Beauty: `complete=True`. Остальные — каркасы меню/агентов/wizard (готовы к наполнению конфигом).

---

## Beauty AI (эталон)

### Меню (Telegram)
💅 Создать пост · 🎥 Создать Reels · 📸 До / После · 🎨 Баннер · 📢 Акция · 🎁 Сертификат · 💲 Прайс · 📅 Контент-план · 💬 Ответ клиенту · 📱 История · ⭐ Избранное · ⚙ Настройки

### Мастер
Бизнес → Услуга → Цель → Аудитория → Площадка → превью цепочки → генерация / полная цепочка

### Цепочка
Промпт → Изображение → Видео → Озвучка → Музыка → Reels → Описание → Хэштеги → Публикация

### Агенты
- AI Копирайтер (Instagram, Telegram, TikTok, Facebook, Google Business, SEO, ответ клиенту)
- AI Дизайнер (баннер, постер, Story, Reels Cover, прайс, сертификат, визитка)
- AI Видео (Reels, TikTok, Shorts, реклама, видео процедуры)
- AI Голос (женский/мужской/премиум/клон)
- AI Маркетинг (акции, upsell, лояльность)

### Сценарии
Маникюр, Косметология, Парикмахер, Барбер, SPA, Массаж, Перманент, Лазер, сертификат, акция, До/После, новинка, видео процедуры

### Календарь
7 / 14 / 30 / 90 дней

---

## Inheritance (каждая вертикаль)

AI Chat · AI Studio · CRM · Документы · История · Избранное · Промпты · Автоматизации · Аналитика · Агенты · Контекст · Поиск · Уведомления · RBAC · Telegram · Web · Desktop · Mobile

---

## Files

| Path | Role |
|------|------|
| `platform_vertical_ai/models.py` | VerticalConfig DTOs |
| `platform_vertical_ai/registry.py` | VerticalRegistry |
| `platform_vertical_ai/framework.py` | VerticalAiFramework |
| `platform_vertical_ai/wizard.py` | Master + chain + calendar |
| `platform_vertical_ai/agents.py` | Copywriter / Designer / Video / Voice |
| `platform_vertical_ai/configs/beauty.py` | Beauty reference |
| `platform_vertical_ai/configs/skeleton.py` | Other industries |
| `services/telegram_ai_super_app/vertical_ux.py` | Telegram keyboards |
| `routers/telegram_super_app_router.py` | Beauty vertical FSM |
| `tests/test_vertical_ai_framework_43_4.py` | Framework + Beauty tests |

---

## Architectural decisions

1. **New package `platform_vertical_ai/`** — SoR отраслевых AI-конфигов; не смешивать с CRM `platform_sdk.verticals` и ops `platform_beauty_os`.
2. **Config over code** — новая вертикаль без копирования handlers/agents.
3. **Shared runtime** — только `UnifiedAiPipeline`; Framework не вызывает вендоров.
4. **Beauty as reference** — полное меню + wizard + agents; остальные — skeleton configs.

Rejected: дублировать Beauty handlers per industry inside Telegram service.

---

## Tests

```bash
.venv/bin/python -m pytest \
  tests/test_vertical_ai_framework_43_4.py \
  tests/test_ai_studio_production_ux_43_3.py \
  tests/test_telegram_ai_super_app_43_0.py \
  tests/test_ai_runtime_pipeline_43_1.py \
  tests/test_ai_providers_43_2.py -q --tb=short
```

---

## Result

После Sprint 43.4 в платформе есть Vertical AI Framework. Beauty AI — первая рабочая вертикаль в Telegram. Следующие отрасли подключаются конфигурацией Framework.
