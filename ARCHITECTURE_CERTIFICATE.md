# Architecture Certificate

> Issued: 2026-08-10 08:03:19 UTC

## Result

**FAIL**

Architecture Score: **80.25/100**

Quality Gates: **FAILED**

## Evaluation

| Area | Score | Status | Notes |
|------|-------|--------|-------|
| Security | 100.0 | PASS | Plugin SDK isolation |
| Architecture | 100.0 | PASS | 0 dependency cycles |
| Boundaries | 0 | WARN/FAIL | 29 critical violations |
| Dependencies | 68 | WARN/FAIL | 4 cross-layer violations |
| API | 100.0 | PASS | OpenAPI contract validation |
| Workflow | 100.0 | PASS | Workflow schema validation |
| Plugin SDK | 100.0 | PASS | SDK export surface |
| Configuration | 85.0 | WARN/FAIL | ConfigurationCenter boundary |
| Legacy | 100.0 | PASS | Legacy isolation via platform_legacy |
| Observability | 95.0 | PASS | Metrics and tracing present |
| Testing | 90.0 | PASS | Architecture governance test suite |

## Minimum Thresholds

- Architecture Score ≥ 90
- No boundary violations (critical)
- No dependency cycles
- No forbidden imports
- 100% API validation
- 100% SDK validation
- 100% workflow validation

## Failed Gates

- Architecture score 80.25 < 90
- 29 critical boundary/import violations
- 0 dependency cycles and 4 strict layer violations detected

---

*This certificate is generated automatically by Architecture Governance CI.*

