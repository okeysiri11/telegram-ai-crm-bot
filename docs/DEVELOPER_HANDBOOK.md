# Developer Handbook — Enterprise Automotive Suite

**Version:** `4.2.0-enterprise`

## Layout

`applications/auto_marketplace/<domain>/` — facade + domain modules; APIs under `/api/<domain>/v1`.

## Rules

- Do not modify Platform Core, AI OS, or Enterprise Edition
- Additive sprint packages only; wire via config, store, application, register
- Tests: `tests/test_*13_*.py` + certification suite

## Certification API

`POST /api/enterprise-certification/v1/bootstrap` runs the full gate pack.
