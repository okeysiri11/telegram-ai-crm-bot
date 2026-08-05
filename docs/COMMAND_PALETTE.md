# Command Palette

**Sprint:** 30.7  
**Hotkey:** Ctrl+K / Cmd+K (also Ctrl+P family via Command Center)

## Implementation

| Piece | Path |
|-------|------|
| Provider / hotkeys | `src/web/command-center/components/CommandCenterProvider.tsx` |
| UI | `UniversalCommandPalette.tsx` (Russian placeholders) |
| Catalog | `command-center/managers/quickActions.ts` → `COMMAND_CATALOG` |
| Nav seeds | `navigation/managers/commandPalette.ts` |

## Required actions (wired)

| Action | Route |
|--------|-------|
| Открыть модуль | `/search` |
| Открыть клиента | `/crm?view=clients` |
| Открыть проект | `/projects` |
| Открыть AI-агента | `/ai-agents` |
| Глобальный поиск | `/search` |
| Открыть город | `/city` |
| Создать задачу | `/tasks` |
| Панель владельца / админа | `/owner`, `/admin` |

## Modes

- **Palette** — command list + search
- **Omnibox** — cross-module search
- **AI** — natural-language intents over the same catalog

All visible labels in the catalog are Russian for Beta.

## Related

[ENTERPRISE_NAVIGATION.md](./ENTERPRISE_NAVIGATION.md) · [WORKSPACE.md](./WORKSPACE.md)
