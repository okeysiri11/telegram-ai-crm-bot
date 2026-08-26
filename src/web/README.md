# Enterprise Web Platform

**Version:** `9.5.0`  
**Sprint label:** 27.1 / 27.1.1 — Application Shell + Local Auth Recovery  
**Design path:** `src/web`  
**Shell:** `src/shell/enterprise/`  
**Auth:** ISAM when online · Demo Auth Provider when `:8080` is down (`VITE_DEMO_AUTH`)

React 19 · TypeScript · Vite · Tailwind · TanStack Query · React Router · Zustand · RHF · Zod · Chart.js · Socket.IO

## Quick start

```bash
cd src/web
npm install
npm run dev      # http://localhost:5180
# Login: owner@ados.demo → /owner
npm run build
```

Local auth recovery notes: `docs/SPRINT_27_1_1_AUTH_RECOVERY.md`  
Shell notes: `docs/SPRINT_27_1_RESULT.md`
