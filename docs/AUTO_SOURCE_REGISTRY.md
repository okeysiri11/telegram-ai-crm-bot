# Auto Source Registry

Sprint 46.1 — searchable inventory sources for Auto Telegram.

## Built-in sources

### A. Dealer / Telegram

| ID | Name | URL | Type | Enabled |
|----|------|-----|------|---------|
| `dealer_warehouse` | Моя база | internal | dealer_warehouse | yes |
| `tg_keepcar` | KEEP CAR | https://t.me/keepcar | telegram_channel | yes |
| `tg_isauto99` | IsAuto | https://t.me/isAuto99 | telegram_channel | yes |
| `tg_kievavto` | KIEVAVTO | https://t.me/KievavtoLocation | telegram_channel | yes |
| `tg_avtosale_odessa777` | avto_batya777 | https://t.me/avtosale_odessa777 | telegram_channel | yes |
| `tg_imperiya_auto` | Імперія Авто / Imperiya Auto | https://t.me/imperiya_auto | telegram_channel | yes |

Telegram channels that cannot be read automatically are marked `requires_configuration` and return **zero** listings — they never break the parallel search. All five share one `TelegramChannelAdapter`.

### B. Public web (always participate when enabled)

| ID | Name | URL |
|----|------|-----|
| `web_autoria` | AUTO.RIA | https://auto.ria.com |
| `web_olx_auto` | OLX Auto | olx.ua transport |
| `web_rst` | RST | https://rst.ua |

## Priority (ranking only)

1. Dealer warehouse  
2. Owner-configured Telegram channels  
3. Configured dealer sources  
4. AUTO.RIA / OLX / RST  
5. Other public web  

Priority **does not exclude** other enabled sources. Search runs in parallel.

## Modules

- `services/auto_source_registry.py` — registry + owner mutations  
- `services/auto_search_adapters.py` — per-type adapters  
- `services/auto_search_orchestrator.py` — fan-out / normalize / dedupe / rank  
- `services/auto_source_models.py` — listing schema  

Conversation engine calls the orchestrator only — no hardcoded source URLs.
