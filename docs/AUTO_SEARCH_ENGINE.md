# Auto Search Engine

Sprint 46.1 multi-source search pipeline.

## Flow

```
CLIENT QUERY
→ Auto Conversation Engine
→ Query Normalizer (slots)
→ Auto Search Orchestrator
→ parallel:
    A. DEALER / TELEGRAM SOURCES
    B. PUBLIC WEB SOURCES (AUTO.RIA, OLX, RST, …)
→ Normalize Listings
→ Deduplicate
→ Ranking (priority weights)
→ Result Cards
→ Telegram response
```

## Listing fields

`source`, `source_type`, `source_url`, `listing_url`, `external_id`,
`make`, `model`, `year`, `price`, `currency`, `mileage`, `fuel`,
`transmission`, `location`, `description`, `photos[]`,
`published_at`, `fetched_at`

## Modes

| Mode | Behavior |
|------|----------|
| `fast` | Parallel search, capped results |
| `deep` | Higher result cap across all enabled sources |
| `monitor` | Save query; notify on new matches |

## Owner UI

Настройки → Авто → Источники поиска  
Моя база · Telegram-каналы · Автосайты · Дополнительные источники  
[+ Telegram] [+ Web] [Вкл/Выкл] [Приоритет] [Проверить]
