# Sprint 46.1 — Auto Telegram AI Manager

## What shipped

Auto Telegram stops being a forced questionnaire and becomes a conversation-first car AI manager:

- Natural language search with immediate execution  
- Request memory (refine without re-qualification)  
- Client vs staff output sanitizer  
- Tenant session helper (RU error, never raw English)  
- Dealer settings menu + owner AI controls  
- Russian First tariffs / rates / analytics labels  
- Localization gate + E2E dry-run tests  
- Docs under `docs/AUTO_*.md`

## Architectural decisions

1. **Extend `services/`** — no new `platform_auto_*` package; conversation/search memory live next to existing auto engines.  
2. **Demo inventory fallback** — E2E works without DB stock; CarEngine used when available.  
3. **Plan IDs unchanged** — only UI labels localized.  
4. **One lead per dialog** — `auto_request_memory.ensure_lead` on commercial intent.

## What shipped (Human Conversation)

- VIN text «Нет»/«2» no longer freezes FSM (`VIN_SKIPPED` → continue)
- Dialog State Manager + Human Conversation Policy + Quality Guard
- Budget refine «Можно до $17000»; diesel refine without re-qualification
- Leasing conversation path; Owner AI style defaults (concise)
- Docs: `docs/AUTO_HUMAN_CONVERSATION.md`


## Architectural decisions

1. Telegram channels that cannot be ingested safely stay `requires_configuration` and return empty — search continues.
2. Public web adapters use connector stubs when present, else deterministic catalog seeds for dry-run.
3. Priority affects ranking weights only, never exclusion of enabled sources.

## Quality gate

| Gate | Status |
|------|--------|
| Unit (slots/refine/cards) | `tests/test_auto_telegram_46_1.py` |
| Localization | `scan_user_facing_strings` |
| Telegram E2E dry-run | same test module |
| Manual Telegram smoke | required before production tag |

## Key files

- `services/auto_conversation_engine.py`  
- `services/auto_request_memory.py`  
- `services/auto_client_output.py`  
- `services/auto_dealer_settings.py`  
- `services/auto_telegram_tenant.py`  
- `services/auto_localization_gate.py`  
- `auto_vertical_handlers.py`  
- `keyboards.py` (`auto_dealer_settings_inline`, RU plan buttons)
