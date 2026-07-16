# Полный аудит репозитория

**Дата:** 2026-07-16  
**Репозиторий:** TelegramBotCourse  
**Метод:** статический анализ AST + grep + сверка регистрации роутеров  
**Режим:** только отчёт и предложения (код прод-потоков не менялся)

---

## Краткий вердикт

Рабочий CRM-путь (клиент → заявка → менеджер) жив, но репозиторий перегружен параллельными движками и «god»-файлами.

| Метрика | Значение |
|---------|----------:|
| Классов в `database/models` | ~530 |
| Неиспользуемых снаружи define-файла | **23** |
| Активных `routers/*` | 6 (все в `startup.py`) |
| Мёртвый handler-роутер | `automotive_treasury_handlers.py` (0 внешних ссылок) |
| Опасные дубли имён классов | `LeadEngineV1`, `DealEngineV1`, `Permission`, … |
| In-memory flow dicts (race/restart) | **11** |
| Блокирующих `time.sleep`/`requests` в async | **0** |
| Подозрений N+1 (await в цикле) | **24** |
| Дубликаты ключей в `.env` | `BOT_TOKEN`×2, `OPENROUTER_API_KEY`×2 |

---

## 1. Мёртвый код

### 1.1 Модели без внешних ссылок (23)

| Класс | Файл |
|-------|------|
| `AiAgent`, `AiDialog`, `AiAgentMemory`, `AiAgentSetting` | `database/models/ai_agents.py` |
| `CommissionRule` | `database/models/commissions.py` |
| `DealAgroExt`, `DealAutoExt`, `DealDroneExt`, `DealFinanceExt`, `DealLegalExt`, `DealLogisticsExt` | `database/models/deals.py` |
| `DealEngineDeal` | `database/models/deal.py` |
| `FinanceAccount` | `database/models/finance.py` |
| `AutomotivePartnerPayout`, `PayoutStatus` | `database/models/automotive_revenue_engine.py` |
| `PartnerKpi`, `PartnerCabinetRole` | partners / partner_cabinet |
| `PermissionCategory` | `rbac_v2_engine.py` |
| `RecommendationFeedbackType`, `SalesMessageRole`, `MediaType`, `ExportFormat`, `IntegrationChannelType` | соответствующие модули |

> Примечание: модели могут использоваться только через Alembic/metadata. Перед удалением — проверка FK и `configure_mappers()`.

### 1.2 Мёртвый роутер

- **`automotive_treasury_handlers.py`** — `external_refs=0`, **не** входит в `handlers.py` `include_router(...)`.
- Engine treasury используется из других мест; сам Telegram-роутер — мёртвый.

### 1.3 Scaffold-дубли (осознанные, но опасные при росте)

- `services/storage` ↔ `src/platform/storage`
- `services/notification_center` ↔ `src/platform/notifications`
- `events.py` / `crm_event_bus` / `src/events`

**Исправление:** пометить LEGACY-кандидаты; удалить/зарегистрировать treasury router; не развивать обе копии storage/notifications.

---

## 2. Дублирование

| Область | Копии | Риск |
|---------|-------|------|
| RBAC | `permission_engine_*`, `rbac_v2_*`, `permissions.py` | неверные гранты, mapper conflicts |
| Events | 3 поколения | пропуск подписчиков |
| Notifications / Storage | по 2 | расхождение конфигов |
| Inventory | vehicles / `inventory` / listings / lead marketplace | путаница продукта |
| SLA / Audit | по 2 | разрозненная аналитика |

### P0 — коллизия имён

В `services/pg_automotive_revenue_engine.py` объявлены классы:

- `LeadEngineV1` (есть также в `pg_lead_engine.py`)
- `DealEngineV1` (есть также в `pg_deal_engine_v1.py`)

Неосторожный импорт подменит тип.

**Исправление:** переименовать в `AutomotiveRevenueLeadRecorder` / `AutomotiveRevenueDealRecorder`.

---

## 3. Циклические зависимости

| Связка | Проблема |
|--------|----------|
| `auto_client_router` ↔ `auto_hub_router` | cross-router import |
| `handlers.py` → handlers → services → lazy imports | скрытые циклы |
| Lazy `from services.X import` внутри методов | граф непрозрачен |
| Корневой `events.py` vs пакет `events/` | конфликт имён (scaffold в `src/events/` — ок) |

**Исправление:** вынести навигацию Auto Client в `services/auto_client_navigation.py`.

---

## 4. Неиспользуемые импорты

Полный автофикс не делался. Рекомендуемый прогон:

```bash
.venv/bin/pip install ruff
.venv/bin/ruff check routers services/pg_auto_client_request_engine.py \
  services/pg_client_request_crm_engine.py auto_vertical_handlers.py \
  --select F401,F841
```

Ожидаемый шум: `handlers.py`, `database_legacy.py`, тестовые suites.

---

## 5. Неиспользуемые модели

См. §1.1 (23 класса).  
Дополнительно: десятки «лёгких» enum/status-классов используются только в одном модуле — не мёртвые, но кандидаты на сжатие API.

---

## 6. Неиспользуемые / незарегистрированные роутеры

| Роутер | Статус |
|--------|--------|
| `routers/auto_client_router` … `manager_debug_router` | ✅ в `startup.py` |
| `auto_vertical_handlers.auto_vertical_router` | ✅ |
| `handlers.router` (+ вложенные) | ✅ |
| `automotive_treasury_handlers.automotive_treasury_router` | ❌ не подключён |

Список include в `handlers.py`: start_routing, tenant_guard, deal_workflow, ai_sales, dealer_onboarding, dealer_quote_authority, bidex, automotive_partner, automotive_revenue, vertical_onboarding, owner_panel, lead_engine, deal_engine, revenue, cart, owner_dashboard, crm_pipeline, anti_loss, partner_cabinet, payment, owner_payment_profile — **без treasury**.

---

## 7. Race conditions / shared mutable state

Глобальные dict без lock (теряются при рестарте, опасны при >1 worker):

| Файл | Состояние |
|------|-----------|
| `auto_vertical_handlers.py` | `auto_vertical_active`, `auto_vertical_flow`, `auto_billing_flow` |
| `automotive_partner_handlers.py` | `partner_lead_flow` |
| `cart_engine_handlers.py` | `cart_sessions`, `pending_checkout` |
| `lead_engine_handlers.py` | `lead_assign_flow` |
| `owner_panel_handlers.py` | `owner_notes_edit_flow` |
| `owner_payment_profile_handlers.py` | `owner_payment_edit_flow` |
| `payment_engine_state.py` | `pending_payment_upload` |
| `services/tenant_context.py` | `_active_tenant_by_user` |

Дополнительно: escalation loop каждые 60с без distributed lock → при 2 репликах бота двойные уведомления.

**Исправление:** Redis FSM/hashes; `SET escalation:lock NX EX 55`.

---

## 8. Блокирующие операции в async

Скан `time.sleep` / `requests.*` / `subprocess.run` внутри `async def`: **0 находок**.

Остаточные UX-блокировки (async I/O, но долгие):

- OpenRouter при finish заявки (`pg_ai_manager_engine`)
- Новый `Bot()` session на каждое notify менеджеру
- Последовательная рассылка в escalation/SLA

**Исправление:** вынести AI qualify в фон; шарить Bot instance; ограничить concurrency.

---

## 9. SQL без индексов

CRM-путь в целом покрыт:

- `client_requests` — client, manager, status, funnel, type, number ✅  
- `auto_client_requests_v1` — аналогично ✅  
- `inventory` — status, seller, brand+model, year, price, city, fuel ✅  

**Пробелы:**

| Риск | Предложение |
|------|-------------|
| Escalation scan `closed_at IS NULL AND first_response_at IS NULL` | partial index на `lead_sla_records` |
| Сложный search inventory (status+price+brand) | composite index по мере роста |
| JSONB photos | GIN обычно не нужен |

---

## 10. N+1 / await в цикле (24 подозрения)

Критичнее для runtime:

| Место | Почему важно |
|-------|----------------|
| `crm_event_bus._dispatch_event` | handlers по одному |
| `pg_webhook_engine.process_pending_retries` | сеть в цикле |
| `pg_automotive_marketplace_engine._sync_images` | поштучная синхронизация |
| `crm_pipeline_boards_repository.list_*_by_stage` | возможные доп. запросы |

Seed/bootstrap циклы (RBAC seed) — приемлемы на старте.

**Исправление:** `asyncio.gather` с semaphore; bulk insert; batch webhook.

---

## 11. Секреты

| Факт | Оценка |
|------|--------|
| `.env` в `.gitignore` | ✅ |
| Дубликаты ключей `BOT_TOKEN`, `OPENROUTER_API_KEY` | ⚠ путаница, last-wins |
| `JWT_SECRET` default `change-me-in-production` | 🔴 слабо для API |
| `REDIS_REQUIRED=false` | ⚠ тихая потеря FSM |
| Live tokens в локальном `.env` | нормально локально; **ротировать**, если среда шарится/логируется |

**Не коммитить** `.env` / `.env.production` с реальными токенами.

---

## 12. Потеря FSM-состояния

| Риск | Механизм |
|------|----------|
| MemoryStorage fallback | `fsm_storage.py` при недоступном Redis |
| `REDIS_REQUIRED=false` | рестарт → обрыв mid-flow |
| Auto Client pending restore | только step key, не полный draft bag |
| `auto_vertical_flow` in-memory | VIN/search mid-flow теряется |
| Photo album collector | буфер медиагруппы в процессе |

`state.clear()` встречается ~9 раз — меню/submit в целом чистят FSM; проблема именно в **хранилище и in-memory vertical flows**.

**Исправление:** prod `REDIS_REQUIRED=true`; draft payload в Redis/DB; vertical flow → Redis.

---

## План исправлений (приоритет)

### P0 — безопасность / коллизии (1–2 дня)

1. Почистить дубли в `.env`; выставить сильный `JWT_SECRET`; для prod — `REDIS_REQUIRED=true`.
2. Ротировать bot token / OpenRouter key при подозрении на утечку.
3. Переименовать `LeadEngineV1`/`DealEngineV1` в revenue-engine.
4. Удалить или `include_router` для `automotive_treasury_handlers`.

### P1 — стабильность (1–2 недели)

5. In-memory flows → Redis.
6. Distributed lock для escalation.
7. AI qualification в фон (не блокировать ответ клиенту).
8. Разорвать цикл auto_client ↔ auto_hub.
9. `ruff F401` на `routers/` + новые CRM-сервисы.

### P2 — консолидация (2–4 недели)

10. Один путь notifications/storage.
11. Один RBAC = `permission_engine_*`.
12. Dual-write `src.events` с CRM submit; позже убрать дубли.
13. Partial index для open SLA; concurrency limit на webhooks.
14. Заморозить `database_legacy.py` / `handlers.py` god-рост.

### P3 — платформа (после гигиены)

15. Подключить `api/v1` к **существующим** engines.
16. Tenant filters на `client_requests`.
17. Pytest coverage ≥70% **только на CRM/marketplace пакетах**, не на всём 70k+ LOC.

---

## Минимальные патчи (наименьший diff)

```text
1) rename colliding classes in pg_automotive_revenue_engine.py
2) register OR delete automotive_treasury_router
3) .env hygiene + REDIS_REQUIRED + JWT_SECRET
4) services/auto_client_navigation.py (break router cycle)
```

Пункты 1–3 **не требуют** изменения FSM/сценариев клиента.

---

## Команды проверки

```bash
# коллизия имён
PYTHONPATH=. python -c "from services.pg_lead_engine import LeadEngineV1 as A; import services.pg_automotive_revenue_engine as m; print(A, m.LeadEngineV1, A is m.LeadEngineV1)"

# мёртвый treasury router
rg "automotive_treasury_router" -g '*.py'

# FSM storage
rg "REDIS_REQUIRED|MemoryStorage" .env fsm_storage.py config.py

# unused imports (точечно)
ruff check routers --select F401
```

---

## Вывод

Главный долг — **не недостаток фич**, а **дубли, коллизии имён, in-memory state и слабая дисциплина секретов/Redis**.  
Сначала P0–P1 hygiene, затем расширение платформы через уже созданный `src/` strangler — без новых параллельных движков.
