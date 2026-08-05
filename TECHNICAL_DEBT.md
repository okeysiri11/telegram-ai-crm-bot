# Technical Debt — ADOS Platform (as of v0.9.4-rc1)

Tracked for Sprint 38.3 RC. Items marked **Sprint 39** are recommended next.

## P0 — do not ignore in production

| ID | Item | Notes | Target |
|----|------|-------|--------|
| TD-01 | Placeholder secrets in `.env.production` | `CHANGE_ME` for Postgres/Grafana/JWT/n8n | Sprint 39 |
| TD-02 | Default Grafana/Postgres passwords in local compose | Acceptable for local RC; never ship as-is | Ops |
| TD-03 | Workflow `eval` in `platform_workflow/runtime_models.py` | Sandboxed (`__builtins__` empty) but still expression-eval | Sprint 39 |

## P1 — platform quality

| ID | Item | Notes | Target |
|----|------|-------|--------|
| TD-04 | ~350 LEGACY pytest failures | Milestone tests pin old `application_version` / sprint ids | Sprint 39–40 |
| TD-05 | `check_no_sqlite.py` reports `cursor.execute` hits | Legacy sync DB paths in several engines | Sprint 39 |
| TD-06 | mypy / pyright not adopted | Only ruff critical rules in CI today | Sprint 39 |
| TD-07 | Certification job soft-fail in CI | `continue-on-error` until score stable | Sprint 39 |
| TD-08 | Empty-file corruption class of bugs | Process: pre-commit size check / CI empty-file gate | Sprint 39 |

## P2 — cleanup / ergonomics

| ID | Item | Notes | Target |
|----|------|-------|--------|
| TD-09 | Builtin-named methods (`set`, `list`, `all`) | Safe with `from __future__ import annotations`; rename for clarity | Backlog |
| TD-10 | Large Vite chunks | Frontend code-split | Backlog |
| TD-11 | Telegram network flakes in bot logs | Polling to `api.telegram.org`; not healthcheck-fatal | Ops |
| TD-12 | `ga_staging_smoke.py` pinned to Sprint 30.6 | Superseded by `smoke_platform_rc.py` | Sprint 39 |
| TD-14 | Circular import when collecting `tests/test_architecture_boundaries.py` via `src.platform.layers` → `database.session` ↔ `platform_configuration` | Isolate policy imports from DB session bootstrap | Sprint 39 |

## Intentionally deferred (not debt)

- Enterprise City visual investment — sequenced after platform completion
- Breaking `/api/v1` changes — frozen contract
- Bulk rewrite of `platform_legacy` — migrate incrementally

## Sprint 39 suggested focus

1. Rotate production secrets; fail-closed if `CHANGE_ME` in `ENVIRONMENT=production`
2. Retire or rewrite LEGACY version-pin tests to read live config versions
3. Replace workflow `eval` with a safe expression AST walker
4. Adopt mypy (strict on `platform_security`, `api`, `services` first)
5. Empty-file CI gate + pre-commit
