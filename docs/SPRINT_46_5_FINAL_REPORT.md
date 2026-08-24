# Sprint 46.5 — FINAL REPORT

**Vertical Navigation Restore + Role View-As + Manual Interface First**

Principle:

```
                 ADOS
                   │
         ┌─────────┴─────────┐
         │                   │
   Manual Interface        AI Interface
   Buttons / Menus      Voice / Concierge
         │                   │
         └─────────┬─────────┘
                   ↓
             Domain Actions
                   ↓
          Workflows / Hercules
                   ↓
                Result
```

AI is an **optional** control surface — never a replacement for vertical workspaces.

---

## 1. Что было сломано

| Problem | Cause |
|---------|--------|
| `🚗 Auto` / `🌾 Agro` / `💄 Beauty` / `💰 Crypto` → Hercules text | Epic 44 mapped EN vertical labels to `BUTTON_TO_PROMPT` on Super App router **before** legacy handlers |
| Auto → reply about Beauty vertical | Sticky `context_memory` + beauty-first `detect_vertical` on enriched `[контекст: vertical=beauty]` |
| Business RU labels (`🚗 Авто`…) | `business_section` showed Concierge/Studio **hints**, not real hubs |
| Main menu AI-first | Sprint 43 Super App put Concierge/Studio first; verticals buried under «Бизнес» |
| Travel after role select | Stub: «Опишите задачу / Студия AI» |

---

## 2. Какие старые handlers найдены

| Vertical | Existing code |
|----------|----------------|
| **Auto** | `auto_vertical_handlers.handle_auto_menu_request`, `_open_auto_hub`, `auto_vertical_menu`, `auto_client_menu`, `auto_vertical_hub_menu` |
| **Agro** | `handlers.open_agro`, `agro_menu`, product/deal/CRM screens |
| **Beauty business** | `handlers.open_cafe_beauty_module`, `cafe_beauty_module_menu`, `MODULE_STUB_BUTTONS` |
| **Beauty AI** | Super App `_open_beauty_vertical` / `💅 Beauty AI` (Studio) |
| **Crypto** | `handlers.open_crypto_otc`, `crypto_otc_menu`, Buy/Sell flow, Crypto Agent |
| **Legal** | `law_module_menu`, unused `lawyer_menu`, module stubs |
| **Drone** | `drone_module_menu` + drone handlers |
| **Registry** | `platform_registry/menus` telegram vertical entries |

---

## 3. Какие были восстановлены / reconnect

| Action | Result |
|--------|--------|
| `routers/vertical_nav_router` **before** Super App | Deterministic vertical entry |
| Role selector → existing menus | No Hercules on navigation |
| Business section → `open_vertical_entry` | Real workspaces |
| Auto Owner/Dealer/Client | hub / `auto_vertical_menu` / `auto_client_menu` |
| Agro Owner/Trader/Client | `agro_menu` / subset |
| Beauty business vs AI | Cafe & Beauty menu vs `💅 Beauty AI` Studio |
| Crypto Owner/Trader/Client | full OTC / client Buy-Sell |
| Legal Owner/Lawyer/Client | `law_module_menu` / `lawyer_menu` / `legal_client_menu` |
| Travel | `travel_module_menu` (туры, брони, …) |
| Crypto `💵 Курсы` / `📊 PnL` | Wired handlers |
| Agro dead labels | Scoped stubs when `active_module=agro` |
| Main menu | Verticals **first**; Concierge/Studio optional |

---

## 4. Какие новые компоненты сохранены

| Component | Status |
|-----------|--------|
| Hercules | Execution backend — unchanged |
| AI Command Center | Generative tools only (image/video/doc/CRM) |
| Concierge | Optional assistant button inside verticals + main |
| AI Studio / Beauty AI Production | Standalone Studio path |
| Continuous Memory / Unified Intent (web) | Untouched |
| Voice / Mode Manager | Untouched |
| Add-car FSM (46.2.2) | Still first in router order |

**New orchestration (not a rewrite):**

- `services/vertical_role_registry.py`
- `services/vertical_nav_service.py`
- `routers/vertical_nav_router.py`

---

## 5. Карта меню каждой вертикали

### Auto
| Persona | Menu |
|---------|------|
| Owner | Hub: машины, страхование, кредит, лизинг, логистика, юр. + nav |
| Dealer | Добавить/список/поиск/калькулятор/продвижение/аналитика/AI/лиды/тариф/казначейство/настройки |
| Client | Купить / продать / объявление / услуги / менеджер / мои заявки |

### Agro
| Persona | Menu |
|---------|------|
| Owner / Trader | Товары, страны, логистика, цены, контракты, аналитика, БД, календарь, фрахт, склады, контрагенты, сделки, документы, финансы, отчёты, AI Agro |
| Client | Товары, контрагенты, контракты, сделки |

### Beauty
| Layer | Entry | Menu |
|-------|-------|------|
| **Business** | `💄 Красота` → roles | Cafe, Салон, Клиенты, Записи, Склад, Календарь (Client: Записи+Салон) |
| **AI Production** | `💅 Beauty AI` in Studio | Posts, Reels, banners, promo… (unchanged) |

### Crypto
| Persona | Menu |
|---------|------|
| Owner / Trader | Buy/Sell USDT/Cash, Сделки OTC, Crypto Agent, Курсы, PnL |
| Client | Buy/Sell only |

### Legal
| Persona | Menu |
|---------|------|
| Owner | Дела, Документы, Законодательство, Судебная практика, Календарь |
| Lawyer | + Профиль (`lawyer_menu`) |
| Client | Дела, Документы, Календарь |

### Travel
| Persona | Menu |
|---------|------|
| All | Туры, Бронирования, Клиенты, Отели, Авиа, Документы, Платежи, Аналитика |

### Common chrome (all)
`🔄 Сменить роль` · `🏠 Главное меню` · `🤖 AI Консьерж` (optional)

---

## 6. Role matrix

| Vertical | Personas (view-as) | Auth preserved |
|----------|--------------------|----------------|
| Auto | Owner / Dealer / Client | `platform_owner` |
| Agro | Owner / Trader / Client | ✓ |
| Beauty | Owner / Manager / Specialist / Client | ✓ |
| Travel | Owner / Manager / Agent / Client | ✓ |
| Crypto | Owner / Trader / Client | ✓ |
| Legal | Owner / Lawyer / Client | ✓ |
| Drone | Owner / Operator / Client | ✓ |

`authenticated_role` ≠ `active_persona` (AUTHORIZATION ≠ VIEW MODE).

---

## 7. Test results

```bash
.venv/bin/python -m pytest tests/test_vertical_nav_46_5.py -q
# 18 passed
```

Coverage includes:

- vertical buttons bypass Hercules  
- Beauty → Auto clears sticky vertical  
- owner view-as preserves auth  
- Auto/Agro/Beauty/Crypto/Legal/Travel selectors  
- main menu vertical-first  
- Travel has no Concierge/Studio replacement copy  
- Crypto client vs Legal lawyer menus  

---

## 8. Оставшийся technical debt

| Item | Severity | Note |
|------|----------|------|
| Agro owner rows still partly stubs | Medium | Handlers reply «экран подключен»; need real Agro ERP data |
| Travel sections are text stubs | Medium | Align with web Travel workspace APIs later |
| Beauty manager/specialist share business menu | Low | Same Cafe & Beauty surface; finer RBAC later |
| Construction not on main menu | Low | In registry; no Telegram keyboard yet |
| In-process VerticalSession | Medium | Multi-worker: move to Redis/Postgres like FSM |
| Some Agro buttons still «в разработке» | Known | Pre-existing module stubs |
| Typecheck noise in unrelated `src/web` AI tests | Pre-existing | Not introduced by 46.5 |

---

## DONE criteria checklist

- [x] Auto Owner / Dealer / Client menus  
- [x] Agro Owner / Trader / Client menus  
- [x] Beauty business + separate Beauty AI Production  
- [x] Crypto Owner / Trader / Client  
- [x] Legal Owner / Lawyer / Client  
- [x] Owner switches view role without new accounts  
- [x] Concierge not mandatory entry  
- [x] Old business functions reconnected  
- [x] AI / Hercules preserved  
- [x] RU-first labels  
- [x] No intentional dead crypto rates/PnL buttons  
- [x] Navigation regression tests PASS  
- [ ] Full `src/web` lint/build — pre-existing unrelated TS errors may remain  

---

## Files

- `services/vertical_role_registry.py`
- `services/vertical_nav_service.py`
- `routers/vertical_nav_router.py`
- `startup.py` / `platform_legacy/adapter.py`
- `keyboards.py` (persona subsets + travel)
- `handlers.py` (Курсы/PnL, agro stubs, agro analytics scope)
- `services/telegram_ai_super_app/keyboards.py` (vertical-first main)
- `tests/test_vertical_nav_46_5.py`
- `docs/SPRINT_46_5_RESULT.md`
