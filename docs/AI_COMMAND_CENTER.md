# AI Command Center — Epic 44.0

Единая точка взаимодействия пользователя с ADOS: текст, голос, файлы, Desktop, Telegram, Web.

## Pipeline

```
User (Desktop / Telegram / Voice / Web)
        ↓
AI Command Center (route → plan → permissions → context)
        ↓
Hercules Runtime
        ↓
Provider Manager / Unified AI Pipeline
        ↓
Result + History
```

**Запрещён обход Hercules.**

## Package

`platform_ai_command/` — core, chat, voice, router, planner, executor, conversation, memory, tools, permissions, history, telegram, api.

## UI

- Web: `/ai-command`
- Telegram: 🧠 AI Command + меню чат/голос/медиа/вертикали
