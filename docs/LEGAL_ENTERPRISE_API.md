# Legal Enterprise API

**Version:** `5.0.0-enterprise`

## Prefixes

| Prefix | Module |
|--------|--------|
| `/api/legal-enterprise/v1` | Foundation |
| `/api/legal-li/v1` | Legislation Intelligence |
| `/api/legal-ji/v1` | Judicial Intelligence |
| `/api/legal-cm/v1` | Case Management |
| `/api/legal-di/v1` | Document Intelligence |
| `/api/legal-cp/v1` | Compliance |
| `/api/legal-aa/v1` | AI Legal Assistant |
| `/api/legal-ei/v1` | Executive Intelligence |
| `/api/legal-enterprise-certification/v1` | Enterprise Certification |

## Certification endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Production readiness flags |
| POST | `/bootstrap` | Run full certification |
| GET | `/architecture` | Architecture gates |
| GET | `/integration` | Integration gates |
| GET | `/performance` | Performance benchmarks |
| GET | `/security` | Security audit |
| GET | `/documentation` | Documentation gates |
| GET | `/quality` | QA gates |
| GET | `/release` | Release package |
| GET | `/executive` | Executive scorecard |
| GET/POST | `/dashboard` | Certification dashboards |

Auth: `X-Principal` header via Legal Enterprise middleware.
