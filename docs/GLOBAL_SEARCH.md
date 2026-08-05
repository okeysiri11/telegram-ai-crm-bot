# Global Search — Sprint 30.2

**Index:** `navigation/managers/searchIndex.ts`  
**Provider:** `searchProvider`  
**UI:** Top bar input → Command Palette (`⌘K`) · `/search` workspace

## Categories (Russian labels)

Клиенты · Проекты · Документы · AI-Агенты · Знания · Задачи (+ модули, команды, панели)

Map: `SEARCH_CATEGORY_RU` in `enterpriseRuNav.ts`.

## Indexed quick commands

- Создать клиента
- Создать проект
- Создать документ
- Запустить AI
- Открыть карту
- Создать задачу

Russian tokens are included so queries like «клиент» / «проект» / «карта» resolve.
