# Installation Guide

1. Deploy `applications/finance_enterprise/` (additive modules 18.0–18.8).
2. Copy `release/config.template.env` and set environment values.
3. Ensure API server registers `register_finance_enterprise_routes`.
4. Verify `GET /api/finance-enterprise-certification/v1/health`.
5. Run `POST /api/finance-enterprise-certification/v1/bootstrap`.
6. Confirm readiness score ≥ 90 and status Production Ready.
