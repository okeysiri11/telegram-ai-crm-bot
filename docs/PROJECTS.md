# Projects — Enterprise Web Module

**Sprint:** 30.8  
**Route:** `/projects`  
**Code:** `src/web/src/enterprise-business/ProjectsModulePage.tsx`

## Surfaces

Проекты · Канбан · Задачи · Вехи · Таймлайн · Документы проекта · Команда

## Persistence

Workspace-backed until a platform Project entity exists (`docs/PROJECT_LIFECYCLE.md`). Tasks also link to `/tasks` and CRM task APIs where available.

## Navigation

`?view=projects|kanban|tasks|milestones|timeline|documents|team`
