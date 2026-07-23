# Financial API

**Version:** `5.1.0-enterprise`  
**Prefix:** `/api/finance-enterprise/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Readiness |
| POST | `/bootstrap` | Seed foundation |
| GET/POST | `/registry` | Financial registry |
| GET/POST | `/ledger` | General ledger |
| GET/POST | `/currency` | Multi-currency |
| GET/POST | `/architecture` | Events, audit, permissions |
| GET/POST | `/dashboard` | Executive dashboards |
| GET/POST | `/knowledge` | Knowledge graph |

Auth: `X-Principal` header.
