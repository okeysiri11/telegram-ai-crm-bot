# Sprint 42.9 — Owner Experience, AI Chat & Human-First Workflow

**Дата:** 2026-08-06  
**Режим:** Enterprise Product Polish · Human UX · Owner Experience · Russian First  
**Область:** `src/web` (без новых backend engine / без ломки API)

## Цель

Сделать платформу интуитивной для ежедневной работы владельца: кто он, где находится, что может сделать, как обратиться к AI, как переключать роль / организацию / рабочее пространство — **без новых функций-движков**, только UX-слой поверх существующей архитектуры.

## Что сделано

### 1. Русификация (критические поверхности)

| Поверхность | Изменение |
|-------------|-----------|
| Launcher (`desktopCatalog` + `DesktopLauncher`) | RU labels, поиск «Поиск приложений…», категории, избранное, недавние, закрепление |
| Shell nav (`enterpriseNav`) | RU: Панель управления, Студия AI, AI-агенты, … |
| Production studios | RU labels для студий и стадий пайплайна |
| City catalog | Студии / Digital Citizens → RU |
| `enterpriseRuNav` | «Студия AI» |
| i18n | default locale уже `ru` |

Английский остаётся для: идентификаторов, API keys, user data, брендов (TikTok/Instagram/YouTube), акронимов (CRM, ERP, AI, VIN, AML).

### 2. Owner Identity (верхняя панель)

Пакет `src/web/src/owner-experience/`:

- `OwnerIdentityStrip` — **Пользователь → Работаю как / Роль → Организация → Рабочее пространство**
- Встроен в `TopNavigation` вместо узкого WorkspaceSwitcher

### 3. Переключатель «Работаю как»

`workAsCatalog.ts`: Владелец платформы · CEO организации · Менеджер · Оператор · Клиент · Партнёр · Демо  
При смене → `viewMode` + `roleSwitcher` + навигация на home роли (меню / дашборд / разрешения через существующий UX Revolution).

### 4. Меню профиля

- `.ews-user-menu` → `position: fixed`, `z-index: 90`, `max-height` + scroll
- Позиция по `getBoundingClientRect` аватара (не обрезается dock / `overflow: hidden` хедера)
- Пункт «Центр AI-задач»

### 5–6. AI Chat + контекст вертикали

- `ContextualAiChat` — модальный чат «Поговорить с AI»
- Кнопки в header и на welcome вертикали
- Owner всегда говорит с **AI Консьержем**; специалист выбирается по `verticalId` (CRM AI, Auto AI, …)

### 7–8. Welcome вертикали + быстрые действия

- `VerticalDashboard`: «Добро пожаловать. Вы работаете в разделе: …»
- `QuickCreatePanel`: Клиент · Документ · Проект · AI-задача · Напоминание · Сделка · Контакт

### 9. Центр AI-задач

- Маршрут `/ai-tasks` → `AiTasksPage`
- Описание · исполнитель AI · приоритет · статус (черновик → запущена → выполняется → готово)
- Хранение в `localStorage` (UX-слой, без нового engine)

### 10. AI Concierge

Единый Concierge во всех вертикалях (Sprint 42.8 + маршрутизация 42.9). Owner не выбирает модель.

### 11. Launcher

Полный RU + поиск + категории + избранное + недавние + pin ★/☆.

### 12. Вертикали

Каркас `/vertical/:id` (42.8) + welcome / AI / create (42.9) для Owner, CRM, Auto, Crypto, Travel, Drone, Construction, Production, Knowledge, Documents, Marketplace, AI Studio (+ Agro).

## Архитектурные решения

| Решение | Почему |
|---------|--------|
| Новый пакет `owner-experience/` | UX-слой без нового `platform_*` / engine |
| Work-as → существующие `viewMode` + `roleSwitcher` | Не дублировать RBAC |
| AI chat / tasks на client + localStorage | Полировка UX, не runtime AI |
| Concierge + specialist map | Owner говорит с одним AI; контекст из вертикали |

**Отклонено:** отдельный identity microservice, новый agent runtime, parallel English UI tree.

## Тесты и проверки

| Проверка | Статус |
|----------|--------|
| Vitest `sprint_42_9_owner_experience.test.ts` | ✓ pass |
| Vitest shell + vertical 42.8 | ✓ pass |
| Typecheck (`tsc -b` / `npm run lint`) | ✓ pass |
| Production build (`npm run build`) | ✓ pass |
| Foundation RU nav expectations | ✓ обновлены под RU |
| Navigation / role / workspace / AI / RU | ✓ unit catalogs |

**Deferred manual smoke:** полный проход по всем вертикалям в браузере (чеклист в разделе «Как проверить»).

## Как проверить вручную

1. Войти `owner@ados.demo` / `demo`
2. В шапке: пользователь, «Работаю как», организация, рабочее пространство
3. Переключить «Работаю как» → смена home / меню
4. Открыть меню аватара — поверх dock
5. «Поговорить с AI» на `/vertical/crm` → контекст CRM AI
6. «Создать» → панель быстрых действий
7. `/ai-tasks` → создать и запустить задачу
8. Ctrl/Cmd+Space → Launcher на русском с поиском и ★

## Deferred (осознанно)

- 100% EN→RU во всех EngineStudio / legacy builder body copy (остаток Sprint 42.5)
- Deep permission matrix per Work-as (сейчас через viewMode)
- Real LLM streaming в ContextualAiChat (демо-ответы)

## Файлы

- `src/web/src/owner-experience/*`
- `src/web/src/navigation/TopNavigation.tsx`
- `src/web/src/vertical-workspace/VerticalDashboard.tsx`
- `src/web/src/enterprise-desktop/DesktopLauncher.tsx`, `desktopCatalog.ts`
- `src/web/src/shell/enterprise/enterpriseNav.ts`, `enterpriseShell.css`
- `src/web/src/App.tsx` (`/ai-tasks`), `main.tsx` (CSS)
- `docs/SPRINT_42_9_OWNER_EXPERIENCE.md` (этот отчёт)
