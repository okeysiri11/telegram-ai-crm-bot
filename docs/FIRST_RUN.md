# First Run

**Sprint:** 31.0 Closed Beta (extends 32.3.1 / 30.3)  
**Route:** `/onboarding/first-entry`  
**Store:** `src/web/src/onboarding/firstEntryStore.ts`

## Mandatory steps

1. **Welcome** — platform introduction  
2. **Role** — platform roles (Владелец, Администратор, Менеджер, Сотрудник, Клиент, …) + vertical roles  
3. **Workspace** — organization name, industry, team size, language (default `ru`), timezone, currency  
4. **Ready** — confirm → create workspace (Tenancy API + local workspace store) → role home  

Optional AI Team / Concierge steps remain in catalog but are skipped in the mandatory UX path (defaults applied).

## After finish

| First-entry role | Landing |
|------------------|---------|
| business_owner / executive | `/owner` |
| administrator | `/admin` |
| manager | `/dashboards/manager` |
| employee | `/dashboards/employee` |
| client | `/dashboards/client` |
| auto / dealer | `/dashboards/dealer` |
| vertical ecosystems | `/workspace/<vertical>` when set |

Language selection updates prefs + i18n locale.

## Triggers

Google login, email registration, invitation join when `completed !== true` (`postAuthDestination`).
