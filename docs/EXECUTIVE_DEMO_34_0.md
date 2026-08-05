# Executive Demo Scenario — Enterprise Platform v1.0 GA

**Updated:** EP-08 (2026-07-27) · Sprint label 34.0 / PB 1.66.0  
**Duration:** ~20–35 minutes  
**Route:** `/demo/scenario`

## Preconditions

- Demo tenant available (`owner@demo.corp` / demo password as configured)
- Role: Owner or Executive
- Browser: desktop (wide preferred)

## Canonical script (GA)

| # | Step | Route | Talk track |
|---|------|-------|------------|
| 1 | Login | `/login` | Secure enterprise entry |
| 2 | Org · First Entry | `/onboarding/first-entry` | Role → company → ready (AI defaults applied) |
| 3 | Morning Brief | `/dashboard?mode=executive` | Observation · Attention · Recommendation · Risks · Opportunities |
| 4 | Dashboard | `/dashboard?mode=executive` | Decision Flow · Continue strip |
| 5 | Enterprise City | `/enterprise-city` | Company map · one-glance health |
| 6 | Mission Control | `/platform-builder/mission-control` | Live ops pulse |
| 7 | AI Concierge | `/platform-builder/concierge` | Advisor: Observation / Why / Action / Impact |
| 8 | Control Tower | `/platform-builder/control-tower` | Owner decide-now |
| 9 | Settings | `/settings` | Notifications · preferences · profile |
| 10 | Logout | `/auth/logout` | Safe sign-out |

## Optional deep-dives (after core path)

- AI Team · Marketplace · Builder Studio · Digital Twin
- Autonomy HITL · OKR · Learning · Runtime · Data Fabric
- Governance: `/platform-builder/governance`

## Success criteria

- Every mandatory step loads without Error Boundary
- Strips collapsed by default (first viewport calm)
- Advisor recommendations use Observation / Why / Action format
- Continue strip moves context between Brief / City / Concierge / Control Tower
- Visual impression: EDL + City + calm motion

## Related

- [ENTERPRISE_PLATFORM_V1_GA.md](./ENTERPRISE_PLATFORM_V1_GA.md)
- [PILOT_CHECKLIST.md](./PILOT_CHECKLIST.md)
- [GA_READINESS_REPORT.md](./GA_READINESS_REPORT.md)
