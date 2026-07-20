# Finance Engine — Documents, Contracts & Financial Operations

> Sprint 6.5 — enterprise document management, contracts, and financial workflows

## Overview

Sprint 6.5 delivers a complete **Finance Engine** for the Auto Marketplace: documents, contracts, payments, invoicing, refunds, settlements, and financial reporting — integrated with Platform Core v3.0 via bridges only.

---

## Architecture

```mermaid
flowchart TB
    subgraph FinanceEngine
        FE[FinanceEngine]
        DE[DocumentEngine]
        CS[ContractService]
        PO[PaymentOperations]
        IS[InvoiceService]
        AC[AccountingService]
        AI[FinanceAIAssistant]
    end

    FE --> DE & CS & PO & IS & AC & AI
    AI -.-> Platform Core
    FE --> CRMEngine
```

---

## Modules

| Module | Role |
|--------|------|
| `finance/` | Engine, models, events, security, AI, workflows |
| `documents/` | Templates, PDF generation, signatures, version history |
| `contracts/` | Purchase, sale, trade-in, dealer agreements |
| `payments/` | Payment tracking, authorization, capture |
| `billing/` | Commission calculation |
| `invoices/` | Invoice generation and approval |
| `receipts/` | Receipt generation |
| `taxes/` | Tax calculation |
| `accounting/` | Refunds, settlements, ledger |
| `reports/` | Financial summaries |

---

## Finance Guide

```python
from applications.auto_marketplace import auto_marketplace

# Document from template
templates = auto_marketplace.finance_engine.documents.list_templates()
doc = await auto_marketplace.finance_engine.documents.generate_from_template(
    templates[0].template_id,
    title="Purchase Agreement",
    variables={"vehicle": "Toyota Camry", "amount": "28000", "currency": "USD"},
    customer_id="c1",
)

# Payment flow
payment = await auto_marketplace.finance_engine.payments.create_payment(FinancePayment(...))
captured = await auto_marketplace.finance_engine.payments.capture(payment.payment_id)

# Invoice with tax
invoice = await auto_marketplace.finance_engine.invoices.generate(
    deal_id="d1", customer_id="c1", amount=28000, jurisdiction="US"
)

# Refund & settlement
refund = await auto_marketplace.finance_engine.accounting.request_refund(payment_id="p1", amount=500)
await auto_marketplace.finance_engine.accounting.process_refund(refund.refund_id)
```

---

## Contracts Guide

```python
from applications.auto_marketplace.finance.models import PurchaseAgreement

agreement = PurchaseAgreement(customer_id="c1", vehicle_id="v1", amount=32000)
contract = await auto_marketplace.finance_engine.contracts.create_purchase_agreement(agreement)
await auto_marketplace.finance_engine.contracts.sign(contract.contract_id, signed_by="customer-1")
analysis = await auto_marketplace.finance_engine.contracts.analyze(contract.contract_id)
```

Contract types: `purchase`, `sale`, `trade_in`, `dealer`, `customer`

Lifecycle: `draft` → `pending_signature` → `signed` → `active` → `terminated`

---

## AI Integration

| Capability | Description |
|------------|-------------|
| Document generation | Template variable fill + Reasoning Engine |
| Contract analysis | Risk detection and clause review |
| Payment anomaly detection | Unusual amount / deviation checks |
| Financial summaries | Invoice and payment aggregation |
| Document classification | Auto-categorize by content |

---

## Security — Finance Roles

| Role | Permissions |
|------|-------------|
| Owner | Full access |
| Administrator | Finance management |
| Finance Manager | Documents, contracts, payments, invoices, refunds |
| Sales Manager | Read/write contracts and documents |
| Dealer | Read-only finance |
| Customer | Self-service read |
| AI Agent | Generate, analyze, detect anomalies |

Audit logging via `finance_engine.security.audit()` and `list_audit()`.

Sensitive payment data uses field encryption (SHA-256) and masking.

---

## Events

`DocumentCreated`, `ContractSigned`, `InvoiceGenerated`, `PaymentCompleted`, `RefundProcessed`, `SettlementCompleted`

---

## API — `/api/auto/v1/finance`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Finance metrics |
| GET | `/documents/templates` | List templates |
| POST | `/documents/generate` | Generate document |
| GET | `/documents/{id}` | Get document |
| POST | `/documents/{id}/approve` | Approve document |
| GET | `/documents/{id}/export` | Export PDF |
| POST | `/contracts` | Create contract |
| GET | `/contracts/{id}` | Get contract |
| POST | `/contracts/{id}/sign` | Sign contract |
| GET | `/contracts/{id}/analyze` | AI risk analysis |
| POST | `/payments` | Create payment |
| POST | `/payments/{id}/capture` | Capture + invoice + receipt |
| POST | `/invoices` | Generate invoice |
| POST | `/refunds` | Request refund |
| POST | `/refunds/{id}/process` | Process refund |
| POST | `/settlements` | Create settlement |
| POST | `/settlements/{id}/complete` | Complete settlement |
| GET | `/reports/summary` | Financial report |
| GET | `/audit` | Audit log |

---

## Manifest

`application_version: "1.4.0-alpha"`

---

## Tests

```bash
pytest tests/test_finance_engine.py -q
```

---

## Developer Guide

Access via `auto_marketplace.finance_engine`. Legacy Sprint 6.1 `document_service` and `payment_service` remain unchanged.

```python
auto_marketplace.finance_engine.metrics()
auto_marketplace.finance_engine.security.authorize("finance_manager", "invoices.manage")
await auto_marketplace.finance_engine.workflow.contract_approval(contract_id, "legal-team")
```
