# Infrastructure Security

**Sprint:** 30.9 Beta Hardening

## Nginx (`nginx.conf`)

- Security headers: nosniff, frame deny, Referrer-Policy, Permissions-Policy, CSP
- `limit_req` on `/api/` and `/management/`
- Gzip compression
- Static `/assets/` cache (7d immutable)
- SPA `try_files` for Enterprise Web dist
- Forwards `X-Tenant-Id` / `X-Organization`
- TLS server block stub + HSTS note (enable when certs mounted)

## Docker Compose production

- `POSTGRES_PASSWORD` **required** (no `postgres` default)
- `GRAFANA_ADMIN_PASSWORD` **required** (no `admin` default)
- Grafana sign-up disabled
- Bot `/health` healthcheck; nginx waits on healthy bot
- Web dist mount: `./src/web/dist` → `/usr/share/nginx/html`

## Still operator-owned

- Provision TLS certs and uncomment 443 server
- Rotate IAM JWT / master keys via ConfigurationCenter
- Network policies / firewall outside compose
