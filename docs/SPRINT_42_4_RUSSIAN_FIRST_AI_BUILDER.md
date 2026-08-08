# Sprint 42.4 — Russian-First Platform & AI Builder Redesign

**Status:** COMPLETE  
**Mode:** Product polish · Russian localization · Human UX  
**Date:** 2026-08-06  

---

## Goal

Fully Russianize ADOS builder surfaces, unify terminology, and redesign AI Builder / AI Concierge into clear step-by-step setup wizards that a non-technical user can finish in under 5 minutes.

---

## Delivered

| # | Requirement | Result |
|---|-------------|--------|
| 1 | Russian localization of Builder / Concierge / Studio chrome | Concierge 2.0, Studio hub, Platform Builder dashboard & layout, agent wizard chrome — RU |
| 2 | Platform glossary | `src/web/src/i18n/platformGlossary.ts` — единый словарь (Dashboard→Панель управления, Workflow→Сценарий, …); acronyms AI/CRM/ERP/API kept |
| 3 | AI Concierge Builder 2.0 | 7-step RU wizard: имя → роль → стиль → навыки → модули → права → тест + live preview |
| 4 | AI Builder hub | **Four** large cards: Консьерж · Команда AI · Настройки · Интеграции |
| 5 | AI Agent Builder | Wizard steps & nav RU; create/preview/back/next localized |
| 6 | Owner / Client split | Unchanged ACL: `/platform-builder*` blocked for client/manager; `/ai-agents` allowed for client assistants |
| 7 | Unified visual | `.pb-hub-card`, `.pb-chip`, `.pb-wizard-grid` shared across Platform Builder + Studio |
| 8 | Commercial demo readiness | Concierge path: open → 7 steps → test dialog → Готово |

---

## Concierge Wizard 2.0 steps

1. Имя и образ (имя, аватар, голос, язык, приветствие)  
2. Роль  
3. Стиль общения  
4. Навыки  
5. Модули платформы  
6. Права  
7. Тестовый диалог  

Changes apply instantly in the right-hand **Предпросмотр**.

---

## AI Builder hub cards

| Card | Action |
|------|--------|
| 🤖 AI Консьерж | `/platform-builder/concierge` |
| 👥 Команда AI | Studio → мастер агента |
| ⚙ Настройки платформы | `/settings` |
| 🔌 Интеграции | Studio → интеграции |

---

## Architectural decisions

| Decision | Why | Rejected |
|----------|-----|----------|
| Extend Concierge + Studio in place | Preserve session APIs / routes | New `ai-builder-ru` package |
| Concierge V2 catalog (`catalogV2.ts`) + map to legacy API | Backend contract unchanged | Breaking API rewrite |
| Keep agent wizard 10 internal steps with RU labels | Avoid breaking step index logic | Full 9-step rewrite in same sprint |
| Glossary module separate from `messages.ts` | Shared by builders without bloating i18n store | Only ad-hoc string replace |

---

## Key files

- `src/web/src/i18n/platformGlossary.ts`  
- `platform-builder/concierge/catalogV2.ts`  
- `platform-builder/concierge/ConciergeWizard.tsx`  
- `src/web/src/ai-builder-studio/AIBuilderStudioPage.tsx`  
- `src/web/src/ai-builder-studio/studioCatalog.ts`  
- `platform-builder/pages/PlatformBuilderDashboard.tsx`  
- `platform-builder/layouts/PlatformBuilderLayout.tsx`  
- `platform-builder/ai-builder/catalog.ts` · `AIBuilderWizard.tsx`  
- `src/web/src/ai-builder-studio/russian_first_42_4.test.ts`  

---

## Demo script (&lt; 5 min)

1. Login `owner@ados.demo` / `demo`  
2. Open **Конструктор платформы** → карточка **AI Консьерж**  
3. Пройти 7 шагов, проверить предпросмотр  
4. На шаге «Тестовый диалог» написать сообщение → получить ответ  
5. Нажать **Готово**  
6. Вернуться в Студию AI — четыре крупные карточки  

---

## Acceptance

| Criterion | Status |
|-----------|--------|
| Builder UI Russianized (hub / concierge / studio / wizard chrome) | ✔ |
| No EN/RU mix on redesigned surfaces | ✔ (deeper catalog help text still EN in places — follow-up) |
| AI Builder is card hub + wizards | ✔ |
| Concierge setup without docs | ✔ |
| Unified builder visual language | ✔ |
| Owner/Dev see builders; Client does not | ✔ |
| Feels like commercial SaaS setup | ✔ for Concierge path |

**Residual (next polish):** full RU pass on `platform-builder/*/catalog.ts` help strings (PROFESSIONS, SKILLS help paragraphs), HelpPanel English bodies, remaining builderRegistry English names for niche hubs.

**Recommendation:** READY for Concierge commercial demo; NEEDS POLISH for 100% catalog string coverage.
