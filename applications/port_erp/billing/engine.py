# Billing Engine — compose charges from commercial tariffs into invoices.

from __future__ import annotations

from applications.port_erp.finance.models import CommercialInvoice, FeeType
from applications.port_erp.invoices.engine import InvoiceEngine, invoice_engine
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.tariffs.commercial import CommercialTariffEngine, commercial_tariff_engine


class BillingEngine:
    """Commercial billing over port/terminal/storage/container/berth fees."""

    def __init__(
        self,
        invoices: InvoiceEngine | None = None,
        tariffs: CommercialTariffEngine | None = None,
    ) -> None:
        self._invoices = invoices or invoice_engine
        self._tariffs = tariffs or commercial_tariff_engine

    def fee_types(self) -> list[str]:
        return self._tariffs.fee_types()

    def create_bill(
        self,
        *,
        customer_id: str,
        charges: list[dict],
        currency: str = "USD",
        contract_id: str = "",
        company_id: str = "",
        country: str = "",
        description: str = "",
    ) -> CommercialInvoice:
        if not customer_id:
            raise ValidationError("customer_id is required")
        if not charges:
            raise ValidationError("charges are required")
        invoice = self._invoices.create(
            CommercialInvoice(
                customer_id=customer_id,
                contract_id=contract_id,
                company_id=company_id,
                currency=currency,
                description=description or "Port services bill",
            )
        )
        for charge in charges:
            self._invoices.add_charge(
                invoice.invoice_id,
                fee_type=charge.get("fee_type", FeeType.PORT.value),
                quantity=float(charge.get("quantity", 1) or 1),
                description=charge.get("description", ""),
                terminal_id=charge.get("terminal_id", ""),
                country=country,
            )
        return self._invoices.get(invoice.invoice_id)

    async def bill_and_issue(self, **kwargs) -> CommercialInvoice:
        invoice = self.create_bill(**kwargs)
        return await self._invoices.issue(invoice.invoice_id)


billing_engine = BillingEngine()
