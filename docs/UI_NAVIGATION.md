# UI Navigation — Sprint 30.2

**Status:** production · Russian enterprise navigation layer  
**Canonical catalog:** `src/web/src/navigation/enterpriseRuNav.ts`

## Surfaces

| Surface | Module |
|---|---|
| Sidebar | `src/web/src/navigation/Sidebar.tsx` |
| Top bar | `src/web/src/navigation/TopNavigation.tsx` |
| Breadcrumbs | `breadcrumbEngine` + `labelForSegment` |
| Workspace chrome | `GlobalWorkspaceBar.tsx` |
| Router | React Router in `App.tsx` (`/owner`, existing hubs) |

## Primary sidebar (Russian)

Главная · Рабочий стол · Город · AI-Агенты · CRM · ERP · Проекты · Клиенты · Финансы · Документы · Продакшн · Маркетинг · Производство · Юридический отдел · Аналитика · Мониторинг · Настройки

Owner Mode block appears for platform owners / role switcher Owner view.

## Managers (do not fork)

- `navigation/managers/menuEngine.ts`
- `navigation/managers/searchIndex.ts`
- `navigation/managers/navigationManager.ts`
- `shell/enterprise/shellModuleRegistry.ts`
