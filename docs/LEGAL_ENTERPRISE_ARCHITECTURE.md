# Legal Enterprise Architecture

**Version:** `5.0.0-enterprise`  
**Sprint:** 17.8  
**Suite:** Legal Enterprise Suite

## Modules

| Sprint | Package | Role |
|--------|---------|------|
| 17.0 | Foundation | Registry, legislation, courts, cases |
| 17.1 | `legislation_intelligence/` | Legislative intelligence |
| 17.2 | `judicial_intelligence/` | Judicial intelligence |
| 17.3 | `case_management/` | Case management platform |
| 17.4 | `document_intelligence/` | Document & contract intelligence |
| 17.5 | `compliance/` | Compliance & governance |
| 17.6 | `ai_legal_assistant/` | AI research & reasoning |
| 17.7 | `executive_intelligence/` | Executive decision support |
| 17.8 | `enterprise_certification/` | Certification & production release |

## Principles

- Additive modules only; prior Legal packages are frozen after each sprint.
- Shared `LegalEnterpriseStore` with prefixed buckets (`li_`, `ji_`, `cm_`, `di_`, `cp_`, `aa_`, `ei_`, `lec_`).
- Isolated API prefixes per module; auth via `X-Principal` middleware.
- Does not modify Platform Core, AI OS, Enterprise Edition, Automotive, Agro, Port, or Crypto.
