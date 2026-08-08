# Auto Search Ranking

## Defaults

1. Within budget
2. Fuel / year filters applied
3. Prefer newer year when tied
4. Cap by `max_results` (fast mode lower)

## Owner controls

- `ranking_rules` (e.g. `price_asc`, `year_desc`)
- `preferred_dealers`
- `preferred_sources` / `excluded_sources`
- `max_results`

Ranking metadata (scores) is **internal** — never shown on client Telegram cards.
