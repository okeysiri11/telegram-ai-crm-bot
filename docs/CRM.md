# CRM — Enterprise Web Module

**Sprint:** 30.8 (Enterprise Business Modules track)  
**Route:** `/crm`  
**Code:** `src/web/src/enterprise-business/CrmModulePage.tsx`, `crmApi.ts`

## Surfaces

Клиенты · Компании · Контакты · Лиды · Сделки · Воронка · Активность · Заметки · Вложения

## API binding

Primary: `/api/auto/v1/crm/*` (Auto Marketplace CRM Engine — customers, leads, deals, pipeline).

On API failure: tenant-scoped workspace cache (`persist.ts`) — no fake seed data.

## Related (do not confuse)

- `docs/CRM_ENGINE.md` — Auto CRM engine
- `docs/CITY_CRM.md` — City research notes
- Vertical CRMs: `AUTO_CRM.md`, `DEALER_CRM.md`, `AGRO_CRM.md`
