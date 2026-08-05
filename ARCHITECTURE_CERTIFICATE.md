# Architecture Certificate

> Issued: 2026-08-05 10:32:37 UTC

## Result

**FAIL**

Architecture Score: **73.85/100**

Quality Gates: **FAILED**

## Evaluation

| Area | Score | Status | Notes |
|------|-------|--------|-------|
| Security | 100.0 | PASS | Plugin SDK isolation |
| Architecture | 100.0 | PASS | 0 dependency cycles |
| Boundaries | 0 | WARN/FAIL | 22 critical violations |
| Dependencies | 84 | WARN/FAIL | 2 cross-layer violations |
| API | 100.0 | PASS | OpenAPI contract validation |
| Workflow | 100.0 | PASS | Workflow schema validation |
| Plugin SDK | 100.0 | PASS | SDK export surface |
| Configuration | 85.0 | WARN/FAIL | ConfigurationCenter boundary |
| Legacy | 0.0 | WARN/FAIL | Legacy isolation via platform_legacy |
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

- Architecture score 73.85 < 90
- 22 critical boundary/import violations
- 0 dependency cycles and 2 strict layer violations detected
- Legacy CI validation failed

---

*This certificate is generated automatically by Architecture Governance CI.*

