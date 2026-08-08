# SPRINT 42.6 — Remove Duplicate Top Navigation Strip

**Mode:** Human-First UX + Declutter + Simplicity  
**Date:** 2026-08-06  
**Surface:** `src/web` Application Shell (`FullLayout`)

---

## Verdict

Горизонтальная полоса вкладок рабочей области (**WorkspaceTabBar** / `.ews-tabbar`) **удалена из рабочего интерфейса** для Owner, Admin, Manager и Client. Контент поднимается выше без пустого резерва. Developer может включить техническую панель **только вручную**.

---

## Проблема

На главном экране под шапкой накапливалась белая полоса вкладок (Owner, AI Studio, Dashboard, CRM, Platform Builder, Concierge…), дублирующая левое меню и съедающая вертикальное пространство.

---

## Что изменено

### 1. Gate в `FullLayout`

Файл: `src/web/src/layouts/FullLayout.tsx`

- Было: `WorkspaceTabBar` для всех, кроме client/manager.
- Стало: показ только если `viewMode === "developer"` **и** пользователь включил preference.

```ts
shouldShowWorkspaceTabBar(viewMode, tabChromeEnabled)
// → developer && enabled
```

`useWorkspaceRouteSync()` **сохранён** — маршруты, состояние вкладок и горячие клавиши не ломаются; меняется только видимость chrome.

### 2. Developer opt-in store

Файл: `src/web/src/workspace-engine/workspaceTabChromeStore.ts`

- Ключ: `ewp_workspace_tab_chrome_v1` (slot-scoped)
- Default: **OFF**
- API: `enabled` / `setEnabled` / `shouldShowWorkspaceTabBar`

### 3. Переключатели (только Developer)

| Место | Назначение |
|---|---|
| Настройки → «Техническая панель вкладок» | полный Switch + подсказка |
| Header рядом с Dev-ролью | короткий Switch «Вкладки» |

Owner / Admin / Manager / Client **не видят** ни полосу, ни переключатель.

### 4. Вертикальное пространство

- Компонент не монтируется → нет margin/padding `.ews-tabbar`.
- CSS safety: `.ews-shell[data-workspace-tabs="0"] .ews-tabbar { display:none; height:0; … }`

### 5. Аналогичные полосы (аудит)

| Компонент | Решение |
|---|---|
| **WorkspaceTabBar** | Убрана из prod-ролей (этот спринт) |
| **WorkspaceQuickDock** (Избранное) | Оставлена — пользовательские избранные модули, не накопленные «вкладки истории» |
| **AIBuilderStudioStrip** | Только Ops Center — не главная |
| **PlatformBuilderLayout** chips | Контекстная навигация конструктора — не дубль главного меню |
| **GlobalWorkspaceBar** | Не смонтирован |

---

## Architectural decisions

1. **Скрыть chrome, не удалять tab engine.** Состояние вкладок и sync маршрутов остаются — Developer может включить панель без потери данных.
2. **Двойной gate:** роль `developer` + явный toggle. Даже в Developer Mode полоса **не** показывается по умолчанию.
3. **QuickDock не трогали.** Это избранное (Sprint 42.0), а не дубль истории вкладок.

---

## Acceptance

| Criterion | Status |
|---|---|
| Белая полоса вкладок убрана у Owner/Admin/Manager/Client | ✓ |
| Нет пустого резерва | ✓ |
| Рабочая область выше | ✓ |
| Навигация (sidebar, routes, sync, hotkeys) | ✓ сохранена |
| Developer включает вручную | ✓ Settings + header |
| Vitest | ✓ 4/4 (`sprint_42_6_tab_chrome.test.ts`) |
| Typecheck / Lint | ✓ `tsc -b` |
| Production Build | ✓ `npm run build` |

---

## Commands

```bash
cd src/web
npm run test -- src/workspace-engine/sprint_42_6_tab_chrome.test.ts
npm run lint
npm run build
```

---

## Files

- `src/layouts/FullLayout.tsx`
- `src/workspace-engine/workspaceTabChromeStore.ts`
- `src/workspace-engine/index.ts`
- `src/workspace-engine/sprint_42_6_tab_chrome.test.ts`
- `src/preferences/InterfaceSettingsPanel.tsx`
- `src/multi-role/DevRoleSwitcher.tsx`
- `src/i18n/messages.ts`
- `src/shell/enterprise/enterpriseShell.css`
- `docs/SPRINT_42_6_REMOVE_DUPLICATE_TOP_NAVIGATION.md`
