# External Pilot Guide — Sprint 32.1

## Goal

Onboard the first external pilot organizations onto the completed seven-ecosystem Enterprise Platform.

## Flow

1. Admin opens `/pilot/onboard` → run full onboarding (tenancy + EON + go-live + EPR first-launch).
2. Select a Business Ecosystem workspace from the onboarding page.
3. Open `/pilot/invite` → register/login ecosystem session → create org → create invitation token.
4. Share `/invite/accept?token=…` with the invitee.
5. Invitee registers/logs in and accepts → continues to `/pilot` or `/workspace`.
6. Activate AI Team at `/platform-builder/ai-team`.
7. Validate production probes at `/pilot/production`.

## Surfaces

| Route | Purpose |
|-------|---------|
| `/pilot/onboard` | Organization registration & activation |
| `/pilot/invite` | Owner/user invitations |
| `/invite/accept` | Token redemption |
| `/pilot` | Multi-org + ops dashboard |
| `/pilot/production` | Production / security checklist |

## Rules

No new ecosystems. No duplicated APIs or AI. Reuse Tenancy, EON, EPR, Ecosystem invitations, ISAM, OBS.

## GA overlay (EP-08)

After org activation, walk the owner through:

1. Morning Brief (`/dashboard?mode=executive`)
2. Enterprise City
3. Mission Control → AI Concierge → Control Tower
4. Sign-off via `docs/PILOT_CHECKLIST.md`

Product certification: `docs/ENTERPRISE_PLATFORM_V1_GA.md`.
