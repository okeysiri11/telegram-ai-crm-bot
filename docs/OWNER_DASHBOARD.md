# Owner Dashboard — Sprint 30.2 / 30.3 / 30.8

**Route:** `/owner`  
**Page:** `src/web/src/navigation/OwnerDashboardPage.tsx`

## Live metrics (Sprint 30.8)

`deriveOwnerMetrics()` reads real platform state:

| Card | Source | Route |
|------|--------|-------|
| Пользователи | Identity | `/identity/users` |
| Организации | Identity | `/identity/organizations` |
| AI-агенты | `aiAgentRuntime` + `DEFAULT_AGENTS` | `/ai-agents` |
| CRM | `crmApi` cache | `/crm` |
| Проекты | projects workspace | `/projects` |
| Runtime | `derivePlatformHealth` | `/platform-builder/runtime` |
| Здоровье | Platform Health | `/health` |
| Уведомления | `notificationStore` | `/notifications` |
| Активность | activity journal | `/identity/activity` |
| Статус системы | health level | `/health` |

Plus Knowledge / Drive / Calendar / Marketplace counts.

## Owner Mode nav

`OWNER_RU_NAV` remains the navigation source of truth. Subsystems grid: `OWNER_SUBSYSTEMS`.
