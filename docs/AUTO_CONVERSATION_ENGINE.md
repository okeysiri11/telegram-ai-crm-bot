# Auto Conversation Engine

Sprint 46.1 — conversation-first automotive AI manager for Telegram.

## Purpose

Replace forced questionnaires with natural dialogue:

1. User speaks in free form (`BMW X5 Одесса до $15000`).
2. Engine extracts slots and **starts search immediately**.
3. Follow-ups refine the same request (`только дизель`) without re-asking brand/budget/city.

## Modules

| Module | Role |
|--------|------|
| `services/auto_request_memory.py` | Slots + one lead per commercial dialog |
| `services/auto_conversation_engine.py` | Welcome, search, refine, compare, save, monitor |
| `services/auto_client_output.py` | Client vs staff sanitizer |
| `services/auto_saved_search.py` | «Следить за новыми» |
| `services/auto_dealer_settings.py` | Owner controls + dealer sections |

## Entry

Telegram: **🤖 AI Менеджер** → free chat (`auto_vertical_ai_manager_chat`).

## Rules

- Max clarifying questions is owner-configurable (default **0**).
- Never show Score / Priority / Dept / Intent to clients.
- Russian First for all client replies.
