# Enterprise Overnight Audit — Top 20 Critical Fixes

Ranked by (severity × cheapness × blast-radius-if-ignored), not by category. Each includes why,
impact, risk, complexity, priority — per the audit's own required format. Documentation only, `src`
not modified; these are recommendations for a future implementation pass.

| # | Fix | Why | Impact if fixed | Risk if ignored | Complexity | Priority |
|---|---|---|---|---|---|---|
| 1 | Resolve `TD-17`'s CI-failing `os.environ` bypass of `ConfigurationCenter` (`platform_security/config.py:23-24`, `secrets.py:30,80`) | Currently failing CI's own architecture gate | Restores a clean CI signal | Governance gate stays red, normalizing ignoring it | S | P0 |
| 2 | Trace `TD-57`'s second JWT-secret read path (`configuration_center.py:100`) to its consumers; guard or remove | The platform's own validated-secret guard may not cover every real signing path | Closes a possible silent auth bypass | Unknown severity until traced — could be P0 | S | P0 |
| 3 | Build the AI Production Center consent-record gate before any real avatar/voice provider (`TD-46`) | UI already exists in a shape that invites building the unsafe order | Prevents a governance/legal failure in a sensitive feature | High — a rushed provider integration is the single most consequential wrong-order risk in the repo | M | P0 |
| 4 | Extend Platform Builder header-only auth with live identity (`TD-08`) | `X-Principal`/`X-Platform-Role` are currently unverified | Closes a real authentication-bypass shape | Any caller can currently claim any role on this surface | L | P0 |
| 5 | Verify tenant-filter completeness across `repositories/` (`TD-58`) | Never exhaustively confirmed | Rules out (or finds) a cross-tenant data leak | Unconfirmed — worst case is the most severe possible finding for a multi-tenant platform | M | P1 |
| 6 | Add `Project` table + `Deal.project_id` FK (`TD-51`) | No real link exists between sales and execution today | Unblocks Resource Allocation/Quality/Metrics work already designed and waiting on this | Every downstream Process/Value-Chain design stays undeployable | M | P1 |
| 7 | Wire or retire `platform_console`'s unrouted pages / unused `ProtectedRoute` (`TD-28`) | Auth exists but enforces nothing because nothing routes through it | Closes an unenforced-by-omission gap | Looks protected, isn't | S | P1 |
| 8 | Confirm `alembic.ini`'s authoritative migrations directory; document/retire the other (`TD-31`) | Two real migration directories exist | Removes "which migrations actually run" ambiguity before it causes a real schema drift incident | A wrong-directory migration could silently not apply | S | P1 |
| 9 | Unify the three permission-scope vocabularies' rank semantics, or explicitly document why they must stay separate (`TD-52`) | `company` means different relative things in `Spatial` vs `Asset` scope today | Removes a same-word-different-meaning security footgun | A future composition bug is easy to introduce silently | L | P1 |
| 10 | Confirm `src/domains`'s 141 files are truly unused, then document-or-delete (`TD-55`) | Largest undocumented architectural fork in the repo | Removes the single biggest "what is this" question for new contributors | Stays as permanent unexplained maintenance surface | S | P1 |
| 11 | Write down the `src/kernel` TS-ecosystem-to-Python-backend relationship decision (`TD-33`) | Never documented as intentional | Resolves the platform's most consequential undocumented fork | Future investment decisions keep being made blind | S | P1 |
| 12 | Publish `CanonicalStageMapping` lookup tables for the six deal systems (`TD-47`) | No shared vocabulary today | Any future cross-system report becomes tractable | Every new integration re-derives its own six-way mapping | S | P1 |
| 13 | Trace whether frontend `workflowRuntime` should call the backend workflow engines or stay UI-only, and document the answer (`TD-48`) | Currently silently disconnected | Closes a real "does the UI reflect what actually ran" trust gap | Users may be watching client-only state believing it's backend-recorded | M | P1 |
| 14 | Retire the orphaned frontend Command Palette copy (`TD-40`) | Confirmed dead, compiled, never rendered | Removes dead code with zero functional risk | Low, but a wasted-maintenance tax accrues | M | P1 |
| 15 | Unify or explicitly justify keeping separate the duplicated favorites/recent-history managers, and add real persistence (`TD-41`) | Two implementations, neither persists | Real UX fix, not just cleanup | Users lose favorites/history on every reload today | M | P1 |
| 16 | Publish the four-knowledge-graph-system disambiguation as the canonical guidance in onboarding docs (`TD-49`) | Four systems, all self-described as "the unifying one" | Prevents a fifth system being built by someone who found only one of the four | Repeat of the exact pattern that created the other collisions | S | P1 |
| 17 | Add index/partition review for `DealStageHistory`-shaped tables before real transaction volume arrives | Write-heavy audit-trail tables benefit from this proactively | Avoids a real future performance incident | Currently unmeasured, not urgent, but worth scheduling | M | P2 |
| 18 | Disambiguate `./platform`/`./workflow` bare directories from their prefixed-package near-namesakes (`TD-56`) | Real import-time confusion risk | Cheap discoverability win | Low but compounding | S | P2 |
| 19 | Consolidate `applications/platform_builder`'s four near-identical center directories (`TD-27`) | Smallest-blast-radius instance of the Command Center pattern | A concrete, bounded proof that consolidation can be done safely, informing the bigger collisions | Stays as an easy example of the pattern going unaddressed | M | P2 |
| 20 | Add a `Deal.project_id`-style linking field decision log entry to `ARCHITECTURE_MAP.md` once #6 ships | `CLAUDE.md`'s own "every architectural decision must be documented" rule | Keeps the living docs honest | Repeats the undocumented-decision pattern this whole audit found repeatedly | S | P2 |

## Related documents

`docs/TECH_DEBT.md`, `docs/ARCHITECTURE_IMPROVEMENTS.md`, `docs/TOP_100_RECOMMENDATIONS.md`,
`docs/SECURITY_REVIEW.md`, `docs/EXECUTIVE_SUMMARY.md`.
