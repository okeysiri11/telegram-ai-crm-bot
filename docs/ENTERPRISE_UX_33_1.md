# Enterprise UX Architecture — Sprint 33.1

**Track:** Enterprise UX Revolution (Foundation)  
**Scope:** Frontend only — navigation, IA, workflows, presentation.  
**No** backend / API / business-logic changes.

## Vision

Make ADOS understandable in the first 5 minutes via **Simple Mode** (default), role workspaces, context navigation, AI command palette, and an executive dashboard.

## Layers

```
TopNavigation (Simple|Pro + Role Workspace)
        ↓
Sidebar (Simple allowlist | Pro full | Context subtree)
        ↓
UniversalCommandPalette (Ctrl+K + AI intents)
        ↓
Routes (unchanged App.tsx modules)
```

Package: [`src/web/src/ux-revolution/`](../src/web/src/ux-revolution/)

| Module | Responsibility |
|--------|----------------|
| `experienceModeStore` | Simple / Pro persistence |
| `simpleModeNav` | Allowlist of 10 primary items |
| `roleWorkspaceCatalog` | 8 enterprise personas |
| `moduleContextNav` | Module-scoped left menus |
| `aiNavigationIntents` | Deterministic phrase → route |
| `ExecutiveSummaryDashboard` | Default Simple home |
| `SimpleProModeToggle` / `RoleWorkspaceSelector` | Chrome controls |

## Compatibility

- Pro Mode restores full prior navigation (RU sidebar, Owner, shell catalog).
- Deep links to Pro modules still work in Simple Mode (nav hide only).
- Existing dashboards available via `?mode=full` or Pro Mode.
