# Sprint 27.2 — Enterprise Navigation & Module Activation

**Phase:** 2 — Functional Navigation Platform  
**App:** `src/web` · version `9.5.0` · sprint `27.2`

## Pages created

| Route | Page |
|-------|------|
| `/crm` … `/security`, `/city` | `EnterpriseModulePage` hubs |
| `/search` | `SearchWorkspacePage` |
| `/` | Restores last module (`HomeRedirect`) |
| `/dashboard` | + Platform Pulse panel |

## Routes activated

`/`, `/dashboard`, `/crm`, `/erp`, `/projects`, `/ai-studio`, `/ai-agents`, `/knowledge`, `/documents`, `/analytics`, `/marketplace`, `/automation`, `/integrations`, `/security`, `/city`, `/settings`, `/search`

Legacy `/workspace/*` and `/platform-builder/*` remain as deep links from hub quick actions.

## Fixed / activated UI

- Left sidebar → clean URLs + active highlight
- Header Search → palette or `/search`
- Alerts → opens Activity Center
- User menu → Profile / Security / Settings / Logout
- Theme · Settings buttons
- Dashboard module cards → hub routes
- Breadcrumb labels for new segments
- Last module persisted (`ews_last_module_v1`)

## Temporary / local data

- Platform Pulse probes (offline when `:8080` down)
- Activity Center seed feed
- Module “recent actions” catalog copy
- Enterprise City hub = Coming Soon (preview via `/enterprise-city`)

## Verify

```bash
cd src/web
npm install
npm run lint    # OK
npm test        # 71 passed
npm run build   # OK
npm run dev     # http://localhost:5180
```

Manual: login → click every sidebar item → hubs open with actions → Search / Alerts / Theme / User menu / Settings work.
