# Sprint CQ-30.6 — Beta Readiness Report

**Question:** can the platform realistically launch as Beta? **Answer:** yes, for a deliberately scoped
Beta (10–100 organizations, invitation-based onboarding, Production Studio marked honestly as
UI-preview), contingent on the blockers below being resolved first — not a "not ready" verdict, a
"ready with conditions" one.

## Blockers (must resolve before Beta launch)

1. **Registration/Invitation flow reality unconfirmed.** No real dedicated Registration or Invitation
   page was found in `src/web/auth` (`docs/LOGIN_USER_FLOW.md` §3, CQ-30.1). Without one of these two,
   no new user can join a Beta organization through the UI at all. **Verify against the running app
   immediately** — if genuinely absent, this is the single highest-priority build item before any
   other recommendation in this review.
2. **79 heuristic tenant-isolation findings, untriaged.** A real audit exists (`docs/TENANT_ISOLATION_
   AUDIT.md`, Sprint 30.0) but none of the 79 flagged repository methods has been manually confirmed
   real-vs-false-positive. Launching Beta with paying/real customer data before this triage is complete
   is the platform's single largest unquantified risk.
3. **AI Production Center consent-gate must precede any real generation backend** (`TD-46`). Not
   currently a blocker in itself (no real generation exists yet, per `TD-45`), but becomes one the
   moment generation work starts — flagged here so it isn't missed in the rush to make Beta "feel"
   more complete.

## Warnings (should resolve soon, not necessarily before launch)

1. Header-only Platform Builder auth is mitigated (Sprint 30.0: live JWT/API-key preferred, header
   auth off by default in production) but not fully cut over across all vertical middlewares (`TD-08`).
2. Client and Dealer roles have no real platform-wide UX (`docs/ROLE_NAVIGATION.md` §3) — if Beta
   includes either persona, this needs real design work first, not just documentation.
3. Google Sign-In is unbuilt — fine if Beta messaging doesn't promise it, a real gap if it does.
4. Three unreconciled permission-scope vocabularies (`TD-52`) — the platform's most plausible
   escalation vector, worth resolving before Beta scales past its initial cohort.
5. No confirmed connection pooler or DB read replica — fine at 10–100 orgs (`docs/SCALABILITY_
   REVIEW.md` §9), a real gap the moment Beta succeeds and needs to grow past that range.
6. Owner-scoped backend endpoint enforcement not independently re-verified this pass (`docs/SECURITY_
   REVIEW.md` §8) — the UI correctly hides Owner-only links, but that alone is not access control.

## Optional improvements (nice-to-have, not blocking)

1. Add generation-status honesty indicators to Production Studio cards (`docs/PRODUCTION_STUDIO_UX.md`
   §3) — improves trust, doesn't block launch since no generation exists to mislabel yet regardless.
2. Consolidate the three in-process task queues — real cost today is low; consolidation is a
   deliberate future decision, not a Beta gate.
3. Add the missing Knowledge Graph API prefixes to `API_MAP.md` (`TD-49`) — improves discoverability,
   no functional impact.
4. Standardize pagination `limit` defaults (`docs/API_REVIEW.md` §3) — cosmetic API consistency.
5. Russian dictionary rollout (`docs/RUSSIAN_UI_DICTIONARY.md`, CQ-30.1) — already designed, wiring
   it in is additive and low-risk whenever convenient.

## What Beta should explicitly NOT attempt

- Do not scale-test or market Beta for 1,000+ organizations — `docs/SCALABILITY_REVIEW.md` §9's own
  verdict is "real risk" at that scale; 10–100 is the honest, defensible target.
- Do not build a GraphQL server for Beta (`docs/API_REVIEW.md` §6).
- Do not attempt to consolidate the six-way deal, seven-way workflow, or four-way Knowledge Graph
  collisions during Beta prep — every prior successful reconciliation in this codebase was
  incremental; a rushed merge during a Beta crunch is a real regression risk.

## Overall verdict

**Conditionally ready.** The platform's core governance (CI-enforced architecture validation, frozen
API contracts, a real and actively-improving technical debt registry, real MFA/session/lockout auth
pages, a mature design system) is genuinely strong — stronger than the volume of open `TD-XX` items
might suggest in isolation. The path to Beta is short and specific: confirm/build one onboarding path
(blocker 1), triage 79 named findings (blocker 2), and sequence the consent gate correctly (blocker 3).
None of the three requires new architecture — all three are execution, not design, work.

## Related documents

`docs/ENTERPRISE_V1_READINESS.md` (CQ-30, the prior readiness pass this report updates),
`docs/LOGIN_USER_FLOW.md` (CQ-30.1), `docs/TENANT_ISOLATION_AUDIT.md` (real, Sprint 30.0),
`docs/SECURITY_REVIEW.md`/`docs/SCALABILITY_REVIEW.md`/`docs/API_REVIEW.md` (CQ-30.6 siblings).
