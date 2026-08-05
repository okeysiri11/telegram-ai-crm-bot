# Platform Boot

**Sprint:** 30.6  
**Code:** `src/web/src/platform-integration/platformBoot.ts`  
**Entry:** `src/web/src/main.tsx` → `App` → `Routes`

## Single entry

```bash
cd src/web && npm run dev
```

Browser: Vite local URL (typically `http://127.0.0.1:5173`).

## Boot surfaces

| Path | Surface |
|------|---------|
| `/` | HomeRedirect → role home |
| `/login` | Authentication (Google + email) |
| `/dashboard` | Beta Home / Dashboard |
| `/city` | Enterprise City |
| `/ai` → `/ai-agents` | AI Agent Center |
| `/production` → `/production-studio` | Production Studio |
| `/settings` | Settings |

Also required: `/crm` · `/erp` · `/analytics` · `/owner` · `/health` · `/demo/scenario`

## Version

`PLATFORM_BOOT_VERSION = "30.6"`

Coverage helper: `assertBootCoverage(registeredPaths)`.
