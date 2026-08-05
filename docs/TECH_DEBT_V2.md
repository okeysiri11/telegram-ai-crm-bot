# Sprint CQ-30.6 — Technical Debt: Ranked Review Snapshot

**This is a snapshot view, not a second registry.** `docs/TECH_DEBT.md` remains the single canonical
technical debt registry for this platform (per its own explicit self-description and the "do not
create a competing document" discipline this engagement has followed since Sprint CQ-20's overnight
audit found `TECH_DEBT.md` already supersedes `docs/TECHNICAL_DEBT_REPORT.md`). This document exists
only because the brief requires this specific ranked Critical/High/Medium/Low format with Why/Impact/
Risk/Effort/Recommended-Sprint columns — every ID below is a `TD-XX` from the canonical registry,
re-ranked for this review's purpose. **Updates to any item's actual status belong in `TECH_DEBT.md`,
not here.**

## Critical

| ID | Item | Why | Impact | Risk | Effort | Recommended sprint |
|---|---|---|---|---|---|---|
| TD-58 | 79 heuristic tenant-isolation findings, real audit tool, not yet triaged | A real, systematic scan exists but none of the 79 flags has been manually confirmed real-vs-false-positive | Cross-tenant data leak is the worst-case outcome for a multi-tenant platform | Unknown until triaged — could range from 0 real leaks to several | M (triage 79 flags) | Next sprint, before any Beta customer with real data |
| TD-51 | No real `Project` entity | Cheapest, highest-leverage schema gap found across this whole engagement; blocks Resource Allocation/Quality/Metrics designs already written | Every downstream Value-Chain design stays undeployable | Low (purely additive) | M | Next sprint |
| TD-46 | AI Production Center consent-gate sequencing risk | UI shell already exists in a shape that invites building avatar/voice generation before the consent gate | Legal/trust failure in a sensitive feature if built in the wrong order | High if skipped | M | Before any Production Studio generation backend work begins |

## High

| ID | Item | Why | Impact | Risk | Effort | Recommended sprint |
|---|---|---|---|---|---|---|
| TD-59/TD-60 | Kernel/Orchestrator naming and layering collision, now three integration layers deep | The exact recommendation from the prior audit ("don't add a second aggregator") was not followed | Future contributor confusion, possible health-state disagreement between layers | Medium | S (document) / M (re-plumb) | Next sprint (documentation), following sprint (re-plumb if needed) |
| TD-55 | `src/domains` — 141 orphaned files | Largest undocumented architectural fork in the repo | Ongoing maintenance-surface confusion cost | Low | S (confirm + decide) | Next sprint |
| TD-08 | Header-only Platform Builder auth — mitigated but not fully cut over | Sprint 30.0 added live JWT/API-key preference with header auth off by default in production, but full token-only cutover for all vertical middlewares remains | Real authentication-bypass shape if `ALLOW_HEADER_AUTH` is ever misconfigured on in production | Medium (down from the prior P0, given the mitigation) | L | Within 2 sprints |
| New | Three independent in-process task queues (`job_queue.py`, `task_queue.py` ×2) | Same problem solved three times, none distributed | Consolidation cost grows the longer each is extended independently | Low today, compounds | L | Deliberate future sprint, not urgent |
| TD-52 | Three permission-scope vocabularies, different rank semantics for "company" | Real escalation-vector shape, not just a naming issue | A future composed check could silently produce an unintended-allow | Medium | L | Within 2-3 sprints |

## Medium

| ID | Item | Why | Impact | Risk | Effort | Recommended sprint |
|---|---|---|---|---|---|---|
| TD-49 | Four Knowledge Graph systems, similar-looking API prefixes undocumented in `API_MAP.md` | Prevents "check before building" from working for exactly the category most likely to recur | A fifth system could be built by someone who found only one of four | Medium | S | Next sprint |
| New | `ENTITY_TYPES`/`RELATION_TYPES` are compile-time tuples, not runtime-extensible | Confirmed this review — a deliberate, defensible choice for Beta, but worth a documented decision, not a silent constraint | New-vertical onboarding requires a code change | Low (accepted for Beta per this review's own §6 recommendation) | S (document the decision) | Next sprint |
| New | Pagination `limit` defaults inconsistent (50/100/500) across `management_router.py` endpoints | Minor API-consistency smell, found this review | Confusing for integrators, not a functional bug | Low | S | Opportunistic |
| TD-31 | Two migrations directories | Unclear which is authoritative for new Alembic revisions | A wrong-directory migration could silently not apply | Low-Medium | S | Next sprint |

## Low

| ID | Item | Why | Impact | Risk | Effort | Recommended sprint |
|---|---|---|---|---|---|---|
| TD-56 | ~100 top-level directories, `./platform`/`./workflow` bare-name collisions | Discoverability tax | Low, compounding | Low | S (disambiguate) / XL (restructure, not recommended) | Opportunistic |
| TD-34/TD-35 | Dead links / CODEOWNERS gaps | Documentation hygiene | Low | Low | S | Opportunistic |
| No GraphQL server | Not built, not needed for Beta per `docs/API_REVIEW.md` §6 | N/A — explicit non-recommendation | N/A | N/A | N/A | Not scheduled |

## Non-goals

- This document does not resolve, close, or re-score any `TD-XX` item — those actions happen in
  `docs/TECH_DEBT.md` only.
- No new debt ID is minted here for items that already have one — the "New" rows above are genuinely
  new findings from this review's own research and will receive real `TD-XX` numbers when folded into
  the canonical registry (recommended as this sprint's own follow-up action, not done in this document
  to avoid numbering collisions with concurrent Cursor work on the same file).

## Related documents

`docs/TECH_DEBT.md` (canonical, TD-01 through TD-60 at time of writing), `docs/ARCHITECTURE_
REVIEW_V2.md`/`docs/SECURITY_REVIEW.md`/`docs/SCALABILITY_REVIEW.md`/`docs/API_REVIEW.md` (CQ-30.6
siblings, the source of every "New" row above).
