# Pilot Report — Sprint 30.6

## Completed workflow

**Automotive first live workflow** — executable at `/workspace/auto`.

## Execution

| Metric | Value |
|--------|-------|
| Steps | 10 (portal auth → OBS) |
| Measured | Wall-clock ms shown in UI after run |
| Staff auth | ISAM (+ JWT if configured) |
| Customer auth | Auto portal register/login |

## Errors / warnings

| Item | Notes |
|------|-------|
| JWT optional | Without `VITE_IAM_LOGIN_SECRET`, ISAM tokens used (still non-demo) |
| Concierge create | Workflow uses session + preview + NBA context; full Concierge registry create remains optional |
| Mission Control activity | Read/probe of existing streams (no parallel activity store) |

## Missing functionality (deferred, not blockers for internal pilot)

- Deep Automotive inventory UI forms  
- Real email delivery beyond Comms Center registration  
- External customer onboarding beyond portal engine  

## Improvement opportunities

1. Wire portal Bearer into subsequent customer-scoped portal calls  
2. Persist workflow run history in OBS dashboard type `business`  
3. Automotive OpenAPI freeze for portal contracts  

## Next ecosystems

See [NEXT_ECOSYSTEM_READINESS_30_6.md](./NEXT_ECOSYSTEM_READINESS_30_6.md) — readiness only, no implementation.
