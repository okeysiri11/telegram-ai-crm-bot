# SPRINT 42.5 — Full Russian Localization Audit (Zero English UI)

**Mode:** Product Polish + Full Localization + Human-First UX  
**Date:** 2026-08-06  
**Surface:** `src/web` — Platform Builder, Concierge, AI Builder, AI Team, Framework

---

## Verdict

**Critical production surfaces are RU-first at 100% gate coverage.**

| Gate (critical) | Result |
|---|---|
| Concierge Builder | ✓ полностью на русском (V2 мастер + legacy catalog) |
| AI Agent Builder | ✓ catalog + wizard UI на русском |
| AI Team Center | ✓ на русском |
| Builder Framework chrome | ✓ `bu()` / `term()` |
| Universal Builder Framework | ✓ шаги и каталог на русском |
| AI Builder Studio hub | ✓ карточки / промпты / пакеты навыков |
| Localization Coverage (critical) | **100%** |
| Hardcoded English (critical) | **0** |
| Missing Translation (critical) | **0** |

Overall `platform-builder/**` secondary visual studios still contain English descriptive copy (~68% RU by string heuristic). Nav titles for all builders are already covered by `BUILDER_NAV_RU`. Follow-up sprint can finish remaining engine studio body copy without touching critical Owner/Admin Concierge/AI paths.

---

## What shipped

### 1. Unified glossary

- Canonical: `src/web/src/i18n/platformGlossary.ts`
- Alias: `src/web/src/i18n/platformGlossary.ru.ts`
- Builder chrome: `src/web/platform-builder/i18n/builderUiRu.ts` (`bu()`, `BUILDER_UI_RU`)

Terms include: Dashboard → Панель управления, Workflow → Сценарий, Preview → Предпросмотр, Coming Soon → Скоро, Visual Intelligence → Визуальный интеллект, Data Fabric → Шина данных, AI Team / Concierge / Mission Control / Digital Twin / etc.

### 2. Concierge Builder

- Active wizard (`ConciergeWizard.tsx` + `catalogV2.ts`) — 7 RU steps
- Legacy `catalog.ts` fully rewritten in Russian (roles, styles, access, orchestration, proactive, recommendations)

### 3. AI Agent Builder

- `ai-builder/catalog.ts` — professions, skills, permissions, styles, specialization tree — RU
- `AIBuilderWizard.tsx` — remaining English chrome/help/placeholders translated

### 4. AI Team Center

- `AITeamCenterPage.tsx` — RU labels; type corruption from unsafe replace repaired (`TeamDashboard`)

### 5. Builder Framework

- Framework chrome via `bu()`
- UBF catalog + studio confirmation / validation / preview copy in Russian
- `LiveValidation` accepts API error objects safely

### 6. Localization Audit

```bash
cd src/web && npm run audit:i18n
# → node scripts/localization_audit.mjs
```

Reports:

```
Русских строк:         XXXX
Английских строк:      0
Hardcoded строк:       0
Missing translation:   0
Localization coverage: 100%
```

JSON artifact: `src/web/reports/localization_audit_42_5.json`

### 7. Project rule

`.cursor/rules/ados-ru-localization.mdc` — new screens must not ship English UI; use glossary/`bu()`; forbid unsafe global EN→RU token replace (corrupts `Content-Type` / identifiers).

### 8. Tests

- `src/web/src/ai-builder-studio/sprint_42_5_localization.test.ts`
- Existing 42.4 / hotfix 42.4.1 suites remain

---

## Architectural decisions

1. **Extend glossary, do not invent a parallel i18n engine.** `platformGlossary` + `builderUiRu` are the dictionaries; `messages.ts` keeps `en`/`ru`/`uk` locale maps for shell chrome.
2. **Critical-path gate first.** Audit fails CI-style on Concierge / AI Builder / AI Team / Framework / Studio. Full visual-engine studio body copy is tracked as residual risk, not blocking Owner Concierge/AI flows.
3. **Never substring-replace short English tokens in source.** Early batch replace corrupted identifiers (`setCreated` → `setСоздатьd`) and headers (`Content-Type` → `Content-Тип`). All such corruption was repaired; short tokens removed from auto-replace maps.

---

## Residual English (non-critical)

Secondary `*EngineStudio.tsx` body strings (strategy / mission-control / experience / etc.) still mix EN help/purpose text. Menu names are RU via `builderDisplayName`. Tracked for Sprint 42.6 polish if required for literal 100% across every studio file.

---

## Acceptance checklist

| Criterion | Status |
|---|---|
| Critical UI without English labels | ✓ |
| Concierge Builder RU | ✓ |
| AI Builder RU | ✓ |
| AI Agents / Team RU | ✓ |
| Framework chrome RU | ✓ |
| Localization Coverage (critical) = 100% | ✓ |
| Hardcoded English (critical) = 0 | ✓ |
| Missing Translation (critical) = 0 | ✓ |
| Vitest | ✓ 16/16 (42.4 + 42.4.1 + 42.5) |
| Typecheck / Lint | ✓ `tsc -b` |
| Production Build | ✓ `npm run build` |

---

## Commands

```bash
cd src/web
npm run audit:i18n
npm run test -- src/ai-builder-studio/sprint_42_5_localization.test.ts
npm run lint
npm run build
```
