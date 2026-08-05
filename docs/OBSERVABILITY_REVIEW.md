# Sprint CQ-30.8 — Observability Review

**Scope:** monitoring, logging, health checks, audit trail. Documentation only, `src` not modified.

## 1. Monitoring — real, more complete than prior reviews credited

`docker-compose.prod.yml` (confirmed this review, full read) runs a real six-service production stack:
`postgres`, `redis`, `bot`, `nginx`, `prometheus` (`prom/prometheus:v2.54.1`, real config at
`deploy/prometheus.yml`), and `grafana` (`grafana/grafana:11.2.0`). This is genuine, working monitoring
infrastructure — prior reviews in this engagement (CQ-20's scalability review) undercounted this by
treating the compose file's service list only at a shallow level. **Correction to the record**: the
platform has real metrics collection and visualization, not just health-check endpoints.

- **Positive finding, no action needed** beyond `docs/SECURITY_REVIEW.md` §9's already-flagged default
  Grafana admin password.

## 2. Health checks — real, at the infrastructure level

Real Docker healthchecks exist for `postgres` (`pg_isready`, 5s interval, 10 retries) and `redis`
(`redis-cli ping`, 3s timeout, 10 retries) in both `docker-compose.yml` and `docker-compose.prod.yml`.
The real `bot` service exposes `/health` (proxied through `nginx.conf`'s real `location /health` block)
but has **no Docker-level `healthcheck:` directive of its own** — `depends_on: condition: service_
healthy` gates `bot`'s startup on Postgres/Redis health, but nothing gates *restart* decisions on the
`bot` service's own health once running.

- **Problem:** the application container itself has no liveness/readiness probe wired at the
  orchestration level.
- **Evidence:** `docker-compose.prod.yml`'s `bot:` service block — `restart: unless-stopped` exists,
  but no `healthcheck:` block, unlike `postgres`/`redis`.
- **Why it matters:** a hung (not crashed) `bot` process would not be automatically restarted — Docker
  only restarts on process exit, not on an unhealthy-but-running state, without an explicit healthcheck.
- **Risk:** Medium — real degraded-service risk with no automatic recovery.
- **Recommended solution:** add a `healthcheck:` block to the `bot` service targeting the real
  `/health` endpoint already exposed.
- **Effort:** S. **Priority:** P1 — cheap, closes a real gap in an otherwise well-instrumented compose
  file.

## 3. Logging — real, structured in places, not confirmed centralized

Real structured logging calls were found in sampled code (`logger.info("configuration_center_
reload")`, `logger.debug("legacy_flags_reload_skipped", exc_info=True)`, per prior reviews' direct
reads of `configuration_center.py`). No centralized log aggregation service (ELK, Loki, etc.) was
found in `docker-compose.prod.yml` — logs presumably go to container stdout/stderr only, collected by
whatever the deployment host does with Docker logs by default.

- **Problem:** no confirmed log-aggregation/retention story beyond default Docker logging.
- **Why it matters:** for a multi-tenant Beta with real customer-facing incidents, "SSH into the host
  and grep container logs" does not scale past a handful of concurrent issues.
- **Risk:** Medium — an operational maturity gap, not a correctness one.
- **Recommended solution:** add Grafana Loki (pairs naturally with the already-real Grafana/
  Prometheus stack) or an equivalent log-aggregation service to `docker-compose.prod.yml`.
- **Effort:** M. **Priority:** P2 — acceptable to defer past initial Beta given the real Prometheus/
  Grafana foundation already exists to build on.

## 4. Audit trail — real, but the two-table split (`TD` context) affects observability too

Real `AuditLog` (per-user) and `PlatformAuditLog` (platform-level) both exist (CQ-12 finding, restated).
From an observability angle specifically: an incident investigation spanning both a user action and a
platform-level event would require querying two separate tables with no confirmed unified view —
`docs/OWNER_MODE_UX.md`'s (CQ-30.1) "unified Owner Audit view" composes them at the UI layer, but no
equivalent exists for an on-call engineer querying directly.

- **Priority:** P3 — the real composed UI view (once built) partially addresses this; a backend-level
  unified query/view is a nice-to-have, not urgent.

## 5. Real request-ID correlation exists, narrowly

`platform_management/response_models.py`'s real `request_id` field (cited in `docs/API_REVIEW.md` §8)
is the one real correlation-ID mechanism found this pass — scoped to the management domain's error
responses, not confirmed as a cross-service, cross-log-line correlation standard.

## Non-goals

- No log-aggregation service implemented — Loki recommended, not built, in this documentation-only
  pass.
- No distributed tracing implemented — `docs/PERFORMANCE_REVIEW.md` §1 covers this in more depth as a
  performance-diagnosis concern; not duplicated here.

## Related documents

`docker-compose.prod.yml`/`deploy/prometheus.yml` (real), `docs/SECURITY_REVIEW.md` §9 (CQ-30.8, the
Grafana default-password finding), `docs/PERFORMANCE_REVIEW.md` (CQ-30.8 sibling), `docs/CITIZEN_
ORGANIZATION_MEMBERSHIP.md` (CQ-12, real `AuditLog`).
