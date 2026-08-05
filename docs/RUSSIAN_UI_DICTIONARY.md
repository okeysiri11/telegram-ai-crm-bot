# Sprint CQ-30.1 — Russian UI Dictionary

**Sprint:** CQ-30.1 — UX Design + Localization. Documentation only, `src` not modified.

**Do not duplicate:** real `src/web/src/i18n/messages.ts` already implements a working `en/ru/uk`
translation store (Zustand `useI18n`, real key namespace: `app.*`/`nav.*`/`auth.*`/`dash.*`/`common.*`,
21 real keys, professional business Russian already in production style — e.g. `"nav.dashboard":
"Панель"`, `"dash.kpis": "KPI"`). This document extends that real namespace convention for every
Beta surface this sprint designed; it does not propose a second i18n system or a different key format.

## 1. Principle: one Russian term per concept, enforced against `docs/SEMANTIC_DICTIONARY.md`

Where this engagement's own CQ-20 semantic work already picked a preferred English term over a
synonym (Company over Organization, Citizen over Worker/Employee-as-ontology-term, Meeting over
Appointment, Deal over Opportunity, Project over Engagement — `docs/SEMANTIC_DICTIONARY.md` §1), the
Russian dictionary below uses **exactly one** Russian term for that concept everywhere, even where an
English synonym might tempt a translator toward a second Russian word. This is the localization-layer
enforcement of that document's own rule.

## 2. Canonical dictionary — extending the real `messages.ts` namespaces

### `nav.*` (extends 5 real keys with the Beta's full sidebar, per `docs/UX_ARCHITECTURE.md` §1)

| Key | English | Russian (canonical) | Notes |
|---|---|---|---|
| `nav.dashboard` | Dashboard | Панель | **Real, unchanged** |
| `nav.city` | City | Город | New |
| `nav.business` | Business Network | Бизнес-сеть | New — not "Организации" (reserved, see `org.*`) |
| `nav.deals` | Deals | Сделки | New — same term for Deal everywhere (`docs/SEMANTIC_DICTIONARY.md` §1's preferred term) |
| `nav.projects` | Projects | Проекты | New |
| `nav.operations` | Operations | Операции | New |
| `nav.calendar` | Calendar | Календарь | New — matches real `dash.calendar` exactly, not a synonym |
| `nav.tasks` | Tasks | Задачи | New — matches real `dash.tasks`'s root "задачи," singular form for the nav label |
| `nav.aiAgents` | AI Agents | AI-агенты | New — same "AI-" prefix convention as real `dash.ai: "AI-ассистент"` |
| `nav.production` | Production Studio | Студия продакшна | New |
| `nav.analytics` | Analytics | Аналитика | New |
| `nav.settings` | Settings | Настройки | **Real, unchanged** |

### `org.*` (new namespace — Organization Switcher, `docs/UX_ARCHITECTURE.md` §1)

| Key | English | Russian | Notes |
|---|---|---|---|
| `org.switcher` | Organization | Компания | Per `docs/SEMANTIC_DICTIONARY.md` §1: Company is preferred over Organization — the Russian term is "Компания" everywhere, never "Организация," even though the UI-facing English label says "Organization Switcher" (matching the real `auth.tenant: "Компания"` key already in production) |
| `org.switch` | Switch organization | Сменить компанию | New |
| `org.create` | Create organization | Создать компанию | New |

### `role.*` (new namespace — `docs/ROLE_NAVIGATION.md`)

| Key | English | Russian | Notes |
|---|---|---|---|
| `role.owner` | Owner | Владелец | New |
| `role.admin` | Administrator | Администратор | New |
| `role.manager` | Manager | Менеджер | New |
| `role.employee` | Employee | Сотрудник | New |
| `role.client` | Client | Клиент | New |
| `role.dealer` | Dealer | Дилер | New |
| `role.partner` | Partner | Партнёр | New |
| `role.lawyer` | Lawyer | Юрист | New |
| `role.accountant` | Accountant | Бухгалтер | New |
| `role.production` | Production | Продакшн | New — matches `nav.production`'s root, not a separate word |
| `role.viewer` | Viewer | Наблюдатель | New |

### `owner.*` (new namespace — `docs/OWNER_MODE_UX.md`)

| Key | English | Russian | Notes |
|---|---|---|---|
| `owner.platformHealth` | Platform Health | Состояние платформы | Distinct from real `dash.health: "Состояние системы"` — Platform Health is the Owner-scoped, all-runtime view; System Health (real key) is the general one. Kept as two terms deliberately since they are two real, different-scoped signals (`docs/OWNER_MODE_UX.md` §1) |
| `owner.overview` | Enterprise Overview | Обзор предприятия | New |
| `owner.securityCenter` | Security Center | Центр безопасности | Matches the real `SecurityCenterPage.tsx`'s already-shipped English label's natural Russian translation |
| `owner.audit` | Audit | Аудит | New |
| `owner.architecture` | Architecture | Архитектура | New |
| `owner.devTools` | Developer Tools | Инструменты разработчика | New |
| `owner.cityAdmin` | City Administration | Управление городом | New |
| `owner.organizations` | Organizations | Компании | Same root as `org.switcher` — "Компании" (plural), not a new word |

### `city.*` (new namespace — `docs/CITY_NAVIGATION.md` §4)

| Key | English | Russian | Notes |
|---|---|---|---|
| `city.district` | District | Район | New |
| `city.building` | Building | Здание | New |
| `city.contextMenu.open` | Open | Открыть | New |
| `city.contextMenu.focus` | Focus | Приблизить | New |
| `city.contextMenu.favorite` | Add to Favorites | В избранное | Matches real `dash.favorites: "Избранное"` root exactly |
| `city.filters` | Map Filters | Фильтры карты | New |
| `city.minimap` | Mini-map | Мини-карта | New |
| `city.zoomCity` | City View | Общий вид | New — per `docs/CITY_NAVIGATION.md` §2's real zoom-level names |
| `city.zoomDistrict` | District View | Вид района | New |
| `city.zoomBuilding` | Building Focus | Вид здания | New |

### `production.*` (new namespace — `docs/PRODUCTION_STUDIO_UX.md`, real 17-studio catalog)

| Key | English | Russian | Notes |
|---|---|---|---|
| `production.image` | Image Studio | Студия изображений | Matches real `productionCatalog.ts` studio id `image` |
| `production.video` | Video Studio | Студия видео | Matches real id `video` |
| `production.reels` | Reels Factory | Фабрика Reels | "Reels"/"TikTok" kept as transliterated proper nouns per platform convention, not translated |
| `production.voice` | Voice Studio | Студия озвучки | Matches real id `voice` |
| `production.brand` | Brand Studio | Студия бренда | Matches real id `brand` |
| `production.prompt` | Prompt Studio | Студия промптов | "Prompt" transliterated, matching common Russian AI-industry usage, not translated to "подсказка" (which would be a false-friend translation in this domain) |
| `production.pipeline` | Pipeline | Конвейер | New — real `PIPELINE_STAGES` (draft/review/approval/generation/render/publish/archive) |
| `production.pipeline.draft` | Draft | Черновик | Matches real pipeline stage `draft` |
| `production.pipeline.review` | Review | Проверка | Matches real stage `review` |
| `production.pipeline.approval` | Approval | Утверждение | Matches real stage `approval` — same root as any future `owner.*`/approval-center term, kept consistent |
| `production.pipeline.publish` | Publish | Публикация | Matches real stage `publish` |
| `production.pipeline.archive` | Archive | Архив | Matches real stage `archive`, same root as `owner.audit`'s archival concept elsewhere in this engagement |

### `auth.*` (extends 5 real keys — `docs/LOGIN_USER_FLOW.md`)

| Key | English | Russian | Notes |
|---|---|---|---|
| `auth.login` | Sign in | Войти | **Real, unchanged** |
| `auth.register` | Register | Регистрация | New |
| `auth.googleSignIn` | Sign in with Google | Войти через Google | New |
| `auth.forgotPassword` | Forgot password? | Забыли пароль? | New |
| `auth.mfa` | Two-factor authentication | Двухфакторная аутентификация | New |
| `auth.invitation` | You've been invited | Вас пригласили | New |
| `auth.joinOrg` | Join organization | Присоединиться к компании | Same "компания" root as `org.*`, not "организация" |

## 3. Terms deliberately kept in English/transliterated (not translated)

Per real precedent already in `messages.ts` (`"dash.kpis": "KPI"`, kept untranslated): `AI`, `KPI`,
`Reels`, `Prompt` (as a domain term, see `production.prompt` note above), and City district names
where they follow the real Odessa-narrative convention (`docs/CITY_LIVING_ECONOMY.md`, CQ-10) are kept
as-is rather than forced into a Russian equivalent that would be less recognizable to the target
business audience.

## Non-goals

- No second i18n store or key format — every entry above extends the real `messages.ts` namespace
  convention exactly.
- No Ukrainian (`uk`) column produced this sprint — the brief scoped Russian specifically; extending
  `uk` alongside `ru` for these same keys is a natural, low-cost follow-up given the real store already
  supports it structurally.

## Related documents

`src/web/src/i18n/messages.ts` (real, the system this document extends), `docs/SEMANTIC_DICTIONARY.md`
(CQ-20, the preferred-English-term rulings this document's Russian choices follow), `docs/UX_
ARCHITECTURE.md`/`docs/ROLE_NAVIGATION.md`/`docs/OWNER_MODE_UX.md`/`docs/CITY_NAVIGATION.md`/
`docs/PRODUCTION_STUDIO_UX.md`/`docs/LOGIN_USER_FLOW.md` (CQ-30.1 siblings, the source of every key
above).
