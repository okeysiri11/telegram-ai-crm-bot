# Sprint CQ-30.7 — Russian Localization Review

**Scope:** review Russian localization; recommend better wording for buttons, titles, menus,
notifications, settings. Documentation only, `src` not modified.

**Context:** `docs/RUSSIAN_UI_DICTIONARY.md` (CQ-30.1) proposed a canonical dictionary before the real
`enterpriseRuNav.ts` (Sprint 30.2/30.7) shipped. This review checks the real, live Russian text against
that proposal and against internal consistency, not against a hypothetical ideal — and finds the real
implementation is largely good, with one serious bug and a few smaller polish items.

## 1. Critical: fix Маркетинг → Маркетплейс for the `marketplace` module id

Restated from `docs/UX_AUDIT.md`/`docs/NAVIGATION_REVIEW.md` as this document's own top wording
recommendation: `MODULE_LABEL_RU.marketplace`, `BREADCRUMB_LABEL_RU.marketplace`, and `SEARCH_
CATEGORY_RU.marketplace` should all read **"Маркетплейс"**, matching the sidebar's own correct label.
The `marketing` sidebar entry, if a real distinct Marketing module is ever built, should get its own
route rather than sharing `/marketplace`; if no distinct Marketing module is planned, the `marketing`
sidebar entry should be removed rather than left as a confusing second door to the same room.

- **Priority:** P0. **Complexity:** S. **Evidence:** `enterpriseRuNav.ts`, three dictionary constants.

## 2. Terminology consistency check — mostly good

Sampled against `docs/SEMANTIC_DICTIONARY.md`'s (CQ-20) preferred-term rulings:

| Concept | Real Russian term(s) | Consistency |
|---|---|---|
| Deal | Not directly in `enterpriseRuNav.ts`'s sidebar (CRM covers it) | N/A — no conflict found |
| Project | "Проекты" (sidebar), "Проекты" (search category) | Consistent |
| Task | "Задачи" (sidebar), "Задачи" (quick action) | Consistent |
| Company/Organization | "Компании" (org selector, search category `organizations`) | Consistent with CQ-20's "Company preferred over Organization" ruling |
| Client | "Клиенты"/"Клиент" throughout (sidebar, search, role switcher) | Consistent |
| Production Studio | "Продакшн" (sidebar `production_studio`) vs. this engagement's own CQ-30.1 proposal of "Студия продакшна" | **Real implementation is terser and arguably better** — recommend `docs/RUSSIAN_UI_DICTIONARY.md` (CQ-30.1) be updated to match the shipped "Продакшн" rather than the other way around |

## 3. Two real Russian words for "monitoring" — verify, don't necessarily fix

Restated from `docs/NAVIGATION_REVIEW.md` §7: `"mission-control"` and the sidebar's `monitoring` item
both render as "Мониторинг." If both are meant to be the same concept from the user's point of view,
this is correct and consistent, not a bug — flagged for confirmation, not changed pre-emptively.

- **Priority:** P3. **Complexity:** S (verify only).

## 4. Notifications — no dedicated real dictionary sampled this pass

`docs/OPERATIONAL_NOTIFICATIONS.md`'s (CQ-17) real `NotificationBucket` values
(`unread/mentions/warnings/errors/success/jobs/all`) were not found with confirmed Russian labels in
`enterpriseRuNav.ts` or `messages.ts` in this pass. `docs/RUSSIAN_UI_DICTIONARY.md`'s (CQ-30.1)
proposed dictionary did not cover this namespace either.

- **Recommendation:** Уведомления (real, `messages.ts`) is correctly the umbrella term; the six bucket
  labels need a first real Russian pass — suggested: Непрочитанные (unread), Упоминания (mentions),
  Предупреждения (warnings), Ошибки (errors), Успешно (success), Задания (jobs), Все (all) — proposed
  here for the first time, not yet validated against any shipped UI.
- **Priority:** P2. **Complexity:** S.

## 5. Settings — real, adequate, one extensibility note

Real `"settings": "Настройки"` (sidebar, breadcrumb, `messages.ts`) is used consistently everywhere
sampled. The real `owner_flags` item ("Флаги функций" — Feature Flags) is a good, clear, specific term
distinct from general Settings — no finding here, cited as a good example of specific-over-generic
naming other areas of the dictionary should follow.

## 6. Buttons — insufficient real evidence sampled this pass

`RU_QUICK_ACTIONS`' verb-first pattern ("Открыть.../Создать...") is the only real button-adjacent
Russian text confirmed this sprint and is consistently well-formed. A full button-label audit across
every real dialog/form component was not performed — flagged as out of scope for this pass's evidence
base, not claimed as reviewed.

## Non-goals

- No wholesale rewrite of `docs/RUSSIAN_UI_DICTIONARY.md` — §2's one correction (Production Studio
  term) is the only proposed change to that document's prior content.
- No new notification-bucket Russian labels implemented — §4's suggestions are proposals pending
  product review, not finalized translations.

## Related documents

`docs/RUSSIAN_UI_DICTIONARY.md` (CQ-30.1, the prior proposal this review checks against reality),
`docs/SEMANTIC_DICTIONARY.md` (CQ-20, the preferred-term rulings), `src/web/src/i18n/messages.ts`
(real), `src/web/src/navigation/enterpriseRuNav.ts` (real), `docs/UX_AUDIT.md`/`docs/NAVIGATION_
REVIEW.md` (CQ-30.7 siblings, the headline bug this document leads with).
