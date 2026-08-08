# Auto Telegram Sources

Telegram as both **channel** and **source**.

## Channel (delivery)

- Delivery of cards, compare, favorites, monitor alerts.
- Default `delivery_channel = telegram`.

## Telegram search pool (5)

| # | Name | URL | Region |
|---|------|-----|--------|
| 1 | KEEP CAR | https://t.me/keepcar | Ukraine |
| 2 | IsAuto | https://t.me/isAuto99 | Ukraine |
| 3 | KIEVAVTO | https://t.me/KievavtoLocation | Kyiv / Ukraine |
| 4 | avto_batya777 | https://t.me/avtosale_odessa777 | Odessa / Ukraine |
| 5 | Імперія Авто / Imperiya Auto | https://t.me/imperiya_auto | Ukraine |

All use the **same** `TelegramChannelAdapter` + `normalize_telegram_post` → `AutoSearchListing`.

Owner may add more via **Источники поиска → + Telegram-канал** (`add_telegram_channel`) without code changes.

Public web sources (AUTO.RIA / OLX / RST) always remain in the parallel fan-out when enabled.

## Ingestion rule

Only allowed Bot API / configured access / cached posts. If a channel cannot be read, mark `requires_configuration` / `unavailable` — do not fail the whole search.
