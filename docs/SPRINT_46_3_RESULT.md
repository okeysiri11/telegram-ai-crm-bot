# Sprint 46.3 RESULT — AI Concierge Chat UX + Real Task Response Flow

## Root cause («передал задачу → тишина»)

[`ContextualAiChat.tsx`](../src/web/src/owner-experience/ContextualAiChat.tsx) был demo Sprint 42.9:
`send()` → локальный `replyFor()` без API. Строка «Передал задачу Marketing AI через Консьержа» была **конечным** ответом; Hercules / Command Center не вызывались.

## Path (после фикса)

```
User → ContextualAiChat
  → classify QUESTION|CHAT|ACTION|WORKFLOW
  → CHAT/QUESTION: human local reply (без handoff)
  → ACTION/WORKFLOW: status «⏳ Выполняю…»
       → POST /management/v1/ai-command/chat (session_id)
       → AiCommandCenter → Planner → Hercules execute_plan
       → sanitize reply_ru → same chat bubble (result / clarify / error)
```

## Hercules

Да. Исполнение по-прежнему только через `hercules_runtime` в `platform_ai_command/executor/hercules_executor.py`.  
`reply_ru` для клиента — человеческий черновик результата; job ids / cost / steps остаются в meta ответа и в Owner «Подробнее».

## Conversation return

Синхронный HTTP: optimistic status → replace тем же message id результатом.  
`session_id` на открытие modal → `conversation_store` + `context_memory` сохраняют ход диалога.

## Modal UX

| Metric | Value |
|--------|--------|
| width | `min(900px, 90vw)` |
| height | `min(760px, 82vh)` |
| min | ~720×600 |
| messages | `overflow-y: auto`, `scrollbar-gutter: stable`, `padding-right: 18px` |
| AI bubble | max 78%, readable contrast |
| USER bubble | max 72%, right + margin |
| composer | fixed bottom, multiline, Enter send / Shift+Enter newline, 🎤 |

## Tests

- Vitest: `src/web/src/owner-experience/sprint_46_3_concierge_chat.test.ts`
- Pytest: clarify + human `_compose_reply` in `tests/test_ai_command_center_44_0.py`
- Regression: Sprint 42.9 `specialistForVertical` export preserved

## Manual smoke

1. Открыть «Поговорить с AI»
2. «Привет» → обычный ответ Консьержа
3. «Хочу рекламировать кафе» → название/город, **не** «Передал Marketing AI»
4. «Сделай рекламу кофейни в Одессе» → «⏳ Выполняю…» → результат в том же чате
5. Длинный текст / 20 сообщений → без horizontal overflow, composer на месте

## Architectural decisions

- Reuse AI Command Center + Hercules; no new WebSocket this sprint (sync status-in-flight UX).
- Soft marketing clarify uses `CLARIFY_MARKETING_RU`, not industry laundry-list, for short ads asks.
