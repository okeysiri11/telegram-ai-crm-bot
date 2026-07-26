# Rollback Checklist — Sprint 32.2

1. Confirm ERL health: `GET /api/enterprise-erl/v1/health`
2. Stop accepting new external onboardings (`/pilot/onboard` soft-close)
3. Preserve feedback + metrics local exports if needed
4. Redeploy previous Platform Builder image / commit (`1.41.0` / 32.1)
5. Verify Mission Control + seven workspace health probes
6. Re-open onboard after health green

No schema migrations required for 32.2 thin UI.
