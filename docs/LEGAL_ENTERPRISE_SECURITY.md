# Legal Enterprise Security

**Version:** `5.0.0-enterprise`

## Controls

- **Authentication** — `X-Principal` middleware on Legal API routes
- **Authorization** — module prefix isolation and suite boundaries
- **Permissions** — role-aware legal roles in configuration
- **Encryption** — TLS at the edge; secrets via environment templates
- **Audit logging** — timestamped store events across modules
- **Data integrity** — `ValidationError` / `NotFoundError` enforcement

## Certification

Security certification is executed via:

`GET /api/legal-enterprise-certification/v1/security`
