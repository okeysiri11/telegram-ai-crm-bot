# Port ERP finance / commercial REST handlers — Sprint 9.7.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.finance.models import (
    Budget,
    CommercialContract,
    CommercialInvoice,
    CommercialTariff,
    ContractPartyType,
    CreditNote,
    CustomerAccount,
    DebitNote,
    ExchangeRate,
    ExpenseRecord,
    FeeType,
    PricingMode,
    Supplier,
    TaxRate,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Customer


async def finance_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "finance_engine": port_erp.config.finance_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.finance.metrics(),
            "cash_flow": port_erp.finance.finance.cash_flow(),
            "profitability": port_erp.finance.profitability.summary(),
        }
    )


async def finance_expense_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        expense = port_erp.finance.finance.record_expense(
            ExpenseRecord(
                cost_center=data.get("cost_center", ""),
                company_id=data.get("company_id", ""),
                category=data.get("category", ""),
                amount=float(data.get("amount", 0) or 0),
                currency=data.get("currency", "USD"),
                description=data.get("description", ""),
            )
        )
        return json_response(expense.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_companies_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.finance.finance.companies_snapshot()})


async def finance_budget_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        budget = port_erp.finance.budgets.create_budget(
            Budget(
                name=data.get("name", ""),
                cost_center=data.get("cost_center", ""),
                company_id=data.get("company_id", ""),
                period=data.get("period", ""),
                amount=float(data.get("amount", 0) or 0),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(budget.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def billing_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        invoice = port_erp.finance.billing.create_bill(
            customer_id=data.get("customer_id", ""),
            charges=list(data.get("charges") or []),
            currency=data.get("currency", "USD"),
            contract_id=data.get("contract_id", ""),
            company_id=data.get("company_id", ""),
            country=data.get("country", ""),
            description=data.get("description", ""),
        )
        return json_response(invoice.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def billing_fee_types_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.finance.billing.fee_types()})


async def contracts_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        contract = port_erp.finance.contracts.create(
            CommercialContract(
                title=data.get("title", ""),
                party_type=ContractPartyType(data.get("party_type", "customer")),
                party_id=data.get("party_id", ""),
                party_name=data.get("party_name", ""),
                currency=data.get("currency", "USD"),
                value=float(data.get("value", 0) or 0),
                terms=data.get("terms", ""),
                company_id=data.get("company_id", ""),
            )
        )
        return json_response(contract.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def contracts_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "items": [c.to_dict() for c in port_erp.finance.contracts.list_contracts()],
            "party_types": port_erp.finance.contracts.party_types(),
        }
    )


async def contracts_activate_handler(request: web.Request) -> web.Response:
    try:
        contract = await port_erp.finance.contracts.activate(request.match_info["contract_id"])
        return json_response(contract.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def tariffs_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        tariff = port_erp.finance.tariffs.register(
            CommercialTariff(
                name=data.get("name", ""),
                fee_type=FeeType(data.get("fee_type", "port_fees")),
                unit=data.get("unit", "unit"),
                rate=float(data.get("rate", 0) or 0),
                currency=data.get("currency", "USD"),
                pricing_mode=PricingMode(data.get("pricing_mode", "standard")),
                min_qty=float(data.get("min_qty", 0) or 0),
                discount_pct=float(data.get("discount_pct", 0) or 0),
                terminal_id=data.get("terminal_id", ""),
                company_id=data.get("company_id", ""),
            )
        )
        return json_response(tariff.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def tariffs_list_handler(request: web.Request) -> web.Response:
    fee_type = request.query.get("fee_type")
    items = port_erp.finance.tariffs.list_tariffs(
        fee_type=FeeType(fee_type) if fee_type else None,
        terminal_id=request.query.get("terminal_id") or None,
    )
    return json_response(
        {
            "items": [t.to_dict() for t in items],
            "fee_types": port_erp.finance.tariffs.fee_types(),
            "pricing_modes": port_erp.finance.tariffs.pricing_modes(),
        }
    )


async def tariffs_quote_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        quote = port_erp.finance.tariffs.quote(
            fee_type=data.get("fee_type", "port_fees"),
            quantity=float(data.get("quantity", 1) or 1),
            terminal_id=data.get("terminal_id", ""),
            volume=float(data.get("volume", 0) or 0),
            priority=bool(data.get("priority", False)),
            emergency=bool(data.get("emergency", False)),
        )
        return json_response(quote)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def invoices_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        invoice = port_erp.finance.invoices.create(
            CommercialInvoice(
                customer_id=data.get("customer_id", ""),
                contract_id=data.get("contract_id", ""),
                company_id=data.get("company_id", ""),
                currency=data.get("currency", "USD"),
                description=data.get("description", ""),
            )
        )
        return json_response(invoice.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def invoices_list_handler(request: web.Request) -> web.Response:
    items = port_erp.finance.invoices.list_invoices(
        customer_id=request.query.get("customer_id") or None
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def invoices_charge_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        invoice = port_erp.finance.invoices.add_charge(
            request.match_info["invoice_id"],
            fee_type=data.get("fee_type", "port_fees"),
            quantity=float(data.get("quantity", 1) or 1),
            description=data.get("description", ""),
            terminal_id=data.get("terminal_id", ""),
            country=data.get("country", ""),
        )
        return json_response(invoice.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def invoices_issue_handler(request: web.Request) -> web.Response:
    try:
        invoice = await port_erp.finance.invoices.issue(request.match_info["invoice_id"])
        return json_response(invoice.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def invoices_credit_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        note = port_erp.finance.invoices.credit_note(
            CreditNote(
                invoice_id=request.match_info["invoice_id"],
                amount=float(data.get("amount", 0) or 0),
                currency=data.get("currency", "USD"),
                reason=data.get("reason", ""),
            )
        )
        return json_response(note.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def invoices_debit_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        note = port_erp.finance.invoices.debit_note(
            DebitNote(
                invoice_id=request.match_info["invoice_id"],
                amount=float(data.get("amount", 0) or 0),
                currency=data.get("currency", "USD"),
                reason=data.get("reason", ""),
            )
        )
        return json_response(note.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def invoices_outstanding_handler(request: web.Request) -> web.Response:
    items = port_erp.finance.invoices.outstanding(
        customer_id=request.query.get("customer_id") or None
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def payments_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        payment = await port_erp.finance.payments.pay(
            invoice_id=data.get("invoice_id", ""),
            amount=float(data.get("amount", 0) or 0),
            method=data.get("method", "transfer"),
            installment_no=int(data.get("installment_no", 0) or 0),
            reference=data.get("reference", ""),
        )
        return json_response(payment.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def payments_list_handler(request: web.Request) -> web.Response:
    items = port_erp.finance.payments.list_payments(
        invoice_id=request.query.get("invoice_id") or None
    )
    return json_response({"items": [p.to_dict() for p in items]})


async def payments_refund_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        amount = data.get("amount") if data else None
        payment = port_erp.finance.payments.refund(
            request.match_info["payment_id"],
            amount=float(amount) if amount is not None else None,
        )
        return json_response(payment.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def accounting_post_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        entries = port_erp.finance.accounting.post(
            debit_account=data.get("debit_account", ""),
            credit_account=data.get("credit_account", ""),
            amount=float(data.get("amount", 0) or 0),
            currency=data.get("currency", "USD"),
            reference=data.get("reference", ""),
            description=data.get("description", ""),
            company_id=data.get("company_id", ""),
        )
        return json_response({"items": [e.to_dict() for e in entries]}, status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def accounting_journal_handler(request: web.Request) -> web.Response:
    items = port_erp.finance.accounting.journal(
        company_id=request.query.get("company_id") or None
    )
    return json_response(
        {
            "items": [e.to_dict() for e in items],
            "receivables": port_erp.finance.accounting.receivables(),
            "payables": port_erp.finance.accounting.payables(),
        }
    )


async def accounting_fx_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        if data.get("rate"):
            rate = port_erp.finance.currencies.set_rate(
                ExchangeRate(
                    base_currency=data.get("base_currency", "USD"),
                    quote_currency=data.get("quote_currency", "EUR"),
                    rate=float(data.get("rate", 1) or 1),
                )
            )
            return json_response(rate.to_dict(), status=201)
        converted = port_erp.finance.accounting.convert(
            float(data.get("amount", 0) or 0),
            from_currency=data.get("from_currency", "USD"),
            to_currency=data.get("to_currency", "EUR"),
        )
        return json_response({"amount": converted})
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def accounting_tax_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        if data.get("register"):
            tax = port_erp.finance.taxes.register(
                TaxRate(
                    name=data.get("name", "VAT"),
                    rate_pct=float(data.get("rate_pct", 0) or 0),
                    country=data.get("country", ""),
                )
            )
            return json_response(tax.to_dict(), status=201)
        result = port_erp.finance.taxes.calculate(
            float(data.get("amount", 0) or 0),
            country=data.get("country", ""),
            tax_name=data.get("tax_name", "VAT"),
        )
        return json_response(result)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_customer_account_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        if data.get("customer_name"):
            customer = port_erp.core.customers.register(
                Customer(name=data.get("customer_name", ""), country=data.get("country", ""))
            )
            customer_id = customer.customer_id
        else:
            customer_id = data.get("customer_id", "")
        account = port_erp.finance.accounts.open_account(
            CustomerAccount(
                customer_id=customer_id,
                currency=data.get("currency", "USD"),
                credit_limit=float(data.get("credit_limit", 0) or 0),
            )
        )
        return json_response(account.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def finance_supplier_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        supplier = port_erp.finance.suppliers.register(
            Supplier(
                name=data.get("name", ""),
                country=data.get("country", ""),
                contact_email=data.get("contact_email", ""),
            )
        )
        return json_response(supplier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
