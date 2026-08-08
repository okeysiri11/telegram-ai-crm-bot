# Chat Architecture — AI Command Center

## Capabilities

Текст · голос · изображения · документы · PDF · Word · Excel · архивы · скриншоты · код · ссылки

## Flow

1. `CommandMessage` (+ attachments)
2. Context enrichment (`context_memory`)
3. `route_command` → `build_plan`
4. `execute_plan` → Hercules only
5. Conversation + History store

## UI

ChatGPT-style panel on `/ai-command` with quick commands and tabs.
