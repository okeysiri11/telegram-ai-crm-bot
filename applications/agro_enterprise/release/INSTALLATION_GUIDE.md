# Installation Guide — Agro Enterprise Suite v4.4.0-enterprise

1. Deploy Agro Enterprise application package under `applications/agro_enterprise/`.
2. Copy `config.template.env` and set environment values.
3. Register routes via `register_agro_enterprise_routes` in the API server.
4. Start the service and verify `/api/agro-enterprise/v1/health`.
5. Run certification bootstrap to confirm Production Ready status.
6. Enable module APIs as needed (precision, irrigation, crop AI, CEA, supply chain, finance, AI agronomist).
