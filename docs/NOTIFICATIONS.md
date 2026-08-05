# Notifications — Enterprise Web Module

**Sprint:** 30.8  
**Route:** `/notifications`  
**Code:** `src/web/src/enterprise-business/NotificationsModulePage.tsx`  
**Store:** `src/web/src/notifications/notificationStore.ts`

## Surfaces

Входящие · Активность · История · Непрочитанные · Приоритет · Read/Unread

## API binding

Optional hydrate from `/api/enterprise-comms/v1/center` (see `NOTIFICATION_CENTER.md`). Extends existing store — no parallel notification engine.
