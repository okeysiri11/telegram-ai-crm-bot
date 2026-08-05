# Sprint 27.1.1 — Local Authentication Recovery

## Root cause (verified)

1. Login calls `productionLogin` → `loginViaIsam` → `POST /api/enterprise-isam/v1/*`.
2. Vite proxies `/api` to `http://localhost:8080`.
3. Backend on `:8080` is **not running** → proxy returns **502** (confirmed via curl).
4. Demo token minting was explicitly disabled; no local fallback.
5. Login form had **no try/catch** → Sign in failed silently.

Not a React Router bug, not cookies, not CORS (same-origin proxy).

## Fix

- **Demo Auth Provider** (`src/auth/demoAuthProvider.ts`) — JWT for `*@demo.corp` / password `demo`.
- **Vite middleware** (`vite.demoAuthPlugin.ts`) — `POST /api/enterprise-demo-auth/v1/login`.
- **`productionLogin`** — if ISAM unreachable and demo auth on → Demo Auth API → in-process provider.
- **Login UI** — error banner; local demo skips first-entry → **Dashboard**.
- **`.env.development`** — `VITE_DEMO_AUTH=true`.

## Credentials

`owner@demo.corp` / `demo` · tenant `demo-corp`

## Verify

```bash
cd src/web
npm install
npm run dev
# open http://localhost:5180/login → Sign in → /dashboard
```
