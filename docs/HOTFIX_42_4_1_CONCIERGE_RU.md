# Hotfix 42.4.1 — Complete Russian Localization of Concierge Builder

**Status:** COMPLETE  
**Date:** 2026-08-06  
**Scope:** Concierge Builder page chrome + Platform Builder navigation (shared layout)

---

## Problem

After Sprint 42.4, `/platform-builder/concierge` still showed English labels in the shared **Platform Builder** navigation (from `BUILDER_CATALOG.name`), because only a short `MENU_NAME_RU` map existed.

---

## Fix

1. Expanded **`BUILDER_NAV_RU`** in `src/web/src/i18n/platformGlossary.ts` — every `BUILDER_CATALOG` id has a Russian display name.
2. Expanded **`EN_TO_RU_LABEL`** for the titles listed in the hotfix brief (and related hubs).
3. Added **`builderDisplayName(id, englishName)`** — single source for menu / dashboard cards.
4. **`PlatformBuilderLayout`** always renders `builderDisplayName` (no English fallback to catalog `name`).
5. **`PlatformBuilderDashboard`** uses the same helper.
6. **`HelpPanel`** badges → словарь (`Назначение`, `Польза`, …).
7. **`helpFor` / `ACADEMY_MODES`** → Russian.
8. Concierge V2 modules: `Drone`→`БПЛА`, `Travel`→`Туризм`; language option `English`→`Английский`.

---

## Concierge Builder page (acceptance)

| Surface | Status |
|---------|--------|
| Page title / subtitle | RU |
| Wizard steps / chips / buttons | RU |
| Live preview | RU |
| Shared builder nav (all buttons) | RU via `BUILDER_NAV_RU` |
| Preview / Coming soon badges | RU |

Allowed acronyms left as-is: **AI**, **CRM**, **ERP**, **API**, **OKR**, **Crypto OTC** (product brand).

---

## Automated scan — remaining English UI in `platform-builder/`

Scan of `platform-builder/**/*.tsx` for English UI word patterns (Builder, Dashboard, Engine, Create, …).  
**Concierge path is clean.** Remaining English is on **other** builder studios (not Concierge):

| File area | Approx. EN UI leftovers |
|-----------|-------------------------|
| `academy-v2/AcademyV2Studio.tsx` | Titles, learning mode, summary |
| `ai-team/AITeamCenterPage.tsx` | Center title, empty states |
| `ai-builder/AIBuilderWizard.tsx` | Some step body strings (`Preview conversation`, …) |
| `vertical/VerticalWizard.tsx` | Title, learning mode, create CTA |
| `ubf/UniversalFrameworkStudio.tsx` | Framework chrome |
| `collaborative-ai/*`, `command-center/*`, `digital-twin/*`, `director/*`, `experience/*`, `god-mode/*`, `intelligence/*`, `mission-control/*`, `navigation-intelligence/*`, `operations/*`, `rendering/*`, `simulation/*`, `story/*`, `strategy/*`, `team-map/*`, `themes/*`, `twin-intelligence/*`, `visual-behavior/*`, `workflow-intelligence/*`, `workspace-os/*`, `assets/*`, `business-ecosystem/*` | Page titles / create CTAs still EN |
| `framework/BuilderFramework.tsx`, `ConfirmationScreen.tsx`, `PreviewWindow.tsx` | Shared EN chrome |
| `pages/FrameBuilderPage.tsx` | Preview frame copy |

**Total scan hits:** ~270 English UI string occurrences across ~35 non-Concierge files (deduped by file+string).

Full machine list can be regenerated:

```bash
cd src/web && python3 scripts/scan_builder_en_ui.py   # or the inline scan used in this hotfix
```

---

## Tests

- `src/web/src/ai-builder-studio/hotfix_42_4_1_ru_nav.test.ts`  
  — every catalog id mapped; listed English titles localize without leftover EN words.

---

## Recommendation

Concierge Builder **READY** for Russian commercial demo.  
Next polish sprint: batch-localize remaining `*Studio.tsx` / Vertical / Academy pages using the same `BUILDER_NAV_RU` + glossary pattern.
