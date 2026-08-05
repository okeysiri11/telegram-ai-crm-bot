# Release Checklist — Closed Beta

**Sprint:** 32.5 · Extends [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md) · [`PILOT_CHECKLIST.md`](./PILOT_CHECKLIST.md)

## Pre-demo

- [ ] `IAM_JWT_SECRET` / secrets set (no placeholders in production)
- [ ] API + Postgres + Redis reachable
- [ ] Web build deployed or `npm run build` green
- [ ] Demo auth policy understood (`VITE_DEMO_AUTH`)

## Functional smoke

- [ ] `/login` — email and/or Google
- [ ] `/auth/register` — registration
- [ ] `/onboarding/first-entry` — wizard completes
- [ ] `/owner` — metrics + God Mode render
- [ ] `/city` — zoom, pan, districts, mini-map, building open
- [ ] Buildings open real modules (CRM, Projects, Knowledge, AI, Security, Production)
- [ ] `/identity/security` — Security Center
- [ ] Command Palette / Search / Notifications / Settings
- [ ] AI Runtime / Agents respond without hard crash

## Quality gates

```bash
cd src/web && npm run lint && npm test && npm run build
./venv/bin/python scripts/architecture_sprint_review.py
```

- [ ] Lint green
- [ ] Unit tests green
- [ ] Build green
- [ ] No critical architecture review failures
- [ ] No dead `#` city routes

## Sign-off

- [ ] Internal demo completed
- [ ] Known limitations reviewed with stakeholders ([`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md))
