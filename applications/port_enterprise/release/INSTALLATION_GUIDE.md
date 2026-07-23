# Installation Guide — Port Enterprise Suite v4.6.0-enterprise

1. Install Python dependencies for the repository virtualenv.
2. Copy `applications/port_enterprise/release/config.template.env` into the deployment environment.
3. Register Port Enterprise routes via `register_port_enterprise_routes`.
4. Start the API process and confirm `/api/port-enterprise/v1/health`.
5. Run `/api/port-enterprise-certification/v1/bootstrap` and confirm all gates PASS.
6. Smoke-test prior module health endpoints (navigation through AI director).
