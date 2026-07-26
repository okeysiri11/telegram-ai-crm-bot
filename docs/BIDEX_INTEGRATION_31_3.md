# Bidex Integration Guide — Sprint 31.3

## Principle

Do **not** invent a parallel Bidex OS. Compose Finance Enterprise (custody/OTC/treasury/settlement), Legal Compliance (KYC/AML), Crypto Enterprise (intel/risk), and ISAM (identity/audit).

## API prefixes (existing)

| Prefix | Role |
|--------|------|
| `/api/finance-da/v1` | Crypto wallets, OTC operations, DA dashboards/AI |
| `/api/finance-pay/v1` | Fiat wallets, payments, approvals |
| `/api/finance-tr/v1` | Treasury |
| `/api/finance-int/v1` | Cross-platform crypto settlement/accounting |
| `/api/finance-cfo/v1` | AI CFO health |
| `/api/legal-cp/v1` | Counterparties, KYC/AML, compliance docs |
| `/api/crypto-enterprise/v1` | Crypto foundation health/dashboard |
| `/api/crypto-rm/v1` | Risk management health |
| `/api/enterprise-isam/v1` | Identity + audit log |

## Pitfalls

- Three wallet stores (pay / da / crypto-oc) — pilot uses **finance-da** for custody and **finance-pay** for fiat.
- OTC is recorded via DA `operation=otc_settlement` (not a separate deal FSM).
- Approvals live on finance-pay `/processing`.
- INT platforms require `"platform":"crypto"`.
