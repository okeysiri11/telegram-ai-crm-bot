# Sprint 38.4 — Platform Baseline Freeze & Safe Development Policy

**Date:** 2026-08-05  
**Baseline tag:** `v0.9.4-rc1`  
**Release branch:** `release/0.9.4`  
**Working branch:** `develop`  
**Status:** **FROZEN / READY FOR SPRINT 39**

## Delivered

1. **Baseline freeze** — git tag `v0.9.4-rc1`, branch `release/0.9.4`, working branch `develop`
2. **`docs/DEVELOPMENT_POLICY.md`** — mandatory safe-development rules
3. **`docs/PLATFORM_BASELINE.md`** — versions, images, health/ready, migration checksums, gate results
4. **Architecture protection** — `scripts/validate_platform_protections.py`
5. **Pre-merge pipeline** — `scripts/pre_merge_gate.py` (+ CI wiring)
6. **Recovery/smoke validation** — pre-merge gate with docker: **ALL PASSED**

## Success criteria

| Criterion | Status |
|-----------|--------|
| git tag `v0.9.4-rc1` | ✓ |
| branch `release/0.9.4` | ✓ |
| `PLATFORM_BASELINE.md` | ✓ |
| `DEVELOPMENT_POLICY.md` | ✓ |
| pipeline green (pre-merge + protections) | ✓ |
| smoke PASS (32/32) | ✓ |
| docker one-command stack | ✓ |
| all containers Healthy | ✓ |
| `/health` 200 | ✓ |
| `/ready` 200 | ✓ |
| infrastructure frozen | ✓ |

## Files added/updated

- `docs/DEVELOPMENT_POLICY.md`
- `docs/PLATFORM_BASELINE.md`
- `docs/baseline_migration_checksums_38_4.json`
- `docs/SPRINT_38_4_RESULT.md`
- `scripts/validate_platform_protections.py`
- `scripts/pre_merge_gate.py`
- `.github/workflows/architecture.yml` (protection + pre-merge steps)

## Gate evidence

- `validate_platform_protections.py` → `PROTECTION_GATE=PASS`
- `pre_merge_gate.py --with-docker` → `ALL REQUIRED GATES PASSED`
- `run_rc_test_suite.py` → 64 passed
- Alembic head `u4o567890123` (sha256 recorded in baseline)

## Policy summary

Feature sprints on `develop` must use **minimal diffs**. Mass renames, API renames,
and architecture rewrites are forbidden unless scheduled as a separate infrastructure sprint.
Merge requires the pre-merge gate to be green.

## Verdict

**Infrastructure FROZEN at v0.9.4-rc1.** Sprint 39+ proceeds on `develop` above this baseline.
