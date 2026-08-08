# Sprint 46.5 RESULT — Restore Vertical Navigation + Role Switcher

## 1. Root cause

Epic 44 registered EN vertical ReplyKeyboard labels (`🚗 Auto`, `🌾 Agro`, `💄 Beauty`, `💰 Crypto`) as **global AI Command intents** on `telegram_super_app_router`, which is registered **before** legacy Auto/Agro/Beauty handlers.

Path:

```
"🚗 Auto" → ai_command_buttons → BUTTON_TO_PROMPT → "Открой Auto AI"
  → AiCommandCenter.handle → enrich_prompt([контекст: vertical=beauty])
  → detect_vertical (beauty matched first from sticky context)
  → Hercules text generation
```

Sprint 43 Business RU labels (`🚗 Авто`, …) only showed hints — never called `handle_auto_menu_request` / `open_agro` / Cafe & Beauty.

## 2. Handlers that were intercepted

| Label | Wrong handler | Correct |
|-------|---------------|---------|
| `🚗 Auto` / `💄 Beauty` / … | `ai_command_buttons` → Hercules | `vertical_nav_router` → role selector |
| `🚗 Авто` / `🌾 Агро` / … | `business_section` hints / Beauty AI shell | `open_vertical_entry` → real menus |

## 3. Restored / reconnected (not rewritten)

- Auto Owner → `handle_auto_menu_request` / hub
- Auto Dealer → existing `auto_vertical_menu()` (add car, list, search, marketing, …)
- Auto Client → existing `auto_client_menu()`
- Agro Owner/Trader → existing `agro_menu()`
- Agro Client → subset of real Agro buttons
- Beauty roles → existing `cafe_beauty_module_menu()`
- Crypto → existing `open_crypto_otc`

## 4. Routing priority BEFORE / AFTER

**BEFORE:** Add-car FSM → Super App (AI Command) → … → Auto vertical → handlers  

**AFTER:**

1. active FSM / `auto_add_vehicle_router`
2. **`vertical_nav_router`** (vertical entry, persona, back, main menu)
3. Super App / AI Command / Concierge / Hercules
4. Auto client/dealer entry routers
5. `auto_vertical_handlers`
6. `handlers`

## 5–12. Role selectors

| Vertical | Personas (view-as) |
|----------|-------------------|
| Auto | Owner / Dealer / Client |
| Agro | Owner / Trader / Client |
| Beauty | Owner / Manager / Specialist / Client |
| Travel / Crypto / Legal / … | config in `VERTICAL_PERSONAS` |

`authenticated_role` (e.g. `platform_owner`) is **never** replaced by persona.

## 13. Beauty → Auto proof

`test_beauty_then_auto_sets_auto`: after Beauty then Auto, `active_vertical == "auto"` and `context_memory.vertical == "auto"`.

## 14. Navigation does NOT call Hercules

- Vertical labels removed from `BUTTON_TO_PROMPT` and AI Command menu
- `test_vertical_buttons_bypass_hercules`
- `open_vertical_entry` answers role selector only (`hercules=0` logged)

## 15. Context isolation + AI

- `detect_vertical` strips `[контекст: …]` / `vertical=…` tags
- `preferred` / `active_vertical` from session wins in `route_command`
- `AiCommandCenter.handle(..., active_vertical=, active_persona=, authenticated_role=)`

## Files

| File | Role |
|------|------|
| `services/vertical_role_registry.py` | VerticalRoleRegistry + session |
| `services/vertical_nav_service.py` | open entry / persona / clear stale |
| `routers/vertical_nav_router.py` | Telegram priority router |
| `startup.py` / `platform_legacy/adapter.py` | register order |
| `platform_ai_command/telegram/menu.py` | no vertical→Hercules map |
| `routers/telegram_super_app_router.py` | business → real verticals |
| `tests/test_vertical_nav_46_5.py` | regression suite |

## Tests

```bash
.venv/bin/python -m pytest tests/test_vertical_nav_46_5.py tests/test_ai_command_center_44_0.py -q
# 215 passed
```

## Architectural decisions

1. **Reconnect, don’t rewrite** — menus stay in `keyboards` / `auto_vertical_handlers` / `handlers`.
2. **AUTHORIZATION ≠ VIEW MODE** — `authenticated_role` vs `active_persona`.
3. **Vertical nav before Super App** — same pattern as HOTFIX 46.2.2 for FSM.
4. **Keep Hercules** for generative tasks only; navigation is deterministic.
5. **Vertical = workspace** — never replace menu with Concierge/Studio prompts.

## UX principle (critical)

Flow: `MAIN → VERTICAL → ROLE/VIEW-AS → FUNCTIONAL MENU → ACTION`

- Main menu lists verticals first; Concierge / Studio are optional.
- Travel opens `travel_module_menu` (туры, брони, …) — no “опишите задачу / Студия AI”.
- Concierge inside a vertical is optional assistant only.
- `💅 Beauty AI` = Studio; `💄 Красота` = Cafe & Beauty workspace.

## Done criteria

- [x] Auto/Agro/Beauty open as verticals  
- [x] Hercules does not intercept navigation  
- [x] Owner view-as personas  
- [x] Real menus restored  
- [x] Vertical switch clears stale context  
- [x] Owner auth preserved  
- [x] Back stack predictable  
- [x] AI gets active_vertical  
- [x] Regression tests PASS  
- [x] Vertical ≠ AI conversation (main menu + Travel functional menu)
