# Compliance Guide — Sprint 31.3

| Control | API |
|---------|-----|
| KYC | `POST /api/legal-cp/v1/counterparties` `action:kyc` |
| AML score | `POST /api/legal-cp/v1/aml` `action:score` |
| Sanctions | `action:sanctions` |
| Risk flags | `action:high_risk` (`entity_name` required) |
| Compliance review | `POST /api/legal-cp/v1/dashboard` `compliance` |
| Document storage | Governance `action:document` KYC pack |
| Audit trail | `POST /api/enterprise-isam/v1/audit` |
| Approval workflow | `POST /api/finance-pay/v1/processing` `action:approve` |
