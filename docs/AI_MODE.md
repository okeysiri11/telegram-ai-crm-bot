# AI Mode

**Epic:** 45.1 Dual Experience  
**Package:** `platform_modes`

## Purpose

AI становится главным интерфейсом. Пользователь может не открывать страницы.

## Pipeline (обязательный)

```
Запрос → AI Command Center → Planner → Agent OS → Hercules Runtime → Execution → Result
```

Прямой вызов агентов / провайдеров **запрещён**.

## Capabilities

- Планы и цепочки
- Запуск агентов через Hercules
- Документы, реклама, поиск данных, Workflow
- Подтверждение чувствительных действий
- Прогресс и стоимость (по настройкам)

## Indicator

`🟢 AI ACTIVE`

## Commands → AI

- `AI ON` · `Включи AI`
