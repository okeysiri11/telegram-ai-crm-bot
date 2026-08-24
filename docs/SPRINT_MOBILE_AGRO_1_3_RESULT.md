# Sprint MOBILE AGRO 1.3 — Real Agro workspace on the phone

## What shipped

Phone Agro is the operational cabinet (menu B), not the generic domain catalog (menu A).

1. **Primary mobile drawer = 19 Agro ops items:** Главная, Контрагенты, Сделки, Договоры, Документы, Расчёты, Бухгалтерия, Поставки, Склады, Культуры, Погода, Цены и рынки, Логистика, Агро-разведка, Аналитика, Календарь, Задачи, Уведомления, Настройки. Links are `/workspace/agro` and `/workspace/agro?view=…`.
2. **Menu A is not deleted.** Товары / Поля / Техника / Посевы / Урожай / Полив / Склад / Работы / ИИ-помощник remain in `vertical-workspace/catalog.ts` and `/vertical/agro`. They are not mixed into the phone drawer. Nesting under «Операционная деятельность» is deferred.
3. **`/workspace/agro` on mobile skips the catalog landing** and mounts `AgroBusinessPage`. Desktop ≥768px still uses the landing gate.
4. **Workspace switch** (Агро / Авто / Crypto / Beauty / Legal / …) persists `verticalId`, loads that vertical’s ops nav, and uses relative public routes (no localhost / `:5180` / `:8080` in browser nav).
5. **Home CTAs** with current workspace Агро: «Открыть рабочее пространство» and «Открыть панель» → `/workspace/agro`.
6. **Android back:** drawer/sheet open → back closes overlay first. Weather → back uses history (`navigate(-1)`), not a kick to login/dashboard.
7. **Drawer density:** row min-height 50px (48–54px target). Platform management is not dumped into the Agro drawer (it stays under Ещё).

## Architectural decisions

- Single source for Agro ops labels: `workspace/agro/agroOpsNav.ts` (cabinet + mobile drawer). Domain catalog A stays in `catalog.ts`.
- Mobile drawer never uses `navFromContext` / catalog A for operational verticals.
- Overlay history: one `pushState` while a sheet is open; navigating from the overlay `replace`s that entry so Weather → back returns to the previous Agro view.

## Genuinely deferred

- Nesting domain catalog A under «Операционная деятельность».
- First login still shows «Владелец системы» until a workspace is selected (then it persists).

MOBILE 1.4 was not started.
