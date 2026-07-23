# Installation Guide

1. Clone the repository and activate `.venv`.
2. Apply `applications/legal_enterprise/release/config.template.env`.
3. Start the API server with Legal Enterprise routes registered.
4. Verify `GET /api/legal-enterprise-certification/v1/health`.
5. Run `POST /api/legal-enterprise-certification/v1/bootstrap`.
6. Confirm readiness score ≥ 90 and status Production Ready.
