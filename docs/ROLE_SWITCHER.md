# Role Switcher — Sprint 30.2

**Store:** `src/web/src/navigation/roleSwitcherStore.ts`  
**Options:** `ROLE_SWITCHER_OPTIONS` in `enterpriseRuNav.ts`

## Roles (Russian UI)

| Id | Label |
|---|---|
| owner | Владелец |
| administrator | Администратор |
| manager | Менеджер |
| employee | Сотрудник |
| dealer | Дилер |
| partner | Партнёр |
| client | Клиент |
| viewer | Наблюдатель |

## Behavior

- Top bar select persists to `localStorage` (`ewp_role_switcher_v1`)
- Owner Mode sidebar visible when `activeRoleId === "owner"` or platform owner
- Complements (does not replace) auth `roleId` / First Entry role catalog
- Global workspace bar shows the switched role label
