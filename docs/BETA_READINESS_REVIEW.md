# Sprint CQ-30.8 — Beta Readiness Review

**Mode:** CTO / Enterprise Architect / Principal Security Engineer / SaaS Product Reviewer. This
document synthesizes this sprint's fresh evidence with `docs/BETA_READINESS_REPORT.md` (CQ-30.6) and
`docs/SPRINT_CQ_30_7_PRODUCT_REVIEW.md` (CQ-30.7) into one ranked blocker list per the brief's explicit
ask. Documentation only, `src` not modified.

## Beta blockers, ranked

### Critical

| Problem | Evidence | Why it matters | Risk | Recommended solution | Effort | Priority |
|---|---|---|---|---|---|---|
| Nginx has no real TLS configuration despite port 443 being exposed | `nginx.conf`, `docker-compose.prod.yml` | Beta customers connecting over HTTPS may fail or connect insecurely | High — direct customer-facing failure | Add a real `server { listen 443 ssl; }` block + certificate | S-M | Critical |
| Nginx catch-all returns a placeholder string, not the real frontend | `nginx.conf`'s `location /` | Reads as an unfinished production config; needs direct confirmation | High if genuinely unfinished | Verify and fix, or confirm frontend is served elsewhere and document why | S (verify) | Critical |
| Grafana ships with a default admin password fallback | `docker-compose.prod.yml` | Real operational/business metrics exposed behind a guessable default | High if deployed as-is | Require the env var with no fallback | S | Critical |
| No prompt-injection/AI-abuse protection anywhere in the codebase | repo-wide grep, zero hits | Real, reachable AI surface (Agents, Production Studio) with no input hardening | Medium-High, unaddressed risk class | Add a basic moderation/sanitization layer ahead of the provider call | M | Critical |
| Registration/Invitation flow reality unconfirmed | `docs/LOGIN_USER_FLOW.md` §3 (CQ-30.1) | No confirmed way for a new user to join a Beta org | Blocking if genuinely absent | Verify against running app immediately | S (verify) | Critical |
| 79 heuristic tenant-isolation findings, untriaged | `docs/TENANT_ISOLATION_AUDIT.md` (real, Sprint 30.0) | Largest unquantified cross-tenant risk | Unknown until triaged | Manual triage of all 79 | M | Critical |

### High

| Problem | Evidence | Why it matters | Risk | Recommended solution | Effort | Priority |
|---|---|---|---|---|---|---|
| Маркетинг/Маркетплейс mislabeling across 3 real dictionaries | `docs/UX_AUDIT.md` (CQ-30.7) | Direct comprehension failure for a brief-named module | Medium | Fix 3 dictionary values | S | High |
| `bot` service has no Docker healthcheck | `docker-compose.prod.yml` | No automatic recovery from a hung (not crashed) app process | Medium | Add healthcheck targeting real `/health` | S | High |
| Client and Dealer roles have no real navigation surface | `docs/CLIENT_EXPERIENCE.md`/`docs/DEALER_EXPERIENCE.md` (CQ-30.7) | Two Beta personas with no defined experience | High if either persona is in the first cohort | Scope Client separately (new design); build Dealer nav (data already real) | L / M | High |
| AI Production Center consent-gate must precede voice/avatar generation | `TD-46` | Legal/trust risk if built in the wrong order | High if skipped | Build the gate before any real generation work | M | High |
| Two real rate limiters, relationship unconfirmed; no edge-layer rate limiting at all | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 4, `docs/SECURITY_REVIEW.md` §9 | Every request relies entirely on unconfirmed application-level limiting | Medium | Trace the two limiters; add `limit_req` at nginx | S (trace) / S (nginx) | High |
| No log aggregation service | `docs/OBSERVABILITY_REVIEW.md` §3 | Incident response relies on manual container-log access | Medium | Add Loki (pairs with real Grafana) | M | High |

### Medium

| Problem | Evidence | Why it matters | Risk | Recommended solution | Effort | Priority |
|---|---|---|---|---|---|---|
| No real `Project` entity | `TD-51` | Blocks Resource Allocation/Quality/Metrics designs | Medium | Add `Project` table + `Deal.project_id` FK | M | Medium |
| Kernel/Orchestrator naming collision, three integration layers | `TD-59`/`TD-60` | Future contributor confusion, possible health-state disagreement | Medium | Document the layering | S | Medium |
| Error response envelope confirmed only within `platform_management`, not platform-wide | `docs/API_REVIEW.md` §8 | Inconsistent integrator experience across domains | Medium | Audit other domains' error shapes | M | Medium |
| No distributed tracing | `docs/PERFORMANCE_REVIEW.md` §1 | Slower incident diagnosis for multi-service requests | Medium | Extend real `request_id` into structured logs first | M | Medium |
| DB fan-out (`management_router`, `dashboard_service`) never load-tested | `TD-32` | Unmeasured performance risk | Medium | Run a real load test | M | Medium |
| Second SQLite artifact in `backups/`, violates `POSTGRES_ONLY` policy | `backups/backup_2026_07_12_12_55.db` | Policy violation, same shape as `TD-30` | Low | Confirm unused, then delete or document | S | Medium |

### Low

| Problem | Evidence | Why it matters | Risk | Recommended solution | Effort | Priority |
|---|---|---|---|---|---|---|
| `src/domains`'s 141 orphaned files | `TD-55` | Largest undocumented architectural fork | Low | Confirm unused, document-or-delete | S | Low |
| `docs/UI_NAVIGATION.md`'s prose undercounts the real 23-item sidebar | `docs/UX_AUDIT.md` | Documentation drift | Low | Resync one line | S | Low |
| Inconsistent pagination `limit` defaults | `docs/API_REVIEW.md` §3 | Minor integrator confusion | Low | Standardize a default | S | Low |
| ~100 top-level directories, bare `./platform`/`./workflow` collisions | `TD-56` | Discoverability tax | Low | Disambiguate two directory names | S | Low |

## Non-goals

- No fixes implemented — every row above is a recommendation, per this sprint's documentation-only
  constraint.
- No re-litigation of items already exhaustively covered in `docs/TECH_DEBT.md`/`docs/TOP_50_
  IMPROVEMENTS.md`/`docs/TOP_100_UX_IMPROVEMENTS.md` — this document ranks and synthesizes, it does
  not re-derive.

## Related documents

`docs/TOP_100_BETA_FIXES.md`/`docs/EXECUTIVE_RELEASE_REPORT.md` (CQ-30.8 siblings, the further
distillation and CTO verdict), `docs/SECURITY_REVIEW.md`/`docs/API_REVIEW.md`/`docs/ARCHITECTURE_
CONSISTENCY.md`/`docs/SCALABILITY_REVIEW.md`/`docs/PERFORMANCE_REVIEW.md`/`docs/OBSERVABILITY_
REVIEW.md`/`docs/PRODUCTION_GAPS.md` (this sprint's full evidence base), `docs/TECH_DEBT.md`
(canonical registry), `docs/BETA_READINESS_REPORT.md` (CQ-30.6), `docs/SPRINT_CQ_30_7_PRODUCT_
REVIEW.md` (CQ-30.7).
