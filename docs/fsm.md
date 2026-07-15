# FSM Reference

## Rule for architecture night task

**Do not modify existing FSM states or transitions.**

Current Auto Client FSM (`states/entry_flow_states.py`):

- `language_select`
- `menu`
- `collecting`
- `awaiting_photos`
- `awaiting_vin`
- `awaiting_phone`
- `services_hub`

Auto Dealer:

- `language_select`
- `dealer_onboarding`

## Guarantees already in product

- Menu buttons clear FSM before starting a new flow
- `state.clear()` after request completion
- Interrupt helpers for back / main menu

## Future domain routers

When migrating to `src/domains/*/routers`, FSM groups should move with the domain  
**only after** parity tests — never mid-flight rewrite.
