# Installation Guide — Crypto Enterprise Suite

**Version:** `4.8.0-enterprise`

1. Install Python dependencies for the repository.
2. Copy `config.template.env` and set vault/secret references.
3. Register routes via `register_crypto_enterprise_routes`.
4. Verify `/api/crypto-enterprise-certification/v1/health`.
5. Run bootstrap certification: `POST /api/crypto-enterprise-certification/v1/bootstrap`.
