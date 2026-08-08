# Human Mode

**Epic:** 45.1 Dual Experience  
**Package:** `platform_modes`

## Purpose

Классический CRM / ERP / Studio опыт. Пользователь управляет вручную. AI не навязывается.

## Behavior

- Обычные страницы, кнопки, формы, меню, документы, CRM, ERP, AI Studio, Telegram
- AI отвечает **только** после прямого обращения
- Агенты **не** запускаются автоматически
- Самостоятельные действия AI запрещены
- Индикатор: `⚪ HUMAN MODE`

## Gate

`ModeManager.gate_ai_action` в Human Mode разрешает только `answer` / `reply` / `chat`.  
Выполнение идёт через AI Command Center с `max_steps=1` (без длинных цепочек).

## Commands → Human

- `AI OFF` · `VOICE OFF` · `HUMAN MODE`
- `Работаем вручную` · `Выключи AI` · `Остановись` · `Стоп` · `Отключись`
