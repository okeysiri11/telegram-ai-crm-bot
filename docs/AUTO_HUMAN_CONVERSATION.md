# Auto Human Conversation

Sprint 46.1 — conversation quality, VIN state machine, short answers.

## Architecture (not one LLM prompt)

| Layer | Module |
|-------|--------|
| Dialog State Manager | `services/auto_dialog_state.py` |
| Conversation Memory | `services/auto_request_memory.py` |
| Intent / Action | `services/auto_conversation_engine.py` + search orchestrator |
| Human Conversation Policy | `services/auto_human_conversation_policy.py` |
| Conversation Quality Guard | `services/auto_conversation_quality_guard.py` |

## VIN root cause (fixed)

`routers/auto_client_router.py` → `auto_client_vin_choice_text` previously **re-asked** on any text including «Нет», leaving FSM in `awaiting_vin_choice` forever.

**Fix:** text «Нет» / «2» / skip tokens → `VIN_SKIPPED` → ack → `_finish_request` immediately.  
«Да» / «1» → `WAITING_FOR_VIN` → ask only for VIN.

## Short answers

With active dialog state, «да/нет/1/2/ищи/сюда/…» resolve via Dialog State Manager first — not as new intents.

## Owner defaults (Auto)

`conversation_style=concise`, `optional_questions=false`, `confirmation=ambiguity_only`,  
`cross_sell=false`, `max_clarifications=1`, `human_guard=true`.
