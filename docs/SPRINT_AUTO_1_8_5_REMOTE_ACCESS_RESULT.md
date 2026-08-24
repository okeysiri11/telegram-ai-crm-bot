# Sprint AUTO 1.8.5 — Remote web / mobile HTTPS access

## Recovery (20 Aug 2026)

The previous run stopped when the computer lost power. AUTO 1.8.5 code was already in the working tree. This recovery **did not restart AUTO 1.9** and did not rewrite the architecture.

| Requirement | After power loss | After recovery |
|---|---|---|
| Stack precheck / no Vercel project | DONE | unchanged |
| Env-based API URL (`VITE_API_BASE` / `VITE_API_BASE_URL`) | DONE | unchanged — default relative `/api` |
| CORS exact origins + trycloudflare suffix | DONE | verified live ACAO |
| Bind `API_PORT` / platform `PORT` | DONE | unchanged |
| Health `/health` + `/api/auto-ops/v1/health` | DONE | **200 AUTO_1.8.5** |
| Production `src/web/dist` | DONE | reused |
| Same-origin gateway `:4173` | DONE | restarted |
| Mobile drawer / table scroll / file `accept` | DONE | unchanged |
| Tests AUTO 1.0–1.8.5 | DONE | re-run **76 / 30 passed** |
| Local processes | dead after reboot | restored: 1× `main.py`, 1× Vite |
| Public HTTPS URL | stale trycloudflare host | **new live URL** |
| Shutdown script | missing | `scripts/stop_remote_https.sh` |
| Result doc | stale URL | this file |

## Result

The **existing** ADOS Enterprise frontend and backend are reachable from a phone over **verified** public HTTPS URLs. No second frontend, backend, demo clone, or Telegram bot was created.

**TEMPORARY: YES**

Временная ссылка работает только пока компьютер и tunnel process включены.

Computer must remain ON: **YES**

## Public URLs (20 Aug 2026 phone-access fix)

Old URL `https://twist-opposition-outline-ddr.trycloudflare.com` is **DEAD** on this LAN: default DNS (`192.168.20.1`) returned **NXDOMAIN**. `curl -I` without a DNS bypass failed with `Could not resolve host`. That URL must not be reused.

| Role | URL |
|---|---|
| Frontend (open on phone) | https://pulse-pepper-invite-bags.trycloudflare.com |
| Backend | https://maybe-launches-concrete-have.trycloudflare.com |
| Auto ops health | https://maybe-launches-concrete-have.trycloudflare.com/api/auto-ops/v1/health |
| Auto workspace | https://pulse-pepper-invite-bags.trycloudflare.com/workspace/auto |
| Login | https://pulse-pepper-invite-bags.trycloudflare.com/login |

Local (Vite now binds `0.0.0.0:5180`):

- Frontend: `http://127.0.0.1:5180` → **200**
- LAN: `http://192.168.20.103:5180` / `http://192.168.20.102:5180` → **200**
- Backend: `http://127.0.0.1:8080` → **200**
- Auto health: `http://127.0.0.1:8080/api/auto-ops/v1/health` → **200**, `AUTO_1.8.5`

## Architecture

No Vercel / Railway / Fly / Render project exists in this repository. Permanent cloud hosting would **not** share the laptop’s current process memory or local database. After the dead-URL incident, AUTO 1.8.5 uses **two Cloudflare quick tunnels** plus Vite on `0.0.0.0`:

```
phone (HTTPS)
  → https://<frontend>.trycloudflare.com
    → 127.0.0.1:5180  Vite (host 0.0.0.0, allowedHosts *.trycloudflare.com)
         └─ proxy /api /management → 127.0.0.1:8080  (existing API + bot)

phone / health checks
  → https://<backend>.trycloudflare.com
    → 127.0.0.1:8080
```

Frontend API calls stay **relative `/api`** (Vite proxy). The phone never calls `127.0.0.1`. Public verification uses the **system DNS resolver** (no `--resolve` / 8.8.8.8 bypass). Postgres (5432) and Redis are not exposed.

Hosting provider: **Cloudflare Tunnel (quick / trycloudflare.com)**. Database: existing local **Postgres**, Auto ops **memory fallback** when SQL tables are missing.

## Environment variables (no secret values)

| Variable | Purpose |
|---|---|
| `VITE_API_BASE` / `VITE_API_BASE_URL` | Absolute API origin only for split deploy. Default empty → relative `/api`. |
| `ADOS_CORS_ORIGINS` | Comma-separated exact frontend origins. Never `*`. |
| `ADOS_CORS_TUNNEL_SUFFIX` | Default `.trycloudflare.com`. |
| `ADOS_GATEWAY_PORT` | Gateway port (default `4173`). |
| `API_PORT` / `PORT` | Listen port. `API_PORT` wins. |
| `ADOS_MAX_UPLOAD_MB` | Multipart limit (default 32). |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Production Google Sign-In. **Not configured**. |

Do not commit `.env`, `BOT_TOKEN`, DB passwords, JWT secrets, or OAuth secrets.

## Startup (repeatable after reboot)

1. One API + one Telegram poller:

```bash
.venv/bin/python main.py
```

2. Local frontend (optional while tunneling; keep for laptop work):

```bash
npm run dev --prefix src/web -- --host 0.0.0.0 --port 5180
```

3. Public HTTPS (reuses `:8080`, does not start a second bot):

```bash
scripts/start_remote_https.sh
```

Combined local without Telegram polling: `scripts/start_local.sh` / `npm run dev:all`.

## Shutdown

Cloudflare tunnels only (does not kill Vite, API, Telegram, or the database):

```bash
scripts/stop_remote_https.sh
```

Stop local frontend: the Vite process on `:5180`.  
Stop API + Telegram: the single `main.py` process on `:8080`.

## Auth / CORS / Google

- Session is **Bearer JWT in localStorage**. Same-origin HTTPS is enough.
- Live CORS preflight: `204`, `Access-Control-Allow-Origin: https://pulse-pepper-invite-bags.trycloudflare.com`, credentials `true`. No `*`.
- Email / demo login over the public frontend URL: `POST /api/enterprise-demo-auth/v1/login` → **200** for `owner@demo.corp` / `demo`. ISAM identity → **201**.
- Google Sign-In: `GOOGLE_CLIENT_ID` is unset. Use Email login. Google needs the Google Cloud console redirect for this hostname if enabled later.

## Live checks (this recovery)

| Check | Result |
|---|---|
| `GET https://…/` | 200, Enterprise Web Platform HTML |
| `GET https://…/login` | 200 |
| `GET https://…/workspace/auto` | 200 |
| `GET https://…/health` | 200 |
| `GET https://…/api/auto-ops/v1/health` | 200, `AUTO_1.8.5` |
| `GET https://…/api/auto-ops/v1/dashboard` | 200 |
| Photo multipart `POST /api/auto-ops/v1/files` | **201** (backend stored the file) |
| PDF multipart `POST /api/auto-ops/v1/files` | **201** |
| Telegram | one `main.py` poller (`Start polling`) |

## Database / migrations

- `alembic current`: `i8d901234567`
- Outstanding AUTO 1.0–1.6 revisions remain unapplied: AUTO 1.1 `exec_driver_sql(..., %s)` breaks asyncpg (`column "s"`). Upgrade was **not** forced. No tables dropped.
- Auto ops uses Postgres when tables exist, otherwise memory fallback.

## Mobile (already shipped; not redesigned)

- Shell hamburger drawer + Auto **Разделы** drawer (`ops-mobile-nav-toggle`).
- Tables: horizontal overflow wrappers, `.eds-table` min-width.
- File inputs: `accept` for images/PDF/docs. Standard HTML `input type=file`.

## Tests (re-run after recovery)

| Suite | Result |
|---|---|
| Backend AUTO 1.0–1.8.5 | **76 passed / 0 failed** |
| Frontend AUTO 1.0–1.8.5 | **30 passed / 0 failed** |
| Production JS bundle (`npx vite build`) | **PASS** (existing dist reused) |
| `npm run build` (`tsc -b && vite build`) | **FAIL** — pre-existing errors outside Auto |

## Known limitations

1. Tunnel URL changes if Cloudflare quick tunnel restarts.
2. Computer, `main.py` on `:8080`, Vite on `:5180`, and both `cloudflared` processes must stay running.
3. AUTO SQL migrations 1.0–1.6 are not fully applied (asyncpg placeholder bug). Do not stamp the head.
4. Google OAuth is not production-ready without `GOOGLE_CLIENT_ID`.
5. A trycloudflare hostname that NXDOMAINs on the LAN resolver is **dead** even if `cloudflared` is still running. Verification must use system DNS, not `--resolve`.
6. Physical device camera was not used in this environment; uploads were real HTTP multipart to the live backend.

## Architectural decisions

| Decision | Why | Rejected |
|---|---|---|
| Tunnel the **current** local app | Same process, same data | New Vercel app + new Postgres |
| Vite `0.0.0.0:5180` + FE/BE quick tunnels | Phone DNS must resolve; API stays relative `/api` | Treating a running tunnel as live when LAN DNS is NXDOMAIN |
| Keep `main.py` as the only bot | One Telegram instance | Starting `run_api_local.py` beside it |
| Relative `/api` by default | Works for Vite proxy and the tunnel | Hardcoding a production host |

AUTO 1.9 was not started.
