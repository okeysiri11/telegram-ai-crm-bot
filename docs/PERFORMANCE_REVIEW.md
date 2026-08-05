# Sprint CQ-30.8 — Performance Review

**Scope:** concrete performance characteristics — distinct from `docs/SCALABILITY_REVIEW.md`'s
org-count/infrastructure-scaling angle. This document asks "is what exists today fast," not "will it
handle more load." Documentation only, `src` not modified, no load test executed (consistent with
every prior review's stated methodology in this engagement).

## 1. No APM/tracing infrastructure confirmed

Real Prometheus + Grafana exist in `docker-compose.prod.yml` (metrics collection/visualization,
confirmed this review) — but no distributed tracing (OpenTelemetry, Jaeger, etc.) was found anywhere
in the repository. Prometheus can answer "is the system healthy in aggregate"; it cannot answer "which
specific request in a multi-service call chain was slow." For a platform with the real fan-out this
engagement has repeatedly flagged (`management_router`'s 9-package fan-out, `dashboard_service`'s
7-service synchronous aggregation, `TD-32`), this is a real gap in the ability to diagnose a slow
request after the fact.

- **Problem:** no request-level tracing exists.
- **Evidence:** `docker-compose.prod.yml` (real Prometheus/Grafana, no tracing service);
  `grep`-confirmed no `opentelemetry`/`jaeger`/`zipkin` dependency anywhere in the repo.
- **Why it matters:** debugging a slow Beta customer complaint would rely entirely on logs and metrics
  aggregates, not a request trace — materially slower incident response.
- **Risk:** Medium — not a launch blocker, a real operational cost once Beta traffic exists.
- **Recommended solution:** add basic request-ID propagation (the real `request_id` correlation
  already used in `platform_management/response_models.py`'s error envelope is a good foundation — 
  extend it into structured logs consistently, before investing in full distributed tracing).
- **Effort:** M.
- **Priority:** P2 (post-Beta acceptable, pre-Beta nice-to-have).

## 2. DB fan-out remains unmeasured

Restated from `TD-32`/`docs/SCALABILITY_REVIEW.md`: `management_router`'s 9-package fan-out and
`dashboard_service`'s 7-service synchronous aggregation have never been load-tested. This review adds
no new evidence beyond confirming the finding is still accurate and still unmeasured.

- **Priority:** P1 — should precede any claim of Beta performance readiness, cheap to actually measure.
- **Effort:** M (a real load test, not a code change).

## 3. Real retry/backoff exists in the task-queue layer — a genuine positive

`platform_workflow/task_queue.py`'s real `requeue_for_retry(task, delay_seconds)` and
`task.retry_count` tracking (confirmed this review) is real, working retry infrastructure — this is a
performance-resilience positive, not a gap. Cited explicitly since most of this review's findings are
gaps; this one is confirmed working.

## 4. Frontend runtime performance — LOD discipline confirmed, elsewhere unconfirmed

Restated from `docs/SCALABILITY_REVIEW.md` §7: the real City Graphics Engine has genuine LOD/
performance-budget discipline. The eleven-plus other frontend runtimes (`spatialRuntime`, `lifeEngine`,
etc.) were not individually profiled for render/computation cost as entity count grows — flagged as
unmeasured, not assumed fine or assumed broken.

## 5. No confirmed frontend bundle-size or load-time budget

No real bundle-analysis config or load-time budget was found in `src/web`'s build tooling in this
pass — a first-time user's actual page-load experience (directly relevant to `docs/FIRST_TIME_
USER.md`'s comprehension question, CQ-30.7) was not measured.

- **Priority:** P3 for Beta (functional correctness matters more at this stage than load-time
  polish), worth adding before a public (non-Beta) launch.
- **Effort:** S (add a bundle-size CI check) to M (actually optimize if the check fails).

## 6. Sprint CQ-32.2 addition — caching, queues, search, DB, async, WebSocket, streaming, provider calls, AI execution

| Area | Real status | Finding |
|---|---|---|
| Caching | Real Redis, real `--appendonly yes` persistence (`docker-compose.prod.yml`) | No confirmed application-level cache-invalidation strategy audited this pass — Redis is real infrastructure, its usage pattern wasn't re-verified |
| Queues | Real, three independent in-process priority queues (`docs/SCALABILITY_REVIEW.md` §10) | Restated — no new evidence this pass |
| Search | **No real search/vector engine exists** (`docs/PLATFORM_CORE_REVIEW.md`) | Confirmed again — this is now the fourth review in this engagement to independently reach the same conclusion |
| Database | Real Postgres, real healthcheck, no confirmed connection pooler | Restated from `docs/SCALABILITY_REVIEW.md` §1 |
| Async jobs | Real `asyncio`-based task queues with real retry (`requeue_for_retry`) | Real and reasonably sophisticated; timeout handling unconfirmed (`docs/AI_RUNTIME_REVIEW.md` §7) |
| WebSocket | Confirmed dormant by default (Socket.IO, prior research) — not re-verified this pass | Restated |
| Streaming | Not independently audited this pass | Flagged as a coverage gap in this review, not claimed as reviewed |
| Provider calls | One real wired provider (`openrouter.py`), real cost tracking (`platform_ai/cost_tracker.py`, new finding this sprint), no confirmed circuit-breaker/backpressure handling | Cost tracking corrects a prior assumption of absence — see `docs/AI_RUNTIME_REVIEW.md` Part B |
| AI execution | Real, now security-hardened (Sprint 30.9 Prompt Firewall) | See `docs/SECURITY_ARCHITECTURE_REVIEW.md` §1 |

## Non-goals

- No load testing performed — every finding here is architectural inference, consistent with this
  entire engagement's stated methodology.
- No performance optimization recommended without a measurement first (§2's recommendation is
  explicitly "measure," not "assume and fix").
- No caching-strategy audit performed — flagged as unverified, not reviewed.

## Related documents

`docs/SCALABILITY_REVIEW.md` (CQ-30.6, the org-count-scaling counterpart to this document),
`docs/TECH_DEBT.md` (TD-32), `docs/OBSERVABILITY_REVIEW.md` (CQ-30.8 sibling, monitoring/logging
infrastructure this review's §1 finding is most relevant to), `docs/AI_RUNTIME_REVIEW.md`/
`docs/PLATFORM_CORE_REVIEW.md` (CQ-32.2 siblings).
