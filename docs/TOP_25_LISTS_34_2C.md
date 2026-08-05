# Sprint 34.2C Independent Review — Top 25 Lists

Five ranked lists per the brief's explicit ask. Sourced from `docs/ARCHITECTURE_REVIEW_34_2C.md`'s
findings plus `docs/TECH_DEBT.md`'s canonical registry (through TD-67). Documentation only.

## TOP 25 Architectural Risks

1. Sync Engine (if being built in 34.2C) designed without the shared history/versioning primitive (`TD-54`) — repeats the platform's most common architectural mistake
2. Adapter cutover (`TD-64`) left open-ended rather than on a fixed cadence
3. Three-layer frontend runtime aggregator confusion (`TD-59`/`TD-60`) — resolution via `enterprise-runtime` not yet confirmed
4. No real vector/RAG search — architecturally absent, not fragmented, at "thousands of AI agents" scale
5. ISAM parallel identity surface for Enterprise Hub (`TD-33`-adjacent, `UNIFIED_IDENTITY_34_2A.md`'s own flagged gap)
6. Auto Marketplace's local Core-shaped services (`TD-61`)
7. No table partitioning/archiving strategy for canonical Deal tables ahead of "millions of records"
8. TenantUserRole integer FK deferred (`34.1 A6`) — costlier to fix the longer it's deferred
9. No connection pooler ahead of 1,000+ org scale
10. No confirmed per-tenant queue isolation in the new Unified Queue
11. No confirmed horizontal scaling path for the `bot` service (single instance in real prod compose)
12. `src/domains`'s 141 orphaned files, including the platform's one clean DDD `DomainEvent` pattern (`TD-55`)
13. No formal ADR log (deliberate choice, revisit post-Beta)
14. Universal Service Constructor foundation-only, no real third-party extension exercised (`TD-63`)
15. Security Center not yet wired into every HTTP/APH path (`TD-66`)
16. `container.py` DI scaffold never adopted (`TD-18`)
17. `database/__init__.py`'s dependency-inversion violation on `database_legacy` (`TD-19`)
18. Three permission-scope vocabularies at the frontend runtime layer, unaffected by Identity Core consolidation (`TD-52`)
19. No real distributed tracing for multi-service request diagnosis
20. `deal.py`'s OTC-flavored statuses leaking a financial-settlement concern into the generic pipeline entity
21. No real SSO/OIDC provider wired (stub only)
22. No confirmed read replicas for Postgres
23. No confirmed multi-region deployment design
24. Real n8n encryption-key default fallback (systemic secret-default pattern, one instance not yet confirmed fixed)
25. ~100 top-level directory sprawl, including bare `./platform`/`./workflow` naming collisions (`TD-56`)

## TOP 25 Technical Debt Items

1. `TD-64` — Adapter cutover for deal/workflow/knowledge/notify/queue (XL)
2. `TD-61` — Auto Marketplace local Core-shaped services (L)
3. `TD-55` — `src/domains` orphaned tree (S to decide)
4. `TD-56` — Top-level directory sprawl (XL, not recommended to act on now)
5. `TD-52` — Three permission-scope vocabularies (L)
6. `TD-50` — Three task/entity concepts, none reconciled (L)
7. `TD-51` — No real `Project` entity (M)
8. `TD-54` — No generic history/versioning mixin (L, now time-sensitive per Sync Engine risk #1 above)
9. `TD-19` — `database_legacy` dependency-inversion violation (M)
10. `TD-24` — 29 `reverse_layer_dependency` warnings (L)
11. `TD-18` — Unused DI scaffold (S decide / L wire in)
12. `TD-31` — Two migrations directories (S)
13. `TD-28` — `platform_console` unrouted pages (S)
14. `TD-40` — Orphaned frontend Command Palette copy (M)
15. `TD-41` — Duplicated favorites/history managers, unpersisted (M)
16. `TD-27` — `platform_builder`'s four near-identical center directories (M)
17. `TD-63` — Universal Service Constructor foundation-only (L)
18. `TD-66` — Security Center progressive wiring incomplete (L)
19. `TD-67` — `securityCenter.ts` seeds demo metrics on ISAM unreachable (M)
20. `TD-13` — Uneven OpenAPI coverage across verticals (L)
21. `TD-34`/`TD-35` — Dead links / CODEOWNERS gaps (S)
22. `TD-01`/`TD-02`/`TD-05` — Legacy naming-collision alias maps not yet published (S each)
23. `TD-43` — Enterprise City's three route aliases, one self-labeled legacy (S)
24. `TD-10` — Eight frame-only Platform Builder builders (L)
25. Note (TD-22/TD-05 staleness) — `TD-22`'s workflow-engine count needs its own registry update pass to point at `TD-48` more prominently

## TOP 25 Scalability Risks

1. Table partitioning/archiving absent for canonical Deal tables at "millions of records" scale
2. No connection pooler at 1,000+ orgs
3. No read replicas at 1,000+ orgs
4. `bot` service single-instance, no confirmed horizontal scaling
5. No confirmed per-tenant queue isolation (noisy-tenant risk) in Unified Queue
6. No real distributed queue if multi-process execution is ever needed beyond the current in-process Unified Queue
7. No real vector search — any future RAG build must be designed tenant-isolated and indexed for scale from day one
8. Frontend runtime state is per-browser-session (not an org-count risk, but a real concurrent-session-count one at "hundreds of simultaneous conversations")
9. No distributed tracing — diagnosing a slow request at scale relies on logs/metrics alone
10. No log aggregation service — incident response at scale relies on manual container access
11. `management_router`'s 9-package fan-out and `dashboard_service`'s 7-service synchronous aggregation, never load-tested
12. WebSocket usage confirmed dormant by default — unverified at "hundreds of simultaneous conversations" scale if activated
13. No confirmed circuit-breaker/backpressure handling on the one real AI provider path
14. No confirmed rate limiting at the nginx/edge layer (application-level only)
15. Telegram bot polling architecture's scaling ceiling not independently assessed at "10,000 users"
16. No confirmed CDN/media-delivery scaling plan beyond the real multi-backend storage abstraction
17. Real Prometheus/Grafana exist but no confirmed alerting-threshold tuning for the brief's stated scale targets
18. No confirmed database index review for the specific query patterns "millions of CRM records" would produce
19. Event Bus fan-out cost at "thousands of AI agents" not independently modeled
20. No confirmed backpressure mechanism between the Unified Queue and downstream AI provider calls
21. Knowledge Graph persistence backend (Postgres vs. in-memory) not confirmed for all real systems
22. No confirmed capacity plan for `n8n` sidecar if workflow volume scales with org count
23. No confirmed multi-region latency plan (single-region assumption throughout)
24. Session/JWT refresh-token storage scaling not independently assessed at 10,000 concurrent users
25. Real City Graphics Engine's LOD discipline (a strength) has no confirmed equivalent for the newer `enterprise-runtime` package's own rendering/computation cost as agent count grows

## TOP 25 Future Blockers

1. No Sync Engine yet — required for real offline/multi-device support at enterprise scale
2. No real vector/RAG search — required for any credible "AI-first enterprise platform" positioning at scale
3. No real SSO/OIDC — blocks enterprise customers with a hard SSO requirement
4. No real multi-region design — blocks customers with data-residency requirements
5. No confirmed horizontal scaling for `bot` — blocks growth past current single-instance ceiling
6. ISAM/Identity Core dual-path — blocks a fully unified session model until folded in
7. Adapter cutover incompleteness (`TD-64`) — blocks confidently deleting any legacy engine
8. No real third-party extension proof — blocks a credible marketplace launch claim
9. No table partitioning — blocks graceful growth to "millions of records" without a painful retrofit
10. No formal ADR log — blocks efficient onboarding of new engineers/teams at larger scale
11. `src/domains`'s undocumented fork — blocks confident engineering decisions about that code's future
12. No distributed tracing — blocks efficient incident response at scale
13. No per-tenant resource quotas — blocks safe multi-tenant scaling past a trust-based model
14. Three permission-scope vocabularies at the frontend layer — blocks a fully consistent authorization story across Identity Core and the older runtimes
15. No confirmed disaster-recovery restore-drill automation — blocks a defensible enterprise DR SLA claim
16. Microservices decomposition premature until canonical-service boundaries (§1) are fully proven — not itself a blocker, but attempting it early would become one
17. No real chaos-engineering validation of the retry/DLQ infrastructure under failure
18. No real per-tenant billing/metering — blocks a metered-usage enterprise pricing model
19. Mobile UI not built (though the registry is ready for it) — blocks a mobile go-to-market claim
20. No confirmed WebSocket scaling design if real-time collaboration features are activated
21. No real government/compliance-specific review — blocks regulated-industry customers
22. Auto Marketplace's local service trees — blocks a fully trustworthy "one Core" claim to prospective enterprise buyers doing technical diligence
23. No confirmed circuit-breaker on the single real AI provider — blocks graceful degradation if that provider has an outage
24. Knowledge Base four-way historical fragmentation, even with a canonical pick, still has real legacy consumers not yet migrated
25. No confirmed capacity-planning documentation tying real infrastructure to the brief's specific stated scale targets (100 companies / 10,000 users / millions of records / thousands of agents / hundreds of conversations) — this review had to estimate against those targets without a pre-existing capacity model to check against

## TOP 25 Highest-ROI Improvements

1. Confirm and complete the `enterprise-runtime` consolidation of `cityVisualization`/`orchestrator`/`kernel` (§8) — cheap to verify, closes two tracked debt items
2. Sequence `TD-54`'s history/versioning pattern design alongside any Sync Engine work, not after
3. Design table partitioning for canonical Deal tables now, while data volume is still low
4. Schedule the TenantUserRole FK migration before the 100-company mark
5. Add a connection pooler — bounded, well-understood, meaningful headroom gain
6. Put the adapter cutover (`TD-64`) on a fixed per-sprint cadence instead of open-ended
7. Verify `ENVIRONMENT=production` is correctly set in the real deploy pipeline — cheap, closes `TD-65`'s residual risk
8. Complete `TD-66`'s progressive Security Center wiring
9. Confirm zero usage of `src/domains`, then document-or-delete — cheap, high discoverability payoff
10. Add basic distributed tracing via the already-real `request_id` correlation pattern
11. Add log aggregation (Loki, pairs with the already-real Grafana)
12. Fold ISAM into Identity Core (`docs/UNIFIED_IDENTITY_34_2A.md`'s own stated next step)
13. Thin the Auto Marketplace adapters via `PlatformBridge`
14. Run a real load test on the two known fan-out points before claiming Beta performance readiness
15. Publish alias maps for the remaining legacy naming collisions (`TD-01`/`TD-02`/`TD-05`) — cheap, closes discoverability gaps
16. Build the Universal Service Constructor UI once a marketplace launch date is set — sequences correctly, not urgent before then
17. Wire real per-tenant queue quotas into the Unified Queue ahead of 1,000+ org scale
18. Add a real OIDC provider once a specific enterprise customer requires SSO — the stub is ready, low incremental cost
19. Retire the orphaned frontend Command Palette copy (`TD-40`) — dead code, zero risk to remove
20. Unify the duplicated favorites/history managers with real persistence (`TD-41`)
21. Confirm the real Prompt Firewall's deny-list coverage against a fresh adversarial-prompt sample, given "thousands of AI agents" raises the exposure surface
22. Design real vector search with tenant isolation from day one — the highest-leverage single capability gap for an "AI-first" positioning
23. Consolidate `platform_builder`'s four near-identical center directories (`TD-27`) — smallest-blast-radius proof-of-concept for the bigger consolidations already done
24. Add a repo-root CI check flagging new top-level directories, preventing `TD-56` from growing further
25. Formalize this engagement's own review cadence as a standing process — the single highest-leverage governance change available, given every review in this lineage has found real, actionable value

## Related documents

`docs/ARCHITECTURE_REVIEW_34_2C.md` (the source of every list item's detail), `docs/TECH_DEBT.md`
(canonical registry), `docs/SPRINT_CQ_34_2C_RESULT.md` (maturity scores + roadmap).
