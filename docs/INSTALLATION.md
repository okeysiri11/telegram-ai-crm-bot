# Installation — Closed Beta / Local Launch

**Sprint:** 31.0 RC · extended by **32.6A** Local Launch Recovery

## Prerequisites

- Node **20+** (Enterprise Web on port **5180**)
- Python **3.11+** + `venv` (API on **8080**)
- PostgreSQL (local or Docker)
- Redis optional locally (`REDIS_REQUIRED=false`)
- Docker Compose **optional** (starts Postgres+Redis when available)

## One-command local demo (recommended)

```bash
# once
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
cp -n .env.example .env   # set JWT_SECRET / DATABASE_URL
npm install --prefix src/web

# every day
npm run dev:all
```

Open http://127.0.0.1:5180/login — `owner@demo.corp` / `demo`.

Full procedure: [`LOCAL_RUN.md`](./LOCAL_RUN.md) · report: [`FIRST_LOCAL_RUN_REPORT.md`](./FIRST_LOCAL_RUN_REPORT.md)

## Web only (demo auth)

```bash
cd src/web
npm ci
npm run dev
# http://localhost:5180 — demo auth on in DEV
```

## Local quality gates

```bash
cd src/web
npm run lint && npm test && npm run build
```

## Production-ish

1. Copy `.env.example` → `.env.production` and set secrets  
2. `cd src/web && npm run build`  
3. `docker compose -f docker-compose.prod.yml up -d --build`  

## First user

1. Open `/login`  
2. Google or email (or demo credentials)  
3. Complete `/onboarding/first-entry`  
4. Land on role dashboard (`/owner`)  

Details: [FIRST_RUN.md](./FIRST_RUN.md) · [CLOSED_BETA.md](./CLOSED_BETA.md) · [CLOSED_BETA_GUIDE.md](./CLOSED_BETA_GUIDE.md)
