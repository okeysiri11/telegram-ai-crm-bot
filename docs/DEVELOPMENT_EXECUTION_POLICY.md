# ADOS Development Execution Policy

**Sprint:** 39.0  
**Effective:** immediately on `develop` above baseline `v0.9.4-rc1`  
**Companion:** [`docs/DEVELOPMENT_POLICY.md`](DEVELOPMENT_POLICY.md) (safe-development / freeze rules)

Every sprint **must** declare an explicit **work mode** in its brief and in `docs/SPRINT_<id>_RESULT.md`.

Cursor may change **any number of files** required by the task.  
Cursor must **not** change architecture, Docker, Compose, CI, or GitHub Workflows unless the sprint mode (or an explicit sprint requirement) allows it.

---

## 1. Work modes

### FEATURE

New product capability.

| Allowed | Forbidden |
|---------|-----------|
| New modules, services, agents, UI | Architecture changes |
| Additive APIs / fields (non-breaking) | Compose / Docker / CI / GitHub Actions changes |
| Tests + docs for the feature | Project structure reshuffles |
| | Mass renames / file moves |

Infrastructure touches in a FEATURE sprint are allowed **only** if the sprint text explicitly requires them.

---

### BUGFIX

Fix one concrete defect.

| Allowed | Forbidden |
|---------|-----------|
| Minimal change that removes the root cause | Refactor “while we are here” |
| Targeted tests proving the fix | Mass renames / file moves |
| | Architecture changes |
| | Unrelated cleanup |

---

### INFRASTRUCTURE

Platform plumbing and ops surface.

| Allowed |
|---------|
| Docker, Compose, CI, GitHub Actions |
| Migrations, deployment, security hardening |
| Healthchecks, monitoring |
| Architecture changes (scoped and documented) |

Only INFRASTRUCTURE (or an explicitly infra-scoped sprint) may change those areas.

---

### RELEASE

Ship / certify — no feature work.

| Allowed | Forbidden |
|---------|-----------|
| Documentation, release notes, versions, tags | Functional / product code changes |
| Final validation, Smoke, RC, Release Candidate | Opportunistic refactors |

---

## 2. End-of-sprint gates (mandatory)

After every sprint, **automatically** run and require PASS:

1. Ruff (critical rules on touched / RC paths)  
2. Critical imports  
3. Architecture / platform protections (`scripts/validate_platform_protections.py`)  
4. Smoke tests (`scripts/smoke_platform_rc.py`)  
5. Docker build  
6. `docker compose up`  
7. Container healthchecks — all Healthy  
8. `GET /health` → 200 + healthy  
9. `GET /ready` → 200 + ready  
10. RC tests (`scripts/run_rc_test_suite.py`)

One-shot local command:

```bash
python scripts/pre_merge_gate.py --with-docker
```

**Any failure → sprint is incomplete (not COMPLETE).**

---

## 3. Nightly validation

Once per day, run the full overnight cycle and write:

**`docs/NIGHTLY_REPORT.md`**

Nightly suite includes:

- Full pytest (`-m "not slow"` where applicable, plus classification)
- Legacy test classification (CURRENT vs LEGACY)
- Load / integration / security suites when present
- CI validation scripts (`validate_architecture`, `validate_legacy_migration`, protections)
- Docker clean build + compose up
- Migration validation (`alembic current` / head)
- Regression + architecture + smoke + RC

Runner:

```bash
python scripts/nightly_validation.py
```

GitHub Actions schedule: `.github/workflows/nightly.yml` (daily).

### Nightly failure policy

- Record and **group** failures in `docs/NIGHTLY_REPORT.md`
- **Do not** auto-fix everything
- Promote grouped items into the **next sprint** backlog

---

## 4. Safe development (file count)

- No artificial limit on how many files may change
- Scope is defined by **mode + sprint brief**, not by file count
- FEATURE/BUGFIX must not silently become INFRASTRUCTURE
- Frozen contracts (`/api/v1`, `/management/v1`, `/health`, `/ready`, …) stay additive-only unless an INFRASTRUCTURE/RELEASE sprint says otherwise

---

## 5. COMPLETE checklist

Before marking a sprint **COMPLETE**, Cursor must confirm:

| Gate | Required |
|------|----------|
| PASS Ruff | ✓ |
| PASS Smoke | ✓ |
| PASS Docker Build | ✓ |
| PASS Compose | ✓ |
| PASS Health | ✓ |
| PASS Ready | ✓ |
| PASS RC | ✓ |

Only then:

```text
STATUS: SPRINT <id> COMPLETE
```

---

## 6. Mode declaration template

Put this at the top of every sprint brief / RESULT:

```text
MODE: FEATURE | BUGFIX | INFRASTRUCTURE | RELEASE
BASELINE: v0.9.4-rc1
```

---

## Enforcement map

| Mechanism | Path |
|-----------|------|
| Execution policy (this file) | `docs/DEVELOPMENT_EXECUTION_POLICY.md` |
| Freeze / safe-dev rules | `docs/DEVELOPMENT_POLICY.md` |
| Pre-merge gate | `scripts/pre_merge_gate.py` |
| Protections | `scripts/validate_platform_protections.py` |
| Nightly runner | `scripts/nightly_validation.py` |
| Nightly report | `docs/NIGHTLY_REPORT.md` |
| Nightly CI | `.github/workflows/nightly.yml` |
| Baseline | `docs/PLATFORM_BASELINE.md` |
