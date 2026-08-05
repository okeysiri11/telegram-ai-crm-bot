# UI Architecture

## Layers

```
platform_console/
  src/
    App.tsx                 # Routes only
    layouts/ControlShell.tsx
    context/RuntimeContext.tsx
    hooks/
      useLiveRuntime.ts     # REST poll 2s + WS invalidate
      useRuntimeSocket.ts
    services/runtimeApi.ts  # Typed Runtime client
    components/
      StatusCard.tsx
      layout/Sidebar.tsx
      layout/TopNav.tsx
    pages/                  # One route = one capability view
```

## Data flow

1. `ControlShell` mounts `useLiveRuntime()`.
2. Context shares live queries with all pages.
3. Pages render Runtime DTOs only — no local fixture data for Kernel/Runtime cards.
4. Mutations (restart, run workflow, …) call Runtime POST and invalidate queries.

## Extension points

| Future module | UI surface | Runtime surface |
|---------------|------------|-----------------|
| Memory Engine | Knowledge page | `GET /knowledge` (add later) |
| Agent Factory | AI Agents | `GET /agents` (live today) |
| Plugin Store | Marketplace | Mesh-registered marketplace service |
| Vertical CRM/ERP | New nav item | New Runtime routes; Kernel stays free of business logic |

## Rules

- Prefer composing Design System tokens in `index.css` over new CSS frameworks.
- Keep pages thin; put HTTP in `runtimeApi`.
- Never import `@ados/kernel` from the browser bundle.
