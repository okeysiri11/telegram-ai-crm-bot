# Port ERP Finance & Commercial Management — Sprint 9.7

Port finance, billing, contracts, and accounting for **Port ERP 1.6.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.6.0-alpha` |
| Finance engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Everything lives under `applications/port_erp/`.

## Engines

| Engine | Module |
|--------|--------|
| Finance Engine | `finance/engine.py` |
| Billing Engine | `billing/engine.py` |
| Contract Engine | `contracts/engine.py` |
| Commercial Tariff Engine | `tariffs/commercial.py` |
| Invoice Engine | `invoices/engine.py` |
| Payment Engine | `payments/engine.py` |
| Accounting Engine | `accounting/engine.py` |
| Customer Account Engine | `customers/accounts.py` |
| Revenue / Cost / Profitability | `profitability/engine.py` |

Also: `currencies/` · `taxes/` · `budget/` · `suppliers/`

> Note: Customs HS `TariffEngine` remains in `tariffs/engine.py`. Commercial port tariffs use `CommercialTariffEngine`.

## Billing fee types

Port · Terminal · Storage · Container · Berth · Handling · Demurrage · Detention · Inspection · Custom services

## Contracts party types

Shipping Lines · Freight Forwarders · Customers · Importers · Exporters · Carriers · Government · Insurance · Banks

## REST API

| Area | Prefix |
|------|--------|
| Finance | `/api/port/v1/finance` |
| Billing | `/api/port/v1/billing` |
| Contracts | `/api/port/v1/contracts` |
| Tariffs | `/api/port/v1/tariffs` |
| Invoices | `/api/port/v1/invoices` |
| Payments | `/api/port/v1/payments` |
| Accounting | `/api/port/v1/accounting` |

## Developer guide

```python
from applications.port_erp import port_erp
from applications.port_erp.finance.models import CommercialTariff, FeeType

port_erp.finance.tariffs.register(
    CommercialTariff(name="Berth day", fee_type=FeeType.BERTH, rate=1200)
)
bill = port_erp.finance.billing.create_bill(
    customer_id="c1",
    charges=[{"fee_type": "berth_fees", "quantity": 2}],
)
issued = await port_erp.finance.invoices.issue(bill.invoice_id)
```

## Related

- [PORT_ERP.md](PORT_ERP.md)
- [PORT_CUSTOMS.md](PORT_CUSTOMS.md) — customs HS tariffs (separate)
