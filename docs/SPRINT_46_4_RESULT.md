# Sprint 46.4 RESULT — Unified Intent Bar + Task Inbox + Human-First UX

## Goal

Одна универсальная строка **«Что хотите сделать?»** вместо разрозненных Search / Omnibox / AI input.
Пользователь пишет или говорит задачу — система сама определяет intent.
После submit текст **всегда** исчезает из input.

## Architecture

UX orchestration only — без нового execution runtime.

```
User Input (UnifiedIntentBar)
  → classifyUnifiedIntent (CHAT | SEARCH | COMMAND | CREATE | NAVIGATE | WORKFLOW)
  → executeUnifiedIntent
       → CHAT capability → CAPABILITY_REPLY_RU (локально)
       → CHAT other / CREATE / COMMAND / WORKFLOW → POST /management/v1/ai-command/chat
       → NAVIGATE → commandRuntime / catalog routes
       → SEARCH → searchProvider + /search?q=… (+ Continuous Memory refine)
  → Task Inbox (zustand + localStorage)
```

## UnifiedIntentBar

| Свойство | Значение |
|----------|----------|
| Title | Что хотите сделать? |
| Placeholder | Напишите или скажите задачу… |
| Clear on submit | Да, синхронно до `await execute` |
| Refocus | Да |
| Enter / Shift+Enter | submit / newline |
| Esc | clear draft |
| Voice (Human) | preview → Отправить / Изменить / Отмена |
| Voice (AI/Voice mode) | auto-send |
| History | последние 3–5 + кнопка «История» |
| Context | `Контекст: {vertical}` из config |

Файлы: `src/web/src/workspace-chrome/unified-intent/`

## Wiring (один компонент)

| Surface | Было | Стало |
|---------|------|-------|
| TopNavigation | Input → palette on focus | compact `UnifiedIntentBar` |
| VerticalDashboard | декоративный Input | `UnifiedIntentBar` + vertical config |
| HumanAiCommandBar (Auto) | локальный propose без clear UX | обёртка над `UnifiedIntentBar` |
| SearchWorkspacePage | «Модули» + группы | human results «Нашёл N» + категории |

## Intent examples

| Input | Intent |
|-------|--------|
| Расскажи, как ты можешь помочь | CHAT → capability reply (не search groups) |
| Открой CRM | NAVIGATE |
| Найди договор GlobeFly | SEARCH |
| Создай клиента Иванов | CREATE → ACC |
| Запусти рекламную кампанию | WORKFLOW → ACC |
| Только дизель (после SEARCH) | SEARCH refine (Continuous Memory) |

## Task Inbox

Кнопка «История» / «Действия»: фильтры Все · Выполняются · Готово · Ошибки.
Статусы RU: Принято / Выполняю / Нужно уточнение / Готово / Ошибка / Отменено.
Toggle «Показать технические данные» — default **OFF**.

## Command Palette

Остаётся power-user (⌘/Ctrl+K).
Вкладки RU: Быстрый доступ / Поиск / Команды / AI.
Скрыты score / `type:` / raw `open_module` в обычных meta.

## Removed / hidden from normal UX

- Header search that only opened palette and left users confused
- Empty «Модули» dump on Search Workspace for AI questions
- Omnibox score / `type: title` labels in palette
- Technical path/score under results (behind Owner toggle)

## Tests

```bash
cd src/web && npm run test -- --run src/workspace-chrome/unified-intent/sprint_46_4_unified_intent.test.ts
```

Acceptance covered in Vitest:

1. Capability → CHAT, no tech labels  
2. NAVIGATE / SEARCH / CREATE / WORKFLOW classification  
3. Vertical configs Auto/CRM/Travel/Beauty/Crypto/Agro  
4. Concurrent tasks visible  
5. Clear-on-submit + capability execute path  

## Architectural decisions

1. **Extend `workspace-chrome`**, не новый `platform_*` — это UX chrome над ACC / search / commandRuntime.
2. **Не дублировать input** по вертикалям — `VERTICAL_INTENT_CONFIGS` + один `UnifiedIntentBar`.
3. **Palette не удалять** — optional power tool; главный UX = Intent Bar.
4. **Continuous Memory** на клиенте: refine предыдущего SEARCH («Только дизель»), без нового memory engine.

## Manual smoke

1. Header: ввести «Расскажи как ты можешь помочь» → input пустой → история + ответ AI  
2. «Открой CRM» → переход, input пустой  
3. «Найди договор» → «Нашёл N», кликабельные результаты, без огромного «Модули»  
4. Voice (Human): preview → Отправить → preview закрыт, input пустой  
5. Две задачи подряд пока первая running → обе в истории  
6. Auto / CRM / Travel / Beauty dashboard — одна и та же строка  

## Done criteria

- [x] одна универсальная строка  
- [x] текст очищается после submit  
- [x] следующую задачу можно вводить сразу  
- [x] запрос в истории + status  
- [x] AI/Search/Command auto  
- [x] Palette optional  
- [x] debug metadata hidden (toggle)  
- [x] verticals config-driven  
- [x] voice + Continuous Memory refine  
- [x] Russian First  
- [x] tests PASS  
