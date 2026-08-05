# Pilot Checklist — Enterprise Platform v1.0 GA

**Use with:** [ENTERPRISE_PLATFORM_V1_GA.md](./ENTERPRISE_PLATFORM_V1_GA.md) · [EXTERNAL_PILOT_GUIDE_32_1.md](./EXTERNAL_PILOT_GUIDE_32_1.md)  
**Date:** 2026-07-27

---

## A. Pre-flight (admin)

- [ ] Staging / pilot env deployed (API + `src/web` dist)
- [ ] Env secrets reviewed (auth, DB, integrations)
- [ ] Health probes green (`/pilot/production` score ≥ 90)
- [ ] Demo tenant or pilot org created
- [ ] Owner invited / First Entry not blocked

## B. Client journey (owner)

- [ ] Login (`/login`) — demo or pilot identity
- [ ] First Entry — role → company → ready (≤ 2 min)
- [ ] Lands on Dashboard / Morning Brief
- [ ] Morning Brief readable: Observation · Attention · Recommendation
- [ ] Enterprise City loads; building states understandable
- [ ] Mission Control shows live / last-good health
- [ ] AI Concierge returns Advisor-format suggestions
- [ ] Control Tower: at least one decide-now action
- [ ] Settings: language / notifications reachable
- [ ] Offline banner / Error Boundary recovery understood (optional drill)

## C. Commercial demo

- [ ] Open `/demo/scenario`
- [ ] Walk GA steps in order (20–35 min)
- [ ] Use Continue strip at least once (Brief → City or Concierge)
- [ ] Pitch: “company in 10 seconds · decide in one click”
- [ ] Optional deep-dive: Twin / Marketplace / Builder Studio

## D. Ops acceptance

- [ ] No ErrorBoundary on mandatory path
- [ ] Live poll quiet when tab hidden
- [ ] Production logging present (`[EWP]` in console on failures only as expected)
- [ ] Accessibility: keyboard to primary CTAs; Reduce Motion respected if OS set
- [ ] Feedback captured for Roadmap 2.0 (not GA blockers)

## E. Sign-off

| Role | Name | Date | OK |
|------|------|------|----|
| Pilot owner | | | ☐ |
| Platform admin | | | ☐ |
| Sales / CS (if commercial) | | | ☐ |

**Pilot Readiness target:** ≥ 9.0 — **Certified 9.4** (EP-08).
