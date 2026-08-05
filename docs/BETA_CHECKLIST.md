# Beta Checklist — Sprint 30.6

## Local launch

- [ ] `cd src/web && npm install` (if needed)
- [ ] `npm run lint`
- [ ] `npm test`
- [ ] `npm run build`
- [ ] `npm run dev` — open app

## Smoke path

- [ ] `/login` — sign in (demo / Google)
- [ ] `/dashboard` — Beta Home
- [ ] `/city` — map loads; open district → module
- [ ] `/ai-agents` — create/start task
- [ ] `/production-studio` — Russian CTA / image studio
- [ ] `/health` — CPU/Memory/API probes
- [ ] `/owner` — subsystems list
- [ ] `/demo/scenario` — walk Beta Live Demo steps
- [ ] Unknown URL → `/errors/404` style page
- [ ] `/errors/offline` and `/errors/unauthorized` render

## Roles

- [ ] Owner switcher sees all Owner subsystems
- [ ] Non-owner still reaches City / AI / Production via nav

## Optional staging

- [ ] `PYTHONPATH=. python scripts/ga_staging_smoke.py`
- [ ] `PYTHONPATH=. python scripts/ga_staging_smoke.py --base-url http://127.0.0.1:5173`
