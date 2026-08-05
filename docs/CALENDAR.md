# Calendar — Enterprise Web Module

**Sprint:** 30.8  
**Route:** `/calendar`  
**Code:** `src/web/src/enterprise-business/CalendarModulePage.tsx`

## Surfaces

День · Неделя · Месяц · Встречи · Задачи · Напоминания

## Backend

Platform `CalendarService` (`services/calendar_service.py`) is the canonical service. Web module uses workspace events with the same day/week/month semantics until a general calendar REST is exposed to `src/web`.

## Related

`docs/BUSINESS_CALENDAR.md`
