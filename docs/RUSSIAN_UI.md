# Russian UI — Sprint 30.2

**Default locale:** `ru` (`webConfig.defaultLocale`)  
**Messages:** `src/web/src/i18n/messages.ts`  
**Dictionary reference:** `docs/RUSSIAN_UI_DICTIONARY.md`

## Principle

Chrome and navigation surfaces ship Russian-first. Language selector (Русский / English / Українська) remains in the top bar for future i18n expansion; default session language is Russian.

## Localized chrome

- Sidebar primary menu + Owner Mode
- Top bar: search, company, language, role, notifications, AI assistant, profile
- Breadcrumbs via `BREADCRUMB_LABEL_RU`
- Quick switch chips
- Quick actions panel
- Shell quick actions / search seed titles
- Owner dashboard

## Namespaces added

`nav.*` · `org.*` · `role.*` · `qa.*` · `search.*` · `uws.*` · expanded `common.searchPlaceholder`
