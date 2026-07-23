# Developer Guide

## Package

`applications/finance_enterprise/` — Bidex Finance Enterprise Suite

Certification: `applications/finance_enterprise/enterprise_certification/` — Sprint 18.8

## APIs

See `docs/FINANCE_ENTERPRISE_API.md` for module prefixes.

## Tests

```bash
.venv/bin/pytest tests/test_finance_enterprise_18_0.py tests/test_payments_18_1.py \
  tests/test_billing_18_2.py tests/test_treasury_18_3.py tests/test_digital_assets_18_4.py \
  tests/test_reporting_18_5.py tests/test_ai_cfo_18_6.py tests/test_integration_18_7.py \
  tests/test_finance_enterprise_certification_18_8.py -q
```
