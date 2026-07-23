# Legal Enterprise Deployment

**Version:** `5.0.0-enterprise`

## Steps

1. Install Python dependencies from the project virtualenv.
2. Copy `applications/legal_enterprise/release/config.template.env` into the environment.
3. Register Legal Enterprise routes with the API server (already wired after Crypto).
4. Verify health: `GET /api/legal-enterprise-certification/v1/health`.
5. Run certification bootstrap: `POST /api/legal-enterprise-certification/v1/bootstrap`.
6. Confirm all module health endpoints return `5.0.0-enterprise`.

## Checklists

- Deployment: `applications/legal_enterprise/release/DEPLOYMENT_CHECKLIST.md`
- Production: `applications/legal_enterprise/release/PRODUCTION_CHECKLIST.md`
- Operations: `applications/legal_enterprise/release/OPERATIONS_CHECKLIST.md`
