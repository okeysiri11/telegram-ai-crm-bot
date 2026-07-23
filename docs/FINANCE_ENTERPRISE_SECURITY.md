# Finance Enterprise Security

**Version:** `5.2.0-enterprise`

## Controls

- Financial permission validation (suite boundaries)
- Authentication via `X-Principal` middleware
- Authorization via API prefix isolation
- Encryption at edge (TLS); secrets via env templates
- Audit logging of store events
- Financial data integrity via ValidationError / NotFoundError paths

Certification gate: `GET /api/finance-enterprise-certification/v1/security`
