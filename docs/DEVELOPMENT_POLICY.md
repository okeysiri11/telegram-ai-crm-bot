# ADOS Development Policy — Safe Development on RC Baseline

**Effective from:** Sprint 38.4  
**Baseline:** `v0.9.4-rc1` / branch `release/0.9.4`  
**Working branch:** `develop`  
**Execution modes (Sprint 39.0+):** see [`docs/DEVELOPMENT_EXECUTION_POLICY.md`](DEVELOPMENT_EXECUTION_POLICY.md)

This policy protects the Release Candidate platform. Feature sprints build **on top of**
the frozen baseline. They must not casually rewrite architecture, rename public APIs,
or destabilize startup/health contracts.

---

## 1. Absolute rules

1. **No mass architectural refactors** in a feature sprint.
2. **No API renames** of frozen contracts (`/api/v1`, `/management/v1`, system `/health` `/ready` `/liveness` `/readiness`).
3. **No mass file/module renames** unless the sprint is an explicit infrastructure rename sprint.
4. **No automated whole-repo rewrites** (codemods across the tree, bulk “cleanup” PRs).
5. **Minimal diffs only.** Fix the cause of the task — nothing else.
6. **Architecture refactors require their own sprint** (named, scoped, with its own RESULT.md).

Violations are grounds to reject the PR / mark the sprint incomplete.

---

## 2. Branch model

| Branch | Role |
|--------|------|
| `release/0.9.4` | Frozen RC line. Hotfixes only (cherry-pick + re-tag if needed). |
| `v0.9.4-rc1` (tag) | Immutable snapshot of the certified baseline. |
| `develop` | Default working branch for Sprint 39+. |
| `main` | Integration/stable mirror (merge from `develop` when ready). |

Do not force-push `release/0.9.4` or move `v0.9.4-rc1`.

---

## 3. Mandatory pre-merge pipeline

No change is complete until **all** of the following pass automatically:

1. Ruff (critical rules on touched packages / RC paths)
2. Pytest RC suite (`scripts/run_rc_test_suite.py`)
3. Smoke tests (`scripts/smoke_platform_rc.py` or CI docker-smoke job)
4. `docker compose up --build` succeeds
5. `GET /health` → HTTP 200 and healthy payload
6. `GET /ready` → HTTP 200 and ready=true
7. All compose services **Healthy** (postgres, redis, bot, nginx, prometheus, grafana)
8. No new `ImportError` / `ModuleNotFoundError` on critical modules
9. No new Alembic / migration failures (`alembic current` at head after entrypoint)
10. No new **critical** warnings that indicate broken startup

Local one-shot gate:

```bash
python scripts/pre_merge_gate.py
```

Any failure → sprint / PR is **not done**.

---

## 4. Architecture protection gates

CI and local pre-merge must run `scripts/validate_platform_protections.py`, which fails on:

- Builtin shadowing that can break annotations (`def list` + `list[...]` without future annotations)
- Empty (0-byte) Python modules under platform/services/repositories/database
- Empty workflow definition files under known workflow roots
- Missing `/health` or `/ready` route registration
- Missing Alembic migrations directory / head revision file
- Suspicious circular-import patterns in critical bootstrap modules (best-effort import probe)
- Duplicate registry / service registration names where detectable

Mass-rename detection: PRs that rename **≥ 25** paths in one change set require an explicit
`INFRASTRUCTURE_RENAME=1` override in CI (infrastructure sprint only).

---

## 5. What belongs in Sprint 39+

Allowed without a separate infra sprint:

- Additive APIs / fields (non-breaking)
- Bug fixes with minimal scope
- Tests and docs for the change
- Vertical/feature modules that extend existing services via DI/events

Requires a dedicated infrastructure sprint:

- Layer boundary changes
- Package moves/renames
- Auth/contract breaks (with version bump)
- Migration strategy overhauls
- Replacing core buses, DI, or startup sequence

---

## 6. Recovery expectation

A clean machine must be able to:

```text
git clone <repo>
git checkout v0.9.4-rc1   # or develop after freeze merge
cp .env.example .env      # fill BOT_TOKEN / secrets as needed
docker compose up --build
```

…and reach healthy containers with automatic migrations — **no manual schema steps**.

---

## 7. Documentation duty

Every sprint that touches platform code must update:

- Relevant `docs/*.md` for the subsystem
- `docs/SPRINT_<id>_RESULT.md`
- Architecture notes if boundaries change (infra sprint only)

---

## 8. Enforcement

| Mechanism | File |
|-----------|------|
| Human policy | `docs/DEVELOPMENT_POLICY.md` (this file) |
| Pre-merge script | `scripts/pre_merge_gate.py` |
| Protection checks | `scripts/validate_platform_protections.py` |
| CI | `.github/workflows/architecture.yml` |
| Baseline record | `docs/PLATFORM_BASELINE.md` |

**Frozen infrastructure is sacred.** Build features above it; do not dig under it without an infra sprint.
