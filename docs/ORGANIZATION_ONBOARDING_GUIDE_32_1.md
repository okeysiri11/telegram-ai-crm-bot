# Organization Onboarding Guide — Sprint 32.1

## Steps (API-backed)

1. **Organization registration** — `POST /api/enterprise-tenancy/v1/onboarding`
2. **Activation / wizard** — `POST /api/enterprise-eon/v1/wizard` (start + advance)
3. **Initial configuration** — `POST /api/enterprise-eon/v1/config`
4. **Readiness** — `GET /api/enterprise-eon/v1/readiness?wizard_id=…`
5. **Go-live** — `POST /api/enterprise-eon/v1/go-live`
6. **First launch** — `POST /api/enterprise-epr/v1/first-launch`
7. **Workspace / ecosystem selection** — existing `/workspace/*` live workflows
8. **Invitations** — `POST /api/ecosystem/v1/organizations/invitations`
9. **Role assignment** — ecosystem roles + `/identity/roles`
10. **AI Team activation** — `/platform-builder/ai-team`

UI: `/pilot/onboard` executes steps 1–6; links cover 7–10.
